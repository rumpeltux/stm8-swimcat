#!/usr/bin/env python3
import espstlink

RAMSIZE = 1024
MAGIC = b'S\xB9'

class SwimCat(object):
  def __init__(self, dev):
    self.dev = dev
    self.pos = self.find_swim_buffer()
    b = self.dev.read_bytes(self.pos, 3)
    if (b[0] & 0xF0) == 0:
      self.bufsize = 8
    else:
      self.bufsize = 1 << (b[0] & 0x7)
      self.pos += 1
  
  def find_swim_buffer(self):
    rb = b''
    pos = None
    for i in range(0, RAMSIZE, 0x80):
      rb += self.dev.read_bytes(i, 0x80)
      pos = rb.find(MAGIC)
      if pos == -1: continue
      return pos + 2
    raise RuntimeError('Could not locate SWIM buffer in RAM. Did you link swimcat.rel?')
  
  def poll(self):
    b = self.dev.read_bytes(self.pos, 2 + self.bufsize)
    #print(b)
    r_index = b[0]
    w_index = b[1]
    self.dev.write(self.pos, w_index)
    avail = (w_index - r_index) % (2 * self.bufsize)
    if avail:
      b = b[2:]
      #print('have', avail)
      w_index %= self.bufsize
      r_index %= self.bufsize
      if w_index > r_index:
        return b[r_index:w_index]
      return b[r_index:self.bufsize] + b[0:w_index]
    return b''

if __name__ == '__main__':
  import argparse
  import sys
  import time
  parser = argparse.ArgumentParser()
  parser.add_argument("-d", "--device", default='/dev/ttyUSB0',
                    help="The serial device the HC is connected to")
  # TODO: This won't really work unless we also unstall and wait for the GSINIT to finish
  parser.add_argument("-r", "--reset", action='store_true',
                     help="Reset the device when connecting")
  args = parser.parse_args()

  dev = espstlink.STLink(args.device.encode())
  dev.init(reset=args.reset)
  s = SwimCat(dev)
  while True:
    b = s.poll()
    if b:
      #print(b)
      sys.stdout.buffer.write(b)
      sys.stdout.buffer.flush()
    else:
      time.sleep(.001)
