#!/usr/bin/env python
# -*- coding:utf8 -*-

import serial
from ctypes import *
from time import sleep
from datetime import datetime
import pymysql.cursors


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
    def __repr__(self):
       loc_tfnet = "division by zero" if (0 == self._TFNET) else str(6250/self._TFNET)
       loc_thfmap = "division by zero" if (0 == self._ThFMAP) else str(6250/self._ThFMAP)
       return """<MAPdata: 
_MODE = %d
_Status_Char = %d
_Uacc = %f
_Iacc = %d
_PLoad = %d
_F_Acc_Over = %d
_F_Net_Over = %d
_UNET = %d
_INET = %d
_PNET = %d
_TFNET = %s
_ThFMAP = %s
_UOUTmed = %d
_TFNET_Limit = %d
_UNET_Limit = %d
_RSErrSis = %d
_RSErrJobM = %d
_RSErrJob = %d
_RSWarning = %d
_Temp_Grad0 = %d
_Temp_Grad2 = %d
_INET_16_4 = %f
_IAcc_med_A_u16 = %f
_Temp_off = %d
_E_NET = %f
_E_ACC = %f
_E_ACC_CHARGE = %f
_Uacc_optim = %f
_I_acc_avg = %f
_I_mppt_avg = %f
_I2C_err = %d
>""" % (self._MODE
, self._Status_Char
, self._Uacc
, self._Iacc
, self._PLoad
, self._F_Acc_Over
, self._F_Net_Over
, self._UNET
, self._INET
, self._PNET
#, 6250/self._TFNET
#, 6250/self._ThFMAP
, loc_tfnet
, loc_thfmap
, self._UOUTmed
, self._TFNET_Limit
, self._UNET_Limit
, self._RSErrSis
, self._RSErrJobM
, self._RSErrJob
, self._RSWarning
, self._Temp_Grad0
, self._Temp_Grad2
, self._INET_16_4
, self._IAcc_med_A_u16
, self._Temp_off
, self._E_NET
, self._E_ACC
, self._E_ACC_CHARGE
, self._Uacc_optim
, self._I_acc_avg
, self._I_mppt_avg
, self._I2C_err
        )

