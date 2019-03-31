#!/usr/bin/env python3

import chirp_modbus
from time import sleep

address_old = 1
address_new = 3

sensor = chirp_modbus.SoilMoistureSensor(address=address_old, serialport='/dev/ttyUSB0')

#print("writing new address: " + str(address_new))
#sensor.setAddress(address_new)

sleep(0.2)
print("reading address from holding register: ")
print(sensor.getAddress())
