#!/usr/bin/env python
# -*- coding:utf8 -*-

import serial
from ctypes import *
from time import sleep

maplib = cdll.LoadLibrary("libmapd_lib_dyn.so")

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

"""
res_str = create_string_buffer(size_of_buffer)
rc = l.check_param(1, 2, byref(res_str))
print "rc=", rc
print "res_str=", str(res_str.raw)
"""




class MAP:
    map_answer = ''
    eeprom1 = ''
    eeprom2 = ''
    fd = -1
    buf = create_string_buffer(size_of_buffer)
    def __init__(self, port_name, baudrate, timeout):
        self.port = serial.Serial(port_name, baudrate=baudrate, timeout=timeout)
        self.fd = self.port.fileno()
    def send_command(self, command, addr, page):
        maplib.send_command(command, self.fd, addr, page, byref(self.buf))
    def read_answer(self):
        return maplib.read_answer(self.fd, byref(self.buf))
    def read_data(self):
        return maplib.read_data(self.fd)
    def read_eeprom(self):
        self.send_command(to_read, 0, 0xFF)
        #self.eeprom1 = self.read_data()
        self.rc = self.read_answer()
        if 0 == self.rc:
            self.eeprom1 = self.buf
        else:            
            self.eeprom1 = ''
            print "rc_read_eeprom1=", self.rc
        #
        self.send_command(to_read, 0x100, 0xFF)
        self.rc = self.read_answer()
        if 0 == self.rc:
            self.eeprom2 = self.buf
        else:            
            self.eeprom2 = ''
            print "rc_read_eeprom2=", self.rc
        #self.eeprom2 = self.read_data()

mapups = MAP('/dev/ttyUSB0', baudrate=19200, timeout=5)
print "MAP created"
#print mapups
print "port=", mapups.port
print "fd=", mapups.fd
print "len(buf)=", len(mapups.buf)
print "type(buf)=", type(mapups.buf)

"""
mapups.send_command(to_read, 0, 0xFF)
rc = mapups.read_answer()
res = mapups.buf
res = maplib.read_data(mapups.fd)
print "type(res.raw)=", type(res.raw)
print "res=", repr(res.raw)
"""

mapups.read_eeprom()
H = ord(mapups.eeprom2[0x69]) + 100
L = ord(mapups.eeprom2[0x6A]) + 100
print "H=", H
print "L=", L
#print "type(mapups.eeprom2)=", type(mapups.eeprom2)
print "mapups.eeprom1="
print ''.join("{:02x}".format(ord(c)) for c in mapups.eeprom1)
print "mapups.eeprom2="
print ''.join("{:02x}".format(ord(c)) for c in mapups.eeprom2)

"""
rc_put = maplib.put_command(to_read, mapups.fd, 0, 0xFF, byref(mapups.buf))
print "rc_put=", rc_put
print "in_waiting=", mapups.port.in_waiting

rc = maplib.read_answer(mapups.fd, byref(mapups.buf))
print "rc=", rc
if 0 == rc :
    print ''.join("{:02x}".format(ord(c)) for c in mapups.buf)
else:
    print "Error"
"""    
