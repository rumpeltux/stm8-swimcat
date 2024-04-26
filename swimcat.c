#include <stdint.h>
#include <stdio.h>

// For Arduino. You can provide a no-op implementation otherwise.
extern void yield(void);

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

#define BUFSIZE_MASK (BUFSIZE - 1)
#define BUFSIZE_2X_MASK (2 * BUFSIZE - 1)

// Whether output should be blocking on full buffer.
#define FLAG_BLOCK (1 << 0)

static struct swimcat {
  uint8_t flags;
  volatile uint8_t read_idx;
  uint8_t write_idx;
} swimcat = {0, 0, 0};

static uint8_t stdout[BUFSIZE];

static const struct swimcat_info {
  uint8_t magic[3];
  uint8_t flags;
  void *swimcat_struct;
  void *stdout_buffer;
} swimcat_info = {.magic = {'s', 'C', 0xB9},
                  .flags = BUFSIZE_BITS,
                  .swimcat_struct = &swimcat,
                  .stdout_buffer = &stdout};

int putchar(int c) {
  uint8_t occupied;
  uint8_t free;

  do {
    occupied = (swimcat.write_idx - swimcat.read_idx) & BUFSIZE_2X_MASK;
    free = BUFSIZE - occupied;
    if (!free && (swimcat.flags & FLAG_BLOCK) == 0) {
      // no SWIM listener is connected, rather than blocking the application
      // we fail the character output.
      return EOF;
    }
  } while (!free);

  stdout[swimcat.write_idx & BUFSIZE_MASK] = c;
  // we keep one more bit for the counter, so that we can distinguish
  // empty vs full.
  swimcat.write_idx = (swimcat.write_idx + 1) & BUFSIZE_2X_MASK;
  return c;
}

void swimcat_flush(void) {
  if ((swimcat.flags & FLAG_BLOCK) == 0)
    return;
  while (swimcat.write_idx != swimcat.read_idx)
    yield();
}
