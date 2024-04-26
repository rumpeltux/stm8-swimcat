# STM8-SwimCat

**Serial I/O using the SWIM debugger interface via stlink.**

Fan of `printf` debugging? This is for you.

`swimcat` is a tiny library implementing `putchar` on a ringbuffer that gets
polled by a remote device using the SWIM debug interface that's also used
when flashing.

If the buffer is full, `putchar` will be blocking if the `swimcat.py` listener
is connected, otherwise it will return `EOF` (-1) and not record the character.

## Usage

1. Run `make` to generate `swimcat.rel`.
2. Link `swimcat.rel` to your regular ihx binary produced by `sdcc`.
3. Flash your binary to STM8
4. Make sure `esp-stlink/python` is in your `PYTHONPATH`:

    git submodule update --init
    make -C esp-stlink/lib
    export PYTHONPATH=$PYTHONPATH:esp-stlink/python

5. Run `./swimcat.py -d /dev/ttyUSB0`.

## Run the demo

Make sure your esp-stlink is connected to `/dev/ttyUSB0` for the demo:

    git submodule update --init
    make demo

## Limitations

* Currently only works with [esp-stlink](https://github.com/rumpeltux/esp-stlink).
* stdin support (`getchar()`) is still unimplemented
