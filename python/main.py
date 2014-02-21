#!/usr/bin/env python
from __future__ import print_function

import serial
import serial.tools.list_ports
from time import sleep
from math import log10


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

  def blank(self):
    self._blankval = self.read_raw()
  
  def read_OD(self):
    od = self.read_raw()
    signal = float(od[1])/float(od[0])
    blank = float(self._blankval[1])/float(self._blankval[0])
    return -log10(signal/blank)
    

if __name__ == '__main__':
    c = Chamber('COM19')
    c.blank()
    while True:
      sleep(5)
      OD = c.read_OD()
      print("%0.4f" % OD)
      c.dilute(15)
      