#include "console.h"
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <errno.h>

static char *token(char **s) {
    while (**s == ' ' || **s == '\t') ++*s;
    if (!**s) return NULL;
    char *start = *s;
    while (**s && **s != ' ' && **s != '\t') ++*s;
    if (**s) *(*s)++ = 0;
    return start;
}
static bool number(const char *s, unsigned base, unsigned max, unsigned *out) {
    if (!s || !*s || *s == '-' || *s == '+') return false;
    errno = 0;
    char *end;
    unsigned long n = strtoul(s, &end, base);
    if (errno || *end || n > max) return false;
    *out = (unsigned)n;
    return true;
}
static action bad(const char *s) { return (action){.kind=ACTION_ERROR,.error=s}; }

action parse_line(char *line) {
    char *cursor = line;
    char *cmd = token(&cursor);
    if (!cmd) return bad("empty command");
    action a = {0};
    if (!strcmp(cmd,"raw")) {
        char *t;
        while ((t=token(&cursor))) {
            unsigned b;
            if (a.length == PACKET_MAX) return bad("packet exceeds 256 bytes");
            if (!number(t,16,255,&b)) return bad("raw requires hex bytes: raw 04 48 49");
            a.bytes[a.length++] = (uint8_t)b;
        }
        if (!a.length) return bad("raw requires at least one byte");
        a.kind=ACTION_SEND;
        return a;
    }
    bool text = false;
    if (!strcmp(cmd,"static") || !strcmp(cmd,"scroll")) {
        a.bytes[a.length++] = !strcmp(cmd,"static") ? 1 : 4;
        text=true;
    } else if (!strcmp(cmd,"cmd") || !strcmp(cmd,"effect")) {
        unsigned b;
        if (!number(token(&cursor),16,255,&b)) return bad("expected hex opcode/effect byte");
        if (!strcmp(cmd,"cmd")) a.bytes[a.length++] = (uint8_t)b;
        else { a.bytes[a.length++]=0; a.bytes[a.length++]=0; a.value=b; }
        text=true;
    } else if (!strcmp(cmd,"toggle")) {
        a.kind=ACTION_SEND; a.bytes[0]=6; a.length=1;
    } else if (!strcmp(cmd,"help")) a.kind=ACTION_HELP;
    else if (!strcmp(cmd,"status")) a.kind=ACTION_STATUS;
    else if (!strcmp(cmd,"stop")) a.kind=ACTION_STOP;
    else {
        unsigned max;
        if (!strcmp(cmd,"bit")) { a.kind=ACTION_BIT; max=10000; }
        else if (!strcmp(cmd,"gap")) { a.kind=ACTION_GAP; max=60000; }
        else if (!strcmp(cmd,"repeat")) { a.kind=ACTION_REPEAT; max=3600000; }
        else if (!strcmp(cmd,"polarity")) { a.kind=ACTION_POLARITY; max=1; }
        else return bad("unknown command; type help");
        if (!number(token(&cursor),10,max,&a.value)) return bad("invalid decimal setting");
        if (a.kind==ACTION_BIT && a.value<100) return bad("bit range is 100..10000 us");
        if (a.kind==ACTION_GAP && a.value<1) return bad("gap range is 1..60000 ms");
    }
    if (text) {
        // One delimiter follows the opcode/command; further spaces are literal text.
        size_t n=strlen(cursor);
        if (n>TEXT_MAX) return bad("text exceeds 35 bytes; use raw for longer experiments");
        memcpy(a.bytes+a.length,cursor,n); a.length+=n;
        if (!strcmp(cmd,"effect")) a.bytes[a.length++]=(uint8_t)a.value;
        a.kind=ACTION_SEND;
    } else if (token(&cursor)) return bad("unexpected argument");
    return a;
}

uint32_t packet_word(const uint8_t *data, size_t length, size_t offset, int zero_high) {
    uint32_t word=0;
    for (size_t i=0;i<4;i++) {
        uint8_t b=offset+i<length ? data[offset+i] : 0xff;
        if (zero_high) b^=0xff;
        word=(word<<8)|b;
    }
    return word;
}
