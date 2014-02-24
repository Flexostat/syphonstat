import matplotlib.pyplot as plt
import json

logf = open('log.dat')

t = []
od = []

for line in logf:
  try:
    temp = json.loads(line)
    t.append(temp["time"])
    od.append(temp["OD"])
  except:
    print("badline")

tt = map(lambda x: (float(x)-t[0])/60/60,t)

plt.plot(tt, od)
plt.title("Simple Plot")
plt.show()
