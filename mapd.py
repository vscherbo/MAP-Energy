#!/usr/bin/env python
# -*- coding:utf8 -*-

import serial
from ctypes import *
from time import sleep
from datetime import datetime
import copy

maplib = cdll.LoadLibrary("libmapd_lib_dyn.so")

size_of_buffer = 560
to_read = 0x72
to_write = 0x77


class MAPdata(Structure):
    _fields_ = [ ('_MODE', c_ubyte), # режим работы МАП
 ('_Status_Char', c_ubyte),
 ('_Uacc', c_float), # напряжение АКБ
 ('_Iacc', c_uint),
 ('_PLoad', c_uint), # мощность по линии АКБ-МАП
 ('_F_Acc_Over', c_ubyte),
 ('_F_Net_Over', c_ubyte),
 ('_UNET', c_uint), # напряжение с подстанции (вход)
 ('_INET', c_ubyte),
 ('_PNET', c_uint), # мощность с подстанции (вход)
 ('_TFNET', c_ubyte), # частота с подстанции (вход)
 ('_ThFMAP', c_ubyte), # частота с МАП (выход)
 ('_UOUTmed', c_uint), # напряжение с МАП (выход)
 ('_TFNET_Limit', c_ubyte),
 ('_UNET_Limit', c_uint),
 ('_RSErrSis', c_ubyte),
 ('_RSErrJobM', c_ubyte),
 ('_RSErrJob', c_ubyte),
 ('_RSWarning', c_ubyte),
 ('_Temp_Grad0', c_ubyte), # температура АКБ
 ('_Temp_Grad2', c_ubyte), # температура транзисторов
 ('_INET_16_4', c_float), # ток (вход)
 ('_IAcc_med_A_u16', c_float), # ток по АКБ
 ('_Temp_off', c_ubyte),
 ('_E_NET', c_ulong),
 ('_E_ACC', c_ulong),
 ('_E_ACC_CHARGE', c_ulong),
 ('_Uacc_optim', c_float),
 ('_I_acc_avg', c_float),
 ('_I_mppt_avg', c_float),
 ('_I2C_err', c_ubyte) ]

class MAP:
    eeprom = ''
    fd = -1
    t_start = 0
    t_fin = 0
    Vhigh = 0
    Vlow = 0
    mdata = MAPdata()
    mdata._Status_Char = 0
    mdata._TFNET = 0
    buf = create_string_buffer(size_of_buffer)
    def __init__(self, port_name, baudrate, timeout):
        self.port = serial.Serial(port_name, baudrate=baudrate, timeout=timeout)
        self.fd = self.port.fileno()
    def send_command(self, command, addr, page):
        self.t_start = datetime.now()
        print 'start send_command=', self.t_start
        maplib.send_command(command, self.fd, addr, page, byref(self.buf))
        self.t_fin = datetime.now()
        print 'finish send_command=', self.t_fin
        print "delta=", (self.t_fin - self.t_start).total_seconds()
    def read_answer(self):
        return maplib.read_answer(self.fd, byref(self.buf))
    def read_data(self):
        return maplib.read_data(self.fd)
    def read_eeprom(self):
        self.send_command(to_read, 0, 0xFF)
        self.rc = self.read_answer()
        if 0 == self.rc:
            self.eeprom = self.buf[:0xFF]
        else:            
            self.eeprom = ''
            print "rc_read_eeprom1=", self.rc
            return False
        #
        self.send_command(to_read, 0x100, 0xFF)
        self.rc = self.read_answer()
        if 0 == self.rc:
            self.eeprom += self.buf[:0xFF]
        else:            
            self.eeprom = ''
            print "rc_read_eeprom2=", self.rc
            return False
        return True
    def read_data(self):
        self.send_command(to_read, 0x400, 0xFF)
        self.rc = self.read_answer()
        if 0 == self.rc:
            self.mdata._Status_Char = c_ubyte(ord(self.buf[0x402 - 0x3FF]))
            #self.mdata._PLoad = c_uint(100*ord(self.buf[0x409 - 0x3FF]))
            #memmove(addressof(self.buf)+0x409 - 0x3FF, self.mdata._PLoad, 2)
            self.mdata._PLoad *= 100
            self.mdata._TFNET = c_ubyte(6250/ord(self.buf[0x425 - 0x3FF]))
            self.mdata._ThFMAP = c_ubyte(6250/ord(self.buf[0x426 - 0x3FF]))

        else:            
            self.mdata = ''
            print "rc_read_data=", self.rc
            return False
        return True

mapups = MAP('/dev/ttyUSB0', baudrate=19200, timeout=5)
print "MAP created"
print "port=", mapups.port


if mapups.read_eeprom():
    H = ord(mapups.eeprom[0x169]) + 100
    L = ord(mapups.eeprom[0x16A]) + 100
    #print ''.join("{:02x}".format(ord(c)) for c in mapups.eeprom[0x169:0x16C])
    print "H=", H
    print "L=", L
    """
    print "mapups.eeprom1="
    print ''.join("{:02x}".format(ord(c)) for c in mapups.eeprom1)
    print "mapups.eeprom2="
    print ''.join("{:02x}".format(ord(c)) for c in mapups.eeprom2)
    """
    print "mapups.eeprom="
    print ''.join("{:02x}".format(ord(c)) for c in mapups.eeprom)
else:
    print "Error read_eeprom()"


if mapups.read_data():
    #print "Fq net=", mapups.mdata._TFNET
    #print "type(mapups.mdata)=", type(MAPdata(mapups.mdata))
    print "mapups.mdata._TFNET=", mapups.mdata._TFNET
    print "mapups.mdata._ThFMAP=", mapups.mdata._ThFMAP
    print "mapups.mdata._PLoad=", mapups.mdata._PLoad
else:    
    print "Error read_data()"
