#/usr/bin/env python3
import struct

from selfdrive.car.hyundai.interface import CarInterface
from selfdrive.car.hyundai.hyundaican import hyundai_checksum
from tools.lib.route import Route
from tools.lib.logreader import LogReader


"""
msgs with checksums that we use in panda rx hook:
608  - 4 bits
897  - 8 bits, same algorithm as LKAS checksum
902  - 4 bits, split over 2 2-bit signals like counter
916  - 4 bits
1057 - 4 bits


seems like the checksum doesn't use the counter
"""

def get_checksum(addr, dat):
  ret = 0
  if addr == 902:
    ret = ((dat[7] >> 4) & 0xc) | (dat[5] >> 6)
  elif addr == 897:
    ret = dat[6]
  elif addr == 608:
    ret = dat[7] & 0xF
  return ret

def calc_checksum(addr, dat):
  ret = 0
  if addr == 902:
    ret = 0
    while addr:
      ret += addr & 0xF
      addr = addr >> 4
    ret = 0
    for i, b in enumerate(dat):
      if i % 2 != 0:
        b = b & 0x3f # mask off checksum and counter
      ret += b
    ret = (addr-ret) & 0xF
  elif addr == 897:
    dat = dat[:6] + dat[7:8]
    #print(dat)
    ret = hyundai_checksum(dat)
  elif addr == 608:
    ret = 0
    #while addr:
    #  ret += addr & 0xF
    #  addr = addr >> 4
    for i, b in enumerate(dat):
      if i == 7:
        b = b & 0xc0
      ret += b
    ret = ret % 0xF
  return ret


# wheel speed when not moving
addr = 902
dats = [
  # not moving, wheel speeds = 0
  b'\x00\xc0\x00\x00\x00\x40\x00\x80',
  # 1 wheel has speed 1
  b'\x00\x80\x00\x40\x01\x00\00\x80',
  # 2 wheels have speed 1
  b'\x00\x00\x00\x00\x01\xc0\01\x80',
]
for dat in dats:
  chksum = get_checksum(addr, dat)
  chksum2 = calc_checksum(addr, dat)
  print(chksum, chksum2)
exit(0)


r = Route("02c45f73a2e5c6e9|2020-05-14--09-37-41")
lr = LogReader(r.log_paths()[0])

canmsg = filter(lambda m: m.which() == 'can', lr)

target_msg = 902
msgs = []
for can in canmsg:
  for msg in can.can:
    if msg.address == target_msg and msg.src == 0:
      msgs.append(msg)
      if len(msgs) > 200:
        break
#print(len(msgs))


a = []
for m in msgs:
  chksum = get_checksum(m.address, m.dat)
  chksum2 = calc_checksum(m.address, m.dat)
  a.append(chksum==chksum2)
  print(chksum, chksum2)
print(all(a))
