#include <stdio.h>

// Noop wait implementation for compatibility with stm8-arduino.
void yield(void) {}

void main(void) {
  for (int i = 0;; i++) {
    printf("Hello world: %d\n", i++);
  }
}
