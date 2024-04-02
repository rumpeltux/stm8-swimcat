#include <stdio.h>
#include <stdint.h>

// Arduino.
extern void yield();

// bufsize 8 (3 bits): 1.5kb/s
// bufsize 128 (7 bits): 5kb/s
// max bufsize_bits: 7 (128 byte buffer)
#ifndef SWIMCAT_BUFSIZE_BITS
#  define BUFSIZE_BITS 3
#else
#  define BUFSIZE_BITS SWIMCAT_BUFSIZE_BITS
#endif

#define BUFSIZE (1 << BUFSIZE_BITS)
#define DEFAULT_BUFSIZE (BUFSIZE_BITS == 3)

struct swimcat {
  uint8_t magic[2];
#if !DEFAULT_BUFSIZE
  uint8_t size_indicator;
#endif
  volatile uint8_t read_idx;
  uint8_t write_idx;
  uint8_t stdout[BUFSIZE];
} swimcat = {
  .magic = {'S', 0xB9},
#if !DEFAULT_BUFSIZE
  .size_indicator = 0x80 | BUFSIZE_BITS,
#endif
};

int putchar(int c) {
  uint8_t occupied;
  uint8_t free;

  do {
    occupied = (swimcat.write_idx - swimcat.read_idx) & (2 * BUFSIZE - 1);
    free = BUFSIZE - occupied;
  } while(!free);
  
  swimcat.stdout[swimcat.write_idx & (BUFSIZE - 1)] = c;
  // we keep one more bit for the counter, so that we can distinguish
  // empty vs full.
  swimcat.write_idx = (swimcat.write_idx + 1) & (2 * BUFSIZE - 1);
  return c;
}

void swimcat_flush() {
  while(swimcat.write_idx != swimcat.read_idx) yield();
}