class MAP:
    eeprom = ''
    fd = -1
    t_start = 0
    t_fin = 0
    Vhigh = 0
    Vlow = 0
    buf_p = None
    mdata = MAPdata()
    mdata1 = MAPdata()
    #mdata._Status_Char = 0
    #mdata._TFNET = 0
    buf = create_string_buffer(size_of_buffer)
    def __init__(self, port_name, baudrate, timeout):
        self.port = serial.Serial(port_name, baudrate=baudrate, timeout=timeout)
        self.fd = self.port.fileno()
    def open_db(self, host, user, password, db):
        self.dbhost = host
        self.dbuser = user
        self.dbpw = password
        self.db = db
        self.connection = pymysql.connect(host = self.dbhost,
                                     user = self.dbuser,
                                     password = self.dbpw,
                                     db = self.db,
                                     charset='utf8',
                                     cursorclass=pymysql.cursors.DictCursor)
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
            #self.buf_p = pointer(self.buf)
            #self.mdata_p = cast(self.buf_p, POINTER(MAPdata))
            #self.mdata1 = copy.copy(mapups.mdata_p.contents)
            #self.mdata1._MODE = mapups.mdata_p.contents._MODE
            self.mdata._MODE = c_ubyte(ord(self.buf[0x400 - 0x3FF]))
            self.mdata._Status_Char = c_ubyte(ord(self.buf[0x402 - 0x3FF]))
            self.mdata._Uacc = ord(self.buf[0x405 - 0x3FF])*256 + ord(self.buf[0x406 - 0x3FF])
            self.mdata._Uacc /= 10
            self.mdata._PLoad = c_uint(ord(self.buf[0x409 - 0x3FF]) * 100)
            self.mdata._F_Acc_Over = c_ubyte(ord(self.buf[0x41C - 0x3FF]))
            self.mdata._F_Net_Over = c_ubyte(ord(self.buf[0x41D - 0x3FF]))
            self.mdata._UNET = c_uint(ord(self.buf[0x422 - 0x3FF]) + 100)
            self.mdata._INET = c_ubyte(ord(self.buf[0x423 - 0x3FF]))
            self.mdata._PNET = c_uint(ord(self.buf[0x424 - 0x3FF]) * 100)
            # self.mdata._TFNET = c_ubyte(6250/ord(self.buf[0x425 - 0x3FF]))
            # self.mdata._ThFMAP = c_ubyte(6250/ord(self.buf[0x426 - 0x3FF]))
            self.mdata._TFNET = c_ubyte(ord(self.buf[0x425 - 0x3FF]))
            self.mdata._ThFMAP = c_ubyte(ord(self.buf[0x426 - 0x3FF]))
            self.mdata._UOUTmed = c_uint(ord(self.buf[0x427 - 0x3FF]))
            if self.mdata._UOUTmed > 0:
                self.mdata._UOUTmed += 100
            self.mdata._TFNET_Limit = c_ubyte(ord(self.buf[0x428 - 0x3FF]))
            if self.mdata._TFNET_Limit != 0:
                self.mdata._TFNET_Limit = 2500/self.mdata._TFNET_Limit
            self.mdata._UNET_Limit = c_uint(ord(self.buf[0x429 - 0x3FF]) + 100)
            self.mdata._RSErrSis = c_ubyte(ord(self.buf[0x42A - 0x3FF]))
            self.mdata._RSErrJobM = c_ubyte(ord(self.buf[0x42B - 0x3FF]))
            self.mdata._RSErrJob = c_ubyte(ord(self.buf[0x42C - 0x3FF]))
            self.mdata._RSWarning = c_ubyte(ord(self.buf[0x2E]))
            self.mdata._Temp_Grad0 = c_ubyte(ord(self.buf[0x2F]) - 50)
            self.mdata._Temp_Grad2 = c_ubyte(ord(self.buf[0x430 - 0x3FF]) - 50)
            if self.mdata._INET < 16:
                self.mdata._INET_16_4 = c_float(float(ord(self.buf[0x32])) / 16.0);
            else:
                self.mdata._INET_16_4 = c_float(float(ord(self.buf[0x32])) / 4.0);
            self.mdata._IAcc_med_A_u16 = c_float(float( ord(self.buf[0x34])*16 + ord(self.buf[0x35])) / 16.0);
            self.mdata._Temp_off = c_ubyte(ord(self.buf[0x43C - 0x3FF]))
            self.mdata._E_NET = c_ulong(ord(self.buf[0x50])*65536 + ord(self.buf[0x4F])*256 + ord(self.buf[0x4E]))
            self.mdata._E_ACC = c_ulong(ord(self.buf[0x53])*65536 + ord(self.buf[0x52])*256 + ord(self.buf[0x51]))
            self.mdata._E_ACC = c_ulong(ord(self.buf[0x53])*65536 + ord(self.buf[0x52])*256 + ord(self.buf[0x51]))
            self.mdata._E_ACC_CHARGE = c_ulong(ord(self.buf[0x56])*65536 + ord(self.buf[0x55])*256 + ord(self.buf[0x54]))
            self.mdata._I2C_err = c_ubyte(ord(self.buf[0x45A - 0x3FF]))
        else:            
            self.mdata = ''
            print "rc_read_data=", self.rc
            return False
        return True
    def save_data_to_db(self):
        self.mdict = {'date': datetime.now().date(), 'time': datetime.now().time()}
        self.mdict.update(dict(self.mdata._fields_))
        print "self.mdict=", self.mdict 
        with self.connection.cursor() as cursor:
            placeholders = ', '.join(['%s'] * len(self.mdict))
            columns = ', '.join(self.mdict.keys())
            sql = "INSERT INTO %s ( %s ) VALUES ( %s )" % ('data', columns, placeholders)
            # cursor.execute(sql, self.mdict.values())
            print "columns=", columns
            print "values=", self.mdict.values()


if __name__ == '__main__':
    mapups = MAP('/dev/ttyUSB0', baudrate=19200, timeout=5)
    print "MAP created"
    mapups.open_db('ct-mail', 'monitor', 'energy', 'upsmap')
    # print "port=", mapups.port
    # print "sizeof(mapups.mdata)=", sizeof(mapups.mdata)


    if mapups.read_eeprom():
        H = ord(mapups.eeprom[0x169]) + 100
        L = ord(mapups.eeprom[0x16A]) + 100
        print "H=", H
        print "L=", L
        #print "mapups.eeprom="
        #print ''.join("{:02x}".format(ord(c)) for c in mapups.eeprom)
    else:
        print "Error read_eeprom()"


    if mapups.read_data():
        print "mapups.mdata=", repr(mapups.mdata)
        print "type(_fields_)=", type(mapups.mdata._fields_)
        print "type(_fields_[0])=", type(mapups.mdata._fields_[0])
        print "len(_fields_)=", len(mapups.mdata._fields_)
        mapups.save_data_to_db()
    else:    
        print "Error read_data()"
