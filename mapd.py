#!/usr/bin/env python
# -*- coding:utf8 -*-

import serial
#from ctypes import *
from time import sleep


size_of_buffer = 560
to_read = 0x72
to_write = 0x77


"""
class MAPdata(Structure):
    _fields_ = [('filler', 361 * c_char),
                 ('Vlow', c_int),
                 ('Vhigh', c_int),
                 ('c', c_char)]
"""


class MAP:
    port = ''
    summ = 0
    Buffer = []
    def __init__(self, port_name, baudrate, timeout):
        self.port = serial.Serial(port_name, baudrate=baudrate, timeout=timeout)
    def put_char(a):
        w_cnt = self.port.write(a)
        a1 = self.port.read()
        if a != a1:
            try_read = True
            cnt = 0
            while try_read:
                a1 = self.port.read()
                cnt += 1
                if cnt > 20:
                    try_read = False
            if a != a1:
                return False
            else
                return True

    def code_DB(self, a):
        if a == '\n':
            self.summ += 0xDB
            if not self.put_char(self,0xDB):
                return
            self.summ += 0xDC
            if not self.put_char(self,0xDC):
                return
        elif a == 0xDB:
            self.summ += 0xDB
            if not self.put_char(self,0xDB):
                return
            self.summ += 0xDD
            if not self.put_char(self,0xDD):
                return
        else:
            self.summ += a
            self.put_char(self,a)
        return

    def send_command(self, command, addr, page):
        self.summ = 0
        a[0] = command
        a[1] = page
        a[2] = addr >> 8
        a[3] = addr & 0xFF
        for i in range(0, 4):
            self.code_DB(self, a[i])          #
        if command == to_write:
            for i in range(page+1):
              self.code_DB(self, self.Buffer[i])
        self.summ = 0xFF - self.summ
        self.summ += 1
        if not self.put_char(self, self.summ):
            return
        if self.summ != '\n':
            self.put_char(self, '\n')
        return

    










map = MAP('/dev/ttyUSB0', timeout=5)
print "MAP created"
print map

map.send_command(to_read, 0, 0xFF)
