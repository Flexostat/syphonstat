import time
import json

with open("log.dat",'rb') as datfile, open("log.csv",'wb') as csvfile:
  csvfile.write("Time, OD\n")
  for line in datfile:
    dat = json.loads(line)
    od = dat["OD"]
    et = dat["time"]
    tob = time.gmtime(et)

    ll = str(time.strftime('%m/%d/%Y %H:%M:%S',tob) ) +", " +str(od) + "\n"
    csvfile.write(ll)




