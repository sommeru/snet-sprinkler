#!./bin/python

import chirp_modbus
from time import sleep

address-old = 1
address-new = 2

sensor = chirp_modbus.SoilMoistureSensor(address=address-old, '/dev/ttyUSB0')

print("writing new address: " + str(address-new))
sensor.setAddress(address-new)

sleep(0.2)
print("reading address from holding register: ")
print(sensor.getAddress())
