CC := sdcc
CFLAGS := -mstm8 --std-c99 --opt-code-size

TARGET ?= demo

all: $(TARGET).ihx

.SECONDARY:

%.rel: %.o %.c
	@echo -n

%.rel: %.S
	sdasstm8 -lo $<

demo.ihx: swimcat.rel

%.ihx: %.rel
	$(CC) $(CFLAGS) $^

flash: $(TARGET).ihx
	make -C esp-stlink/lib
	esp-stlink/python/flash.py -i $<
	
demo: flash
	./swimcat.py

clean:
	rm -f *.asm *.adb *.ihx *.cdb *.lst *.map *.mem *.lk *.rel *.rst *.sym *.o
