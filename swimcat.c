#include <stdio.h>
#include <stdint.h>

// bufsize 8 (3 bits): 1.5kb/s
// bufsize 128 (7 bits): 5kb/s
// max bufsize_bits: 7 (128 byte buffer)
#define BUFSIZE_BITS 3
#define BUFSIZE (1 << BUFSIZE_BITS)
#define DEFAULT_BUFSIZE (BUFSIZE_BITS == 3)

struct swimcat {
  uint8_t magic[2];
#if !DEFAULT_BUFSIZE
  uint8_t size_indicator;
#endif
  uint8_t read_idx;
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
  swimcat.write_idx = (swimcat.write_idx + 1) & (2 * BUFSIZE - 1);
  return c;
}
