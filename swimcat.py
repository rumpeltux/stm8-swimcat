#!/usr/bin/env python3
import espstlink
import datetime
import sys
import time

from espstlink.debugger import Debugger, CPU
import swimtrace

ROMSIZE = 8192
ROM_BASE = 0x8000
MAGIC = b'sC\xB9'
FLAG_BLOCK = 1

class SwimCat(object):
  def __init__(self, dev, show_date=False, unstall=False, blocking=True):
    self.dev = dev
    self.show_date = show_date

    rom_pos = self.find_swim_buffer()
    config = self.dev.read_bytes(rom_pos, 5)
    self.bufsize = 1 << (config[0] & 0x7)
    self.struct_pos = config[1] << 8 | config[2]
    self.buffer_pos = config[3] << 8 | config[4]
    self.flags = self.dev.read(self.struct_pos)

    # Write to RAM that future calls should be blocking.
    self.dev.write(self.struct_pos, blocking and FLAG_BLOCK)
    if unstall:
      # If the device just reset than RAM may not have been initialized, so our
      # FLAG_BLOCK would be overwritten by RAM initialization. So we set a breakpoint
      # to catch this.
      deb = Debugger(dev)
      deb.breakpoint('Data Write on @=BK1 and Data=BK2L', bk1=self.struct_pos, bk2=0)
      deb.cont()
      # wait until we hit the breakpoint
      while deb.DM_CSR2['STALL'] == 0:
        pass
      deb.breakpoint('Disabled')
      self.dev.write(self.struct_pos, blocking and FLAG_BLOCK)
      deb.cont()

    self.date_pending = True
    print("SWIMCAT(%d)" % self.bufsize, file=sys.stderr)

  def canReadRam(self):
    return self.dev.read_bytes(0x1000, 4)

  def find_swim_buffer(self):
    rb = b''
    pos = None
    for i in range(0, ROMSIZE, 0x80):
      rb += self.dev.read_bytes(ROM_BASE + i, 0x80)
      pos = rb.find(MAGIC)
      if pos == -1: continue
      return ROM_BASE + pos + len(MAGIC)
    open('/tmp/swimcat-rom.bin', 'wb').write(rb)
    raise RuntimeError('Could not locate SWIM buffer in /tmp/swimcat-rom.bin. Did you link swimcat.rel?')
  
  def poll(self):
    while True:
      try:
        b = self.dev.read_bytes(self.struct_pos, 3)
        flags = b[0]
        r_index = b[1]
        w_index = b[2]
        if r_index >= self.bufsize * 2 or w_index > self.bufsize * 2 or flags > 1:
          raise espstlink.STLinkException()
        if r_index == w_index:
          return b''
        avail = (w_index - r_index) % (2 * self.bufsize)
        if avail:
          b = self.dev.read_bytes(self.buffer_pos, self.bufsize)
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

    # Mark the data as read by setting r_index = w_index.
    self.dev.write(self.struct_pos + 1, w_index)
    if avail:
      w_index %= self.bufsize
      r_index %= self.bufsize
      if w_index > r_index:
        msg = b[r_index:w_index]
      else:
        msg = b[r_index:self.bufsize] + b[0:w_index]
      if self.show_date:
        date = datetime.datetime.now().isoformat().encode() + b'\t'
        if self.date_pending:
          msg = date + msg
        msg = msg[:-1].replace(b'\n', b'\n' + date) + msg[-1:]
        self.date_pending = msg[-1:] == b'\n'
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
  parser.add_argument("-n", "--non-blocking", action='store_true',
                     help="Do not put swimcat in blocking mode (may cause missing data)")
  parser.add_argument("-r", "--reset", action='store_true',
                     help="Reset the device when connecting (implies --continue)")
  parser.add_argument("-D", "--date", action='store_true',
                     help="Show date in front of each line")
  args = parser.parse_args()

  dev = espstlink.STLink(args.device.encode())
  dev.init(reset=args.reset)
  # Reset requires unstall so that GSINIT can finish and we can find the SWIMCAT buffer.
  unstall = vars(args)['continue'] or args.reset
  s = SwimCat(dev, args.date, unstall, not args.non_blocking)
  while True:
    b = s.poll()
    if b:
      sys.stdout.buffer.write(b)
      sys.stdout.buffer.flush()
    else:
      time.sleep(.001)
