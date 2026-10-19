#include <stdio.h>
#include <string.h>
#include "pico/stdlib.h"
#include "hardware/pio.h"
#include "hardware/clocks.h"
#include "transmit.pio.h"
#include "console.h"
#ifndef INFOGLOBE_SIG_PIN
#define INFOGLOBE_SIG_PIN 2
#endif

static PIO pio=pio0;
static uint sm, offset;
static unsigned bit_us=1000, gap_ms=20, repeat_ms;
static int zero_high=1;
static bool busy;
static uint8_t packet[PACKET_MAX];
static size_t packet_len, next_byte;
static uint64_t ready_at, repeat_at;

static void idle(void) {
    pio_sm_set_enabled(pio,sm,false);
    pio_sm_set_pins_with_mask(pio,sm,0,1u<<INFOGLOBE_SIG_PIN);
}
static void start(void) {
    pio_sm_set_enabled(pio,sm,false);
    pio_sm_clear_fifos(pio,sm);
    pio_sm_restart(pio,sm);
    pio_sm_exec(pio,sm,pio_encode_jmp(offset));
    pio_interrupt_clear(pio,0);
    float div=(float)clock_get_hz(clk_sys)*bit_us/(33.0f*1000000.0f);
    pio_sm_set_clkdiv(pio,sm,div);
    pio_sm_clkdiv_restart(pio,sm);
    pio_sm_put(pio,sm,(uint32_t)(packet_len*8-1));
    next_byte=0; busy=true;
    while (next_byte<packet_len && !pio_sm_is_tx_fifo_full(pio,sm)) {
        pio_sm_put(pio,sm,packet_word(packet,packet_len,next_byte,zero_high));
        next_byte+=4;
    }
    printf("TX %u:",(unsigned)packet_len);
    for (size_t i=0;i<packet_len;i++) printf(" %02X",packet[i]);
    printf("\n");
    pio->fdebug=1u << (PIO_FDEBUG_TXSTALL_LSB+sm);
    pio_sm_set_enabled(pio,sm,true);
}
static void pump(void) {
    if (busy) {
        while(next_byte<packet_len && !pio_sm_is_tx_fifo_full(pio,sm)) {
            pio_sm_put(pio,sm,packet_word(packet,packet_len,next_byte,zero_high));
            next_byte+=4;
        }
        if (pio_interrupt_get(pio,0)) {
            idle(); pio_interrupt_clear(pio,0); busy=false;
            ready_at=time_us_64()+(uint64_t)gap_ms*1000;
            repeat_at=ready_at+(uint64_t)repeat_ms*1000;
            puts("DONE");
        } else if (pio->fdebug & (1u << (PIO_FDEBUG_TXSTALL_LSB+sm))) {
            idle(); busy=false; repeat_ms=0;
            ready_at=time_us_64()+(uint64_t)gap_ms*1000;
            puts("ERR PIO underrun; aborted, repetition disabled");
        }
    } else if (repeat_ms && packet_len && time_us_64()>=repeat_at) start();
}
static void help(void) {
    puts("Infoglobe lab: USB serial, LF/CRLF, case-sensitive\n"
         "static TEXT | scroll TEXT | toggle\n"
         "cmd HH TEXT       hex opcode plus literal text\n"
         "effect HH TEXT    00 00 TEXT HH (effect ID in HEX)\n"
         "raw HH HH ...     exact bytes, including 00/FF; max 256\n"
         "bit N             decimal us per bit (100..10000; default 1000)\n"
         "gap N             decimal minimum silence ms (1..60000; default 20)\n"
         "polarity N        1: zero=SIG HIGH (default); 0: zero=SIG LOW\n"
         "repeat N          repeat last packet N ms AFTER gap; 0 disables\n"
         "stop              abort transmission and repetition, SIG LOW\n"
         "status | help\n"
         "Text is literal bytes, max 35; no quote or escape processing.\n"
         "SIG LOW is always idle. No acknowledgements come from the rotor.");
}
static void execute(char *line) {
    action a=parse_line(line);
    if(a.kind==ACTION_ERROR) { printf("ERR %s\n",a.error); return; }
    if(a.kind==ACTION_HELP) { help(); return; }
    if(a.kind==ACTION_STATUS) {
        printf("pin=%u bit_us=%u gap_ms=%u zero_high=%d repeat_ms=%u busy=%d last_bytes=%u\n",
               INFOGLOBE_SIG_PIN,bit_us,gap_ms,zero_high,repeat_ms,busy,(unsigned)packet_len);
        return;
    }
    if(a.kind==ACTION_STOP) {
        idle(); busy=false; repeat_ms=0;
        pio_sm_clear_fifos(pio,sm); pio_interrupt_clear(pio,0);
        ready_at=time_us_64()+(uint64_t)gap_ms*1000;
        puts("OK stopped; rotor message is unchanged"); return;
    }
    if(busy) { puts("ERR transmitter busy; stop or wait for DONE"); return; }
    if(a.kind==ACTION_SEND) {
        if(time_us_64()<ready_at) { puts("ERR inter-packet gap; retry shortly"); return; }
        memcpy(packet,a.bytes,a.length); packet_len=a.length; start(); return;
    }
    switch(a.kind) {
        case ACTION_BIT: bit_us=a.value; break;
        case ACTION_GAP: gap_ms=a.value;
            if (ready_at<time_us_64()+(uint64_t)gap_ms*1000)
                ready_at=time_us_64()+(uint64_t)gap_ms*1000;
            break;
        case ACTION_POLARITY: zero_high=(int)a.value; break;
        case ACTION_REPEAT:
            repeat_ms=a.value;
            repeat_at=(time_us_64()>ready_at ? time_us_64():ready_at)+(uint64_t)repeat_ms*1000;
            break;
        default: break;
    }
    puts("OK");
}
int main(void) {
    stdio_init_all();
    offset=pio_add_program(pio,&transmit_program);
    sm=pio_claim_unused_sm(pio,true);
    pio_gpio_init(pio,INFOGLOBE_SIG_PIN);
    pio_sm_set_consecutive_pindirs(pio,sm,INFOGLOBE_SIG_PIN,1,true);
    pio_sm_config c=transmit_program_get_default_config(offset);
    sm_config_set_out_pins(&c,INFOGLOBE_SIG_PIN,1);
    sm_config_set_set_pins(&c,INFOGLOBE_SIG_PIN,1);
    sm_config_set_out_shift(&c,false,true,32); // MSB first, autopull 32 bits
    sm_config_set_fifo_join(&c,PIO_FIFO_JOIN_TX);
    pio_sm_init(pio,sm,offset,&c); idle();
    char line[LINE_MAX_SIZE]; size_t used=0; bool overflow=false, after_cr=false;
    while(true) {
        pump();
        int ch=getchar_timeout_us(0);
        if(ch==PICO_ERROR_TIMEOUT) { tight_loop_contents(); continue; }
        if(ch=='\n' && after_cr) { after_cr=false; continue; }
        after_cr=ch=='\r';
        if(ch=='\r' || ch=='\n') {
            if(overflow) puts("ERR line too long; discarded");
            else if(used) { line[used]=0; execute(line); }
            used=0; overflow=false;
        } else if(ch==8 || ch==127) { if(!overflow && used) used--; }
        else if(ch==0) { overflow=true; }
        else if(!overflow) {
            if(used+1<sizeof(line)) line[used++]=(char)ch;
            else overflow=true;
        }
    }
}
