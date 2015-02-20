#!/usr/bin/env python
"""Usage: main.py [options]
Options: 
 -?, --help           Prints this message and exits.
 -t, --test           Test mode: displays sensor data as (tx,rx) and exits
     --port=PORT      Sets serial port to PORT.  For windows this should be in 
                      the form COMnnn eg COM1 or COM123.  For nix/MacOS use the
                      path to the serial device eg /dev/cu.usbserial
     --setpoint=f.ff  Sets the OD set point to f.ff OD units.  eg 0.40
     --logfile=of.dat Sets the file used to wirte out log data.

Example: 
  Read sensor data to verify the device is working on COM5
main.py -t --port=COM5

  Run syphoning turbidostat on COM32 at 0.7 OD and write logs to history.dat
main.py --port=COM32 --setpoint=0.7 --logfile=history.dat
"""
from __future__ import print_function

import os
import pickle
import serial
import serial.tools.list_ports
import getopt, sys
from time import sleep, time
from math import log10

#########################################################
#BEGIN: Configuration variables
#vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
LOGFILE = 'log.dat'   #Name of log file
COMPORT = 'COM4'     #name of comport
SETPOINT = 0.4        #OD setpoint
#Gains: bigger kp means a faster controller but more 
# cycle-to-cycle variation in dilution volumes
# hint: keep kp/ki >15
kp = 300
ki = 8
DILUTE_PERIOD = 60    #how often to dilute in seconds
USE_CONTROLLER_PV = True
#^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#END: Configuration variables
#########################################################


class Chamber(object):
  def __init__(self,port_name):
    self._blankval = None

    self._init_serial(port_name)

  def _init_serial(self,p):
    try:
      self.spt = serial.Serial(port = p,baudrate=19200,timeout = 0.5)
      self.spt.setRTS(True) #close SPV1
    except:
      print("Problem opening serial port " + str(p))
      print("available serial ports are: ")
      for cp in serial.tools.list_ports.comports():
        print(cp[0])
      raise ValueError('invalid port')

  def _odbytes2tuple(self,odbytes):
    #correct endianness
    #TODO: replace this with struct.unpack("<ii",data)
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
    #read response
    b=self.spt.read(8)

    #open SPV on syphonstat board
    if USE_CONTROLLER_PV:
      self.spt.setRTS(False) #open PV1
      sleep(period*5.0/1000.0) #this is not very accurate.
      self.spt.setRTS(True) #close PV1

    if len(b)!=8:
      return None
    print(self._odbytes2tuple(b));
    return self._odbytes2tuple(b);

  def blank(self,blank_tuple=None):
    if blank_tuple==None:
      self._blankval = self.read_raw()
    else:
      self._blankval = blank_tuple
      
  def getblank(self):
    return self._blankval

  def read_OD(self):
    try:
      od = self.read_raw()
      signal = float(od[1])/float(od[0])
      blank = float(self._blankval[1])/float(self._blankval[0])
      return -log10(signal/blank)
    except ZeroDivisionError:
      print("WARNING! encountered division by zero.  Check" +
        "your hardware is plugged in and functioning correctly")
      return 1



if __name__ == '__main__':
  test_mode = False
  growth_test_mode = False
  #process commandline flags
  LOPTS = ["test","help","port=","setpoint=","logfile="]
  try:
    opts, args = getopt.getopt(sys.argv[1:], "tg?", LOPTS)
  except getopt.GetoptError as err:
    print(str(err))
    print("\n"+__doc__)
    sys.exit(0)
  for o,a in opts:
    if o in ("-t","--test"):
      test_mode = True
    if o in ("-?","--help"):
      print(__doc__)
      sys.exit(0)
    if o == "--port":
      COMPORT = a
    if o == "--setpoint":
      try:
        SETPOINT = float(a)
      except ValueError as err:
        print("bad argument --setpoint:")
        print(str(err))
    if o == "--logfile":
      LOGFILE = a
    if o == "-g":
      growth_test_mode = True
      print("GT mode on.")

    
  c = Chamber(COMPORT)
  if test_mode:
    print("test mode:")
    print (c.read_raw())
    sys.exit(0)
  
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
  growth_test = 0
  while True:
    OD = c.read_OD()
    #if in growth test mode dilute to setpoint -0.1 then grow to setpoint
    if growth_test_mode and time()%(8.0*60*60)<(2*60):
      growth_test = -1
    if growth_test<0:  #dilute down
      u = 255
      if OD<SETPOINT-0.1:
        growth_test=1 #go into grow mode
    elif growth_test>0:
      u=0
      if OD>SETPOINT:
        growth_test=0
    else: #normal operation
      err = OD-SETPOINT
      z = z+ki*err
      z = min(max(0.0,z),255.0) #saturate 0.0-255.0
      u = int(round(z+err*kp))
      u = min(max(0,u),255) #saturate 0-255
      try:
        with open("state.dat",'w') as f:
          pickle.dump({'z': z,'blank':c.getblank()},f)
      except KeyboardInterrupt as e:
        with open("state.dat",'w') as f:
          pickle.dump({'z': z,'blank':c.getblank()},f)
        raise e

    logline = '{' + '"time":{:d}, "OD":{:.4f}, "Z":{:.4f}, "U":{:d}'.format(int(time()),OD,z,u) +'}'
    c.dilute(u)

    print(logline)
    print(logline,file=lf)
    #force the file to get written!
    lf.flush()
    os.fsync(lf.fileno())
    sleep(DILUTE_PERIOD)


