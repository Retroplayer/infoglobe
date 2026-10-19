#include "tusb.h"
#include "pico/unique_id.h"
static const tusb_desc_device_t device = {
    .bLength=sizeof(tusb_desc_device_t), .bDescriptorType=TUSB_DESC_DEVICE,
    .bcdUSB=0x0200, .bDeviceClass=TUSB_CLASS_MISC,
    .bDeviceSubClass=MISC_SUBCLASS_COMMON, .bDeviceProtocol=MISC_PROTOCOL_IAD,
    .bMaxPacketSize0=64, .idVendor=0x2e8a, .idProduct=0x000a,
    .bcdDevice=0x0100, .iManufacturer=1, .iProduct=2, .iSerialNumber=3,
    .bNumConfigurations=1
};
uint8_t const *tud_descriptor_device_cb(void) { return (uint8_t const *)&device; }
enum { ITF_CDC, ITF_DATA, ITF_COUNT };
static const uint8_t configuration[] = {
    TUD_CONFIG_DESCRIPTOR(1,ITF_COUNT,0,TUD_CONFIG_DESC_LEN+TUD_CDC_DESC_LEN,0,100),
    TUD_CDC_DESCRIPTOR(ITF_CDC,4,0x81,8,0x02,0x82,64)
};
uint8_t const *tud_descriptor_configuration_cb(uint8_t index) { (void)index; return configuration; }
uint16_t const *tud_descriptor_string_cb(uint8_t index,uint16_t langid) {
    (void)langid;
    static uint16_t result[64];
    static char serial[PICO_UNIQUE_BOARD_ID_SIZE_BYTES*2+1];
    const char *strings[]={"","Infoglobe project","Infoglobe IR recorder",serial,"IR capture CDC"};
    if(index==0) { result[0]=(TUSB_DESC_STRING<<8)|4; result[1]=0x0409; return result; }
    if(index>=sizeof(strings)/sizeof(*strings)) return NULL;
    pico_get_unique_board_id_string(serial,sizeof(serial));
    size_t n=strlen(strings[index]); if(n>63)n=63;
    for(size_t i=0;i<n;i++)result[i]=(uint8_t)strings[index][i];
    result[0]=(TUSB_DESC_STRING<<8)|(2*n+2);
    return result;
}
