#include "console.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
static action parse(const char *s) {
    char copy[2048]; assert(strlen(s)<sizeof(copy)); strcpy(copy,s);
    return parse_line(copy);
}
static void bytes(const char *s,const uint8_t *expected,size_t n) {
    action a=parse(s); assert(a.kind==ACTION_SEND); assert(a.length==n);
    assert(!memcmp(a.bytes,expected,n));
}
int main(void) {
    bytes("scroll HI",(uint8_t[]){4,0x48,0x49},3);
    bytes("static HI",(uint8_t[]){1,0x48,0x49},3);
    bytes("effect 0C HI",(uint8_t[]){0,0,0x48,0x49,0x0c},5);
    bytes("cmd 02 HI",(uint8_t[]){2,0x48,0x49},3);
    bytes("cmd FE  X",(uint8_t[]){0xfe,0x20,0x58},3);
    bytes("toggle",(uint8_t[]){6},1);
    bytes("raw 00 FF 80 0x04",(uint8_t[]){0,255,128,4},4);
    bytes("static",(uint8_t[]){1},1);
    const char *invalid[]={"raw","raw 100","raw GG","raw -1","raw 01 junk",
        "effect 100 HI","cmd ZZ HI","toggle garbage","status x","help x",
        "bit 99","bit 10001","bit -1","bit 1000x","bit 1000 x",
        "gap 0","repeat 3600001","polarity 2","unknown",""};
    for(size_t i=0;i<sizeof(invalid)/sizeof(*invalid);i++)
        assert(parse(invalid[i]).kind==ACTION_ERROR);
    assert(parse("bit 1000").value==1000);
    assert(parse("repeat 0").kind==ACTION_REPEAT);
    char text[80]="scroll "; memset(text+7,'X',35);text[42]=0;
    assert(parse(text).length==36);text[42]='X';text[43]=0;
    assert(parse(text).kind==ACTION_ERROR);
    char raw[1024]="raw";
    for(int i=0;i<256;i++)strcat(raw," AA");
    assert(parse(raw).length==256);strcat(raw," BB");
    assert(parse(raw).kind==ACTION_ERROR);
    uint8_t p[]={0x04,0x48,0x49,0xff,0x00};
    assert(packet_word(p,5,0,1)==0xfbb7b600u);
    assert(packet_word(p,5,4,1)==0xff000000u);
    assert(packet_word(p,5,0,0)==0x044849ffu);
    puts("PASS: packet formats, raw binary, bounds, invalid input, polarity, MSB packing");
}
