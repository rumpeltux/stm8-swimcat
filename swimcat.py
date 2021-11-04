#!/usr/bin/env python3
import espstlink
import datetime
import sys
import time

from espstlink.debugger import Debugger, CPU


RAMSIZE = 1024
MAGIC = b'S\xB9'

class SwimCat(object):
  def __init__(self, dev, show_date=False, unstall=False):
    self.dev = dev
    self.show_date = show_date
    self.pos = self.find_swim_buffer()
    b = self.dev.read_bytes(self.pos, 3)
    if (b[0] & 0xF0) == 0:
      self.bufsize = 8
    else:
      self.bufsize = 1 << (b[0] & 0x7)
      self.pos += 1
    if unstall:
      deb = Debugger(dev)
      deb.cont()
    print("SWIMCAT(%d)" % self.bufsize, file=sys.stderr)

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
    while True:
      try:
        b = self.dev.read_bytes(self.pos, 2 + self.bufsize)
        r_index = b[0]
        w_index = b[1]
        if r_index >= self.bufsize * 2 or w_index > self.bufsize * 2:
          raise espstlink.STLinkException()
        break
      except espstlink.STLinkException:
        time.sleep(0.1)
        # device may be in halt mode or resetted, keep retrying
        while True:
          try:
            dev.init(reset=False)
            break
          except espstlink.STLinkException:
            time.sleep(1)

    r_index = b[0]
    w_index = b[1]
    # set r_index := w_index on device
    self.dev.write(self.pos, w_index)

    avail = (w_index - r_index) % (2 * self.bufsize)
    if avail:
      b = b[2:]
      #print('have', avail)
      w_index %= self.bufsize
      r_index %= self.bufsize
      if w_index > r_index:
        msg = b[r_index:w_index]
      else:
        msg = b[r_index:self.bufsize] + b[0:w_index]
      if self.show_date:
        msg = msg.replace(b'\n', b'\n' + datetime.datetime.now().isoformat().encode() + b'\t')
      return msg
    return b''

if __name__ == '__main__':
  import argparse
  import sys
  import time
  parser = argparse.ArgumentParser()
  parser.add_argument("-d", "--device", default='/dev/ttyUSB0',
                    help="The serial device the HC is connected to")
  parser.add_argument("-c", "--continue", action='store_true',
                      help="Unstall the device (disable the debugger breakpoint and continue program execution)")
  parser.add_argument("-r", "--reset", action='store_true',
                     help="Reset the device when connecting (implies --continue)")
  parser.add_argument("-D", "--date", action='store_true',
                     help="Show date in front of each line")
  args = parser.parse_args()

  dev = espstlink.STLink(args.device.encode())
  dev.init(reset=args.reset)
  # Reset requires unstall so that GSINIT can finish and we can find the SWIMCAT buffer.
  unstall = vars(args)['continue'] or args.reset
  s = SwimCat(dev, args.date, unstall)
  while True:
    b = s.poll()
    if b:
      sys.stdout.buffer.write(b)
      sys.stdout.buffer.flush()
    else:
      time.sleep(.001)
