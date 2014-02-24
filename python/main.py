#!/usr/bin/env python
from __future__ import print_function

import os
import pickle
import serial
import serial.tools.list_ports
from time import sleep, time
from math import log10

#some config constants
LOGFILE = 'log.dat'
COMPORT = 'COM19'
SETPOINT = 0.4
kp = 150
ki = 8
DILUTE_PERIOD = 60

class Chamber(object):
  def __init__(self,port_name):
    self._blankval = None

    self._init_serial(port_name)

  def _init_serial(self,p):
    try:
      self.spt = serial.Serial(port = p,baudrate=19200,timeout = 0.5)
    except:
      print("Problem opening serial port")
      print("available serial ports are: ")
      for cp in serial.tools.list_ports.comports():
        print(cp[0])
      raise ValueError('invalid port')

  def _odbytes2tuple(self,odbytes):
    #correct endianness
    txbytes = odbytes[3::-1]  #first 4bytes
    rxbytes = odbytes[7:3:-1] #next 4bytes
    tx=int(txbytes.encode('hex'),16)
    rx=int(rxbytes.encode('hex'),16)
    return (tx,rx)

  def read_raw(self):
    """
      Read the raw (tx,rx) numbers from chamber.

      This function requests tx,rx data from the chamber and decodes it into
      python int type.

      Returns (tx,rx) tuple.
      Returns None on serial timeout.
    """
    return self.dilute(0)

  def dilute(self,period):
    """
      Dilute chamber.

      period: uint8_t proportional to dilution volume.
      as of right now period = 255 should open the dilution valve for 10 seconds

      returns the current raw read value.
    """

    if period > 255:
      period = 255
    if period < 0:
      return
    period = int(round(period))
    self.spt.write(bytearray([period]))
    b=self.spt.read(8)
    if len(b)!=8:
      return None
    return self._odbytes2tuple(b);

  def blank(self,blank_tuple=None):
    if blank_tuple==None:
      self._blankval = self.read_raw()
    else:
      self._blankval = blank_tuple
      
  def getblank(self):
    return self._blankval

  def read_OD(self):
    od = self.read_raw()
    signal = float(od[1])/float(od[0])
    blank = float(self._blankval[1])/float(self._blankval[0])
    return -log10(signal/blank)


if __name__ == '__main__':
    
    c = Chamber(COMPORT)
    try:
      with open("state.dat") as f:
        temp = pickle.load(f)
      c.blank(temp['blank'])
      z = temp['z']
    except IOError:
      c.blank()
      z=0
      
    lf = open(LOGFILE,'a')
    sleep(5)
    while True:
      OD = c.read_OD()
      err = OD-SETPOINT
      z = z+ki*err
      z = min(max(0.0,z),255.0) #saturate 0.0-255.0
      u = int(round(z+err*kp))
      with open("state.dat",'w') as f:
        pickle.dump({'z': z,'blank':c.getblank()})

      logline = '{' + '"time":{:d}, "OD":{:.4f}, "Z":{:.4f}, "U":{:d}'.format(int(time()),OD,z,u) +'}'
      c.dilute(u)

      print(logline)
      print(logline,file=lf)
      #force the file to get written!
      lf.flush()
      os.fsync(lf.fileno())
      sleep(DILUTE_PERIOD)
