#ifndef INFOGLOBE_CONSOLE_H
#define INFOGLOBE_CONSOLE_H
#include <stddef.h>
#include <stdint.h>
#define PACKET_MAX 256
#define LINE_MAX_SIZE 1024
#define TEXT_MAX 35

typedef enum { ACTION_ERROR, ACTION_SEND, ACTION_HELP, ACTION_STATUS,
    ACTION_STOP, ACTION_BIT, ACTION_GAP, ACTION_POLARITY, ACTION_REPEAT } action_kind;
typedef struct {
    action_kind kind;
    uint8_t bytes[PACKET_MAX];
    size_t length;
    unsigned value;
    const char *error;
} action;
// Modifies the supplied line. Numeric settings are decimal; byte arguments are hex.
action parse_line(char *line);
uint32_t packet_word(const uint8_t *data, size_t length, size_t offset, int zero_high);
#endif
