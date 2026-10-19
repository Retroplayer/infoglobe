#include <stdio.h>
#include <string.h>
#include "pico/stdlib.h"
#include "hardware/pio.h"
#include "hardware/dma.h"
#include "hardware/irq.h"
#include "hardware/clocks.h"
#include "hardware/sync.h"
#include "tusb.h"
#include "capture.pio.h"
#define WORDS 1024u
#define SAMPLES (WORDS*32u)
#define BUFFERS 8
#define RATE 1000000u
// Types: metadata=1, samples=2, marker=3, status=4, end=5, loss=6.
typedef struct __attribute__((packed)) {
    char magic[4]; uint8_t version,type; uint16_t flags;
    uint32_t sequence; uint64_t sample; uint32_t length;
} header;
_Static_assert(sizeof(header)==24,"wire header size");
static uint32_t buffers[BUFFERS][WORDS];
static volatile uint8_t used[BUFFERS];
static volatile uint8_t queue[BUFFERS],qread,qwrite;
static uint channel[2],channel_buffer[2];
static volatile uint64_t buffer_sample[BUFFERS],completed_sample;
static uint buffer_words[BUFFERS];
static uint64_t next_sample;
static volatile bool running,loss;
static volatile bool ending;
static PIO pio=pio0; static uint sm,offset;
static uint32_t sequence;
static volatile uint32_t blocks;
static const char * volatile end_reason="stopped";
static uint8_t frame[sizeof(header)+WORDS*4+4];
static size_t frame_size,frame_sent;
static int frame_buffer=-1;
static char notice[320],marker[200];
static bool status_pending,marker_pending;
static uint64_t marker_sample,marker_us;
static uint64_t session;
static uint32_t crc32(const uint8_t *p,size_t n) {
    uint32_t c=0xffffffff;
    while(n--) { c^=*p++; for(int b=0;b<8;b++)c=(c>>1)^(0xedb88320u&-(c&1)); }
    return c^0xffffffff;
}
static void frame_begin(uint8_t type,uint64_t sample,const void *payload,size_t n) {
    header h={{'I','G','C','P'},1,type,0,sequence++,sample,(uint32_t)n};
    memcpy(frame,&h,sizeof(h));memcpy(frame+sizeof(h),payload,n);
    uint32_t crc=crc32(frame,sizeof(h)+n);
    memcpy(frame+sizeof(h)+n,&crc,4);
    frame_size=sizeof(h)+n+4;frame_sent=0;
}
static void json_frame(uint8_t type,uint64_t sample,const char *text) {
    frame_begin(type,sample,text,strlen(text));
}
static void halt(void) {
    running=false;pio_sm_set_enabled(pio,sm,false);
    dma_channel_abort(channel[0]);dma_channel_abort(channel[1]);
    dma_hw->ints0=(1u<<channel[0])|(1u<<channel[1]);
}
static void dma_irq(void) {
    uint32_t mask=dma_hw->ints0;
    dma_hw->ints0=mask&((1u<<channel[0])|(1u<<channel[1]));
    if(!running)return;
    // At most one normally completes per 32.768 ms; service in acquisition order.
    for(int pass=0;pass<2;pass++) {
        int i=buffer_sample[channel_buffer[0]]<buffer_sample[channel_buffer[1]]?0:1;
        if(!(mask&(1u<<channel[i])))i^=1;
        if(!(mask&(1u<<channel[i])))break;
        mask&=~(1u<<channel[i]);
        uint b=channel_buffer[i];
        if(buffer_sample[b]!=completed_sample) { loss=true;halt();ending=true;end_reason="dma_order_loss";return; }
        completed_sample+=SAMPLES;blocks++;buffer_words[b]=WORDS;
        queue[qwrite%BUFFERS]=(uint8_t)b;qwrite++;
        int free_buffer=-1;
        for(int k=0;k<BUFFERS;k++)if(!used[k]) {free_buffer=k;break;}
        if(free_buffer<0) {loss=true;halt();ending=true;end_reason="buffer_overflow";return;}
        used[free_buffer]=1;channel_buffer[i]=(uint)free_buffer;
        buffer_sample[free_buffer]=next_sample;next_sample+=SAMPLES;
        dma_channel_set_write_addr(channel[i],buffers[free_buffer],false);
        dma_channel_set_trans_count(channel[i],WORDS,false);
    }
}
static void stop_clean(void) {
    // Preserve DMA-transferred whole words in the final partial block as well.
    // At most the RX FIFO and an incomplete shift word remain unrecorded.
    uint32_t saved=save_and_disable_interrupts();
    halt();
    for(int pass=0;pass<2;pass++) {
        int i=buffer_sample[channel_buffer[0]]<buffer_sample[channel_buffer[1]]?0:1;
        if(buffer_sample[channel_buffer[i]]!=completed_sample)i^=1;
        uint b=channel_buffer[i];
        if(buffer_sample[b]!=completed_sample)break;
        uint n=WORDS-dma_channel_hw_addr(channel[i])->transfer_count;
        if(!n)break;
        buffer_words[b]=n;
        queue[qwrite%BUFFERS]=(uint8_t)b;qwrite++;
        completed_sample+=(uint64_t)n*32;blocks++;
    }
    ending=true;end_reason="stopped";
    restore_interrupts(saved);
}
static uint64_t sample_now(void) {
    uint32_t saved=save_and_disable_interrupts();
    uint64_t n=completed_sample;
    if(running)for(int i=0;i<2;i++)if(dma_channel_is_busy(channel[i]))
        n=buffer_sample[channel_buffer[i]]+(WORDS-dma_channel_hw_addr(channel[i])->transfer_count)*32;
    restore_interrupts(saved);return n;
}
static void begin(void) {
    halt();memset((void*)used,0,sizeof(used));qread=qwrite=0;
    loss=false;ending=false;blocks=0;completed_sample=0;next_sample=2*SAMPLES;
    session=time_us_64();
    pio_sm_clear_fifos(pio,sm);pio_sm_restart(pio,sm);
    pio_sm_exec(pio,sm,pio_encode_jmp(offset));pio_sm_clkdiv_restart(pio,sm);
    pio->fdebug=1u<<(PIO_FDEBUG_RXSTALL_LSB+sm);
    for(int i=0;i<2;i++) {
        channel_buffer[i]=(uint)i;used[i]=1;buffer_sample[i]=(uint64_t)i*SAMPLES;
        dma_channel_config c=dma_channel_get_default_config(channel[i]);
        channel_config_set_transfer_data_size(&c,DMA_SIZE_32);
        channel_config_set_read_increment(&c,false);channel_config_set_write_increment(&c,true);
        channel_config_set_dreq(&c,pio_get_dreq(pio,sm,false));
        channel_config_set_chain_to(&c,channel[i^1]);
        dma_channel_configure(channel[i],&c,buffers[i],&pio->rxf[sm],WORDS,false);
    }
    snprintf(notice,sizeof(notice),"{\"firmware\":\"infoglobe-capture-1\",\"session\":%llu,\"sample_rate\":%u,\"gpio\":%u,\"active_low\":true,\"format\":\"u32le-msb-first\",\"block_samples\":%u,\"marker_uncertainty_samples\":288}",
        (unsigned long long)session,RATE,INFOGLOBE_RX_PIN,SAMPLES);
    json_frame(1,0,notice);running=true;
    dma_start_channel_mask(1u<<channel[0]);pio_sm_set_enabled(pio,sm,true);
}
static void command(char *line) {
    if(!strcmp(line,"start")) {
        if(running || ending || qread!=qwrite) {status_pending=true;return;}
        begin();
    } else if(!strcmp(line,"stop")) {
        if(running)stop_clean();
        else status_pending=true;
    } else if(!strcmp(line,"status"))status_pending=true;
    else if(!strncmp(line,"mark ",5)) {
        if(!running || marker_pending){status_pending=true;return;}
        // Marker content is UTF-8 text, not JSON, so no escaping is required.
        strncpy(marker,line+5,sizeof(marker)-1);marker[sizeof(marker)-1]=0;
        marker_sample=sample_now();marker_us=time_us_64();marker_pending=true;
    } else status_pending=true;
}
int main(void) {
    offset=pio_add_program(pio,&capture_program);sm=pio_claim_unused_sm(pio,true);
    pio_gpio_init(pio,INFOGLOBE_RX_PIN);gpio_pull_up(INFOGLOBE_RX_PIN);
    pio_sm_set_consecutive_pindirs(pio,sm,INFOGLOBE_RX_PIN,1,false);
    pio_sm_config c=capture_program_get_default_config(offset);
    sm_config_set_in_pins(&c,INFOGLOBE_RX_PIN);sm_config_set_in_shift(&c,false,true,32);
    sm_config_set_fifo_join(&c,PIO_FIFO_JOIN_RX);
    sm_config_set_clkdiv(&c,(float)clock_get_hz(clk_sys)/RATE);
    pio_sm_init(pio,sm,offset,&c);
    for(int i=0;i<2;i++){channel[i]=dma_claim_unused_channel(true);dma_channel_set_irq0_enabled(channel[i],true);}
    irq_set_exclusive_handler(DMA_IRQ_0,dma_irq);irq_set_enabled(DMA_IRQ_0,true);
    tusb_init();
    char line[256];size_t len=0;bool overflow=false;
    while(true) {
        tud_task();
        if(running && (pio->fdebug&(1u<<(PIO_FDEBUG_RXSTALL_LSB+sm)))) {
            uint32_t saved=save_and_disable_interrupts();
            loss=true;halt();ending=true;end_reason="pio_sample_loss";
            restore_interrupts(saved);
        }
        if(running && !tud_cdc_connected()) {
            uint32_t saved=save_and_disable_interrupts();
            loss=true;halt();ending=true;end_reason="usb_disconnected";
            restore_interrupts(saved);
        }
        if(frame_size) {
            uint32_t available=tud_cdc_write_available();
            if(available && tud_cdc_connected()) {
                size_t n=frame_size-frame_sent;if(n>available)n=available;
                frame_sent+=tud_cdc_write(frame+frame_sent,n);tud_cdc_write_flush();
                if(frame_sent==frame_size) {
                    frame_size=0;
                    if(frame_buffer>=0){used[frame_buffer]=0;frame_buffer=-1;}
                }
            }
        } else if(qread!=qwrite) {
            uint32_t saved=save_and_disable_interrupts();
            uint b=queue[qread%BUFFERS];qread++;
            restore_interrupts(saved);
            frame_buffer=(int)b;frame_begin(2,buffer_sample[b],buffers[b],buffer_words[b]*4);
        } else if(marker_pending) {
            // First 8 payload bytes are device receipt time in microseconds.
            uint8_t payload[208];size_t n=strlen(marker);
            memcpy(payload,&marker_us,8);memcpy(payload+8,marker,n);
            frame_begin(3,marker_sample,payload,n+8);marker_pending=false;
        } else if(ending) {
            snprintf(notice,sizeof(notice),"{\"reason\":\"%s\",\"blocks\":%u,\"sample_end\":%llu,\"loss\":%s,\"unrecorded_tail_samples_max\":%s}",
                end_reason,(unsigned)blocks,(unsigned long long)completed_sample,loss?"true":"false",loss?"null":"287");
            json_frame(loss?6:5,completed_sample,notice);ending=false;
        } else if(status_pending) {
            snprintf(notice,sizeof(notice),"{\"running\":%s,\"blocks\":%u,\"loss\":%s,\"session\":%llu}",
                running?"true":"false",(unsigned)blocks,loss?"true":"false",(unsigned long long)session);
            json_frame(4,sample_now(),notice);status_pending=false;
        }
        // Do not start a new session while a frame is being transmitted.
        while(!frame_size && tud_cdc_available()) {
            char ch; if(tud_cdc_read(&ch,1)!=1)break;
            if(ch=='\n'||ch=='\r') {
                if(len && !overflow){line[len]=0;command(line);}
                len=0;overflow=false;
            } else if(!overflow) {
                if(len+1<sizeof(line))line[len++]=ch;else overflow=true;
            }
        }
        tight_loop_contents();
    }
}
