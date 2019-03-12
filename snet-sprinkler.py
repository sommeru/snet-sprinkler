#!./bin/python3

#command:
# line1.mode = auto, semi, manu
# line1.value = 1-999
# line1.active = ON,OFF
#status:
# line1.mode
# line1.value
# line1.active
# line1.temperature
# line1.moisture

line1_mode = "manu"
line2_mode = "manu"
line3_mode = "manu"

line1_manu_irrigationtime = 5
line2_manu_irrigationtime = 5
line3_manu_irrigationtime = 5

line1_semi_irrigationtime = 5
line2_semi_irrigationtime = 5
line3_semi_irrigationtime = 5

line1_auto_sensitivity = 500
line2_auto_sensitivity = 500
line3_auto_sensitivity = 500

line1_humidity = 0
line2_humidity = 0
line3_humidity = 0

line1_temperature = 0.0
line2_temperature = 0.0
line3_temperature = 0.0


import schedule # for running cron like tasks (schedule.readthedocs.io)
import time  # for waiting in the code
import sys  # for exiting the code if an error occurs
import paho.mqtt.client as mqtt #for processing mqtt messages
import csv # for importing the mqtt credentials
import configparser #for reading the configuration file
import chirp_modbus #for interfacing with the chirp moisture sensors
import random #for generating arbitrary numbers in sim mode

config = configparser.ConfigParser()
config.read('snet-sprinkler.conf')

mqttpublishstatus = config['MQTT Settings']['domain'] + "/" + config['MQTT Settings']['hostname'] + "/status"
mqttpublishdebug = config['MQTT Settings']['domain'] + "/" + config['MQTT Settings']['hostname'] + "/debug"

if ('address_sensor_1' in config['RS485 Soil Moisture Sensors']):
    sensor_line1 = chirp_modbus.SoilMoistureSensor(address=config['RS485 Soil Moisture Sensors'].getint('address_sensor_1'), serialport=config['RS485 Soil Moisture Sensors']['port'])
if ('address_sensor_2' in config['RS485 Soil Moisture Sensors']):
    sensor_line2 = chirp_modbus.SoilMoistureSensor(address=config['RS485 Soil Moisture Sensors'].getint('address_sensor_2'), serialport=config['RS485 Soil Moisture Sensors']['port'])
if ('address_sensor_3' in config['RS485 Soil Moisture Sensors']):
    sensor_line3 = chirp_modbus.SoilMoistureSensor(address=config['RS485 Soil Moisture Sensors'].getint('address_sensor_3'), serialport=config['RS485 Soil Moisture Sensors']['port'])

if (config['Simulation Mode'].getboolean('sim_relay_board') == False):
    print ("Setting up GPIO pins...")
else:
    print ("Entering GPIO simulation mode...")

mqttclient = mqtt.Client("snet-sprinkler")
todolist_time = dict()






def read_moisture_sensors():
    global line1_humidity
    global line2_humidity
    global line3_humidity
    global line1_temperature
    global line2_temperature
    global line3_temperature

    if ('address_sensor_1' in config['RS485 Soil Moisture Sensors']):
        if (config['Simulation Mode'].getboolean('sim_moisture_sensors') == False):
            print("Reading sensor_line1..." )
            try:
                line1_act_humidity = sensor_line1.getMoisture()
                line1_act_temperature = sensor_line1.getTemperature()
                print("Moisture line1 =", line1_act_humidity, " Temperature line1 =", line1_act_temperature)
            except (IOError, ValueError):
                print("Error reading sensor_line1")
        else:
            print("Pretending to read sensor_line1...")
            line1_act_humidity = random.randrange(200, 300, 1)
            line1_act_temperature = random.randrange(200, 250, 1) / 10
        if ('line1_act_humidity' in locals()):
            if (abs(line1_act_humidity - line1_humidity) > config['RS485 Soil Moisture Sensors'].getint('sensor_threshold_moisture')):
                line1_humidity = line1_act_humidity
                mqttpublishstring = mqttpublishstatus + "/" + "line1" + "/" + "moisture"
                mqttclient.publish(mqttpublishstring,line1_humidity)
        if ('line1_act_temperature' in locals()):
            if (abs(line1_act_temperature - line1_temperature) > config['RS485 Soil Moisture Sensors'].getfloat('sensor_threshold_temperature')):
                line1_temperature = line1_act_temperature
                mqttpublishstring = mqttpublishstatus + "/" + "line1" + "/" + "temperature"
                mqttclient.publish(mqttpublishstring,line1_temperature)

    if ('address_sensor_2' in config['RS485 Soil Moisture Sensors']):
        if (config['Simulation Mode'].getboolean('sim_moisture_sensors') == False):
            print("Reading sensor_line2..." )
            try:
                line2_act_humidity = sensor_line2.getMoisture()
                line2_act_temperature = sensor_line2.getTemperature()
                print("Moisture line2 =", line2_act_humidity, " Temperature line2 =", line2_act_temperature)
            except (IOError, ValueError):
                print("Error reading sensor_line2")
        else:
            print("Pretending to read sensor_line2...")
            line2_act_humidity = random.randrange(200, 300, 1)
            line2_act_temperature = random.randrange(200, 250, 1) / 10
        if ('line2_act_humidity' in locals()):
            if (abs(line2_act_humidity - line2_humidity) > config['RS485 Soil Moisture Sensors'].getint('sensor_threshold_moisture')):
                line2_humidity = line2_act_humidity
                mqttpublishstring = mqttpublishstatus + "/" + "line2" + "/" + "moisture"
                mqttclient.publish(mqttpublishstring,line2_humidity)
        if ('line2_act_temperature' in locals()):
            if (abs(line2_act_temperature - line2_temperature) > config['RS485 Soil Moisture Sensors'].getfloat('sensor_threshold_temperature')):
                line2_temperature = line2_act_temperature
                mqttpublishstring = mqttpublishstatus + "/" + "line2" + "/" + "temperature"
                mqttclient.publish(mqttpublishstring,line2_temperature)

    if ('address_sensor_3' in config['RS485 Soil Moisture Sensors']):
        if (config['Simulation Mode'].getboolean('sim_moisture_sensors') == False):
            print("Reading sensor_line3..." )
            try:
                line3_act_humidity = sensor_line3.getMoisture()
                line3_act_temperature = sensor_line3.getTemperature()
                print("Moisture line3 =", line3_act_humidity, " Temperature line3 =", line3_act_temperature)
            except (IOError, ValueError):
                print("Error reading sensor_line3")
        else:
            print("Pretending to read sensor_line3...")
            line3_act_humidity = random.randrange(200, 300, 1)
            line3_act_temperature = random.randrange(200, 250, 1) / 10
        if ('line3_act_humidity' in locals()):
            if (abs(line3_act_humidity - line3_humidity) > config['RS485 Soil Moisture Sensors'].getint('sensor_threshold_moisture')):
                line3_humidity = line3_act_humidity
                mqttpublishstring = mqttpublishstatus + "/" + "line3" + "/" + "moisture"
                mqttclient.publish(mqttpublishstring,line3_humidity)
        if ('line3_act_temperature' in locals()):
            if (abs(line3_act_temperature - line3_temperature) > config['RS485 Soil Moisture Sensors'].getfloat('sensor_threshold_temperature')):
                line3_temperature = line3_act_temperature
                mqttpublishstring = mqttpublishstatus + "/" + "line3" + "/" + "temperature"
                mqttclient.publish(mqttpublishstring,line3_temperature)


def mqttconnected(client, userdata, flags, rc):
    if rc==0:
        print("successfully connected to MQTT broker. Returned code =",rc)
    else:
        print("Bad connection to MQTT broker. Returned code =",rc)
        mqtterrorcode = {
            1: "Connection refused – incorrect protocol version",
            2: "Connection refused – invalid client identifier",
            3: "Connection refused – server unavailable",
            4: "Connection refused – bad username or password",
            5: "Connection refused – not authorised"
        }
        print (mqtterrorcode.get(rc, "Error code unknown..."))

def mqtt_connect():

    mqttclient.username_pw_set(config['MQTT Credentials']['user'], password=config['MQTT Credentials']['password'])
    mqttclient.on_message=mqtt_message_recieved
    mqttclient.on_subscribe=mqttsubscribed
    mqttclient.on_connect=mqttconnected
    mqttclient.connect(config['MQTT Credentials']['server'], port=int(config['MQTT Credentials']['port']), keepalive=60, bind_address="")

    mqttclient.loop_start()
    mqttsubscribe = config['MQTT Settings']['domain'] + "/" + config['MQTT Settings']['hostname'] + "/command/#"
    mqttclient.subscribe(mqttsubscribe)
    mqttclient.publish(mqttpublishdebug,"hello from snet-sprinkler")

def mqttsubscribed(client, userdata, mid, granted_qos):
    print ("successfully subscribed to MQTT topic with qos levels:", granted_qos)

def mqtt_message_recieved(client, userdata, message):
    mqtttopic=str(message.payload.decode("utf-8"))
    print("message received" ,mqtttopic, "/ message topic =",message.topic, "/ message qos =", message.qos, "/ message retain flag =", message.retain)
    topicmsg = message.topic.split("command/")[1]
    channel = topicmsg.split("/")[0]
    channelsetting= topicmsg.split("/")[1]

    if (channel == "line1"  or channel == "line2" or channel == "line3"):
        processchannelsettings(channel,channelsetting, mqtttopic)

def processchannelsettings(channel, channelsetting, value):

    global line1_mode
    global line2_mode
    global line3_mode

    global line1_manu_irrigationtime
    global line2_manu_irrigationtime
    global line3_manu_irrigationtime

    global line1_semi_irrigationtime
    global line2_semi_irrigationtime
    global line3_semi_irrigationtime

    global line1_auto_sensitivity
    global line2_auto_sensitivity
    global line3_auto_sensitivity

    if (channelsetting == "mode"):
        if (channel == "line1"):
            print("changing mode of line1 to", value)


            line1_mode = value
        elif (channel == "line2"):
            line2_mode = value
            print("changing mode of line2 to", value)
        elif (channel == "line3"):
            line3_mode = value
            print("changing mode of line3 to", value)
    elif (channelsetting == "value"):
        if (channel == "line1"):
            if (line1_mode == "manu"):
                print("Setting line1_manu_irrigationtime to", value)
                line1_manu_irrigationtime = int(value)
            elif (line1_mode == "semi"):
                print("Setting line1_semi_irrigationtime to", value)
                line1_semi_irrigationtime = int(value)
            elif (line1_mode == "auto"):
                print("Setting line1_auto_sensitivity to", value)
                line1_auto_sensitivity = int(value)
        elif (channel == "line2"):
            if (line1_mode == "manu"):
                print("Setting line2_manu_irrigationtime to", value)
                line2_manu_irrigationtime = int(value)
            elif (line2_mode == "semi"):
                print("Setting line2_semi_irrigationtime to", value)
                line2_semi_irrigationtime = int(value)
            elif (line2_mode == "auto"):
                print("Setting line2_auto_sensitivity to", value)
                line2_auto_sensitivity = int(value)
        elif (channel == "line3"):
            if (line1_mode == "manu"):
                print("Setting line3_manu_irrigationtime to", value)
                line3_manu_irrigationtime = int(value)
            elif (line3_mode == "semi"):
                print("Setting line3_semi_irrigationtime to", value)
                line3_semi_irrigationtime = int(value)
            elif (line3_mode == "auto"):
                print("Setting line3_auto_sensitivity to", value)
                line3_auto_sensitivity = int(value)

    elif (channelsetting == "active"):
        if (channel == "line1"):
            if (line1_mode == "manu"):
                if (value == "ON"):
                    switch_channel(channel,"ON")
                    todolist_time[channel] = [int(round(time.time() * 1000)), line1_manu_irrigationtime*1000, "OFF"]
                elif (value == "OFF"):
                    switch_channel(channel,"OFF")
                    removetodolist_time(channel)
    update_mqtt_status(channel)

def update_mqtt_status(channel):
    mqttpublishstring = mqttpublishstatus + "/" + channel + "/" + "mode"
    if (channel == "line1"):
        value = line1_mode
    elif (channel == "line2"):
        value = line2_mode
    elif (channel == "line3"):
        value = line3_mode
    mqttclient.publish(mqttpublishstring,value)

    mqttpublishstring = mqttpublishstatus + "/" + channel + "/" + "value"
    if (channel == "line1"):
        if (line1_mode == "manu"):
            value = line1_manu_irrigationtime
        elif (line1_mode == "semi"):
            value = line1_semi_irrigationtime
        elif (line1_mode == "auto"):
            value = line1_auto_sensitivity
    if (channel == "line2"):
        if (line2_mode == "manu"):
            value = line2_manu_irrigationtime
        elif (line2_mode == "semi"):
            value = line2_semi_irrigationtime
        elif (line2_mode == "auto"):
            value = line2_auto_sensitivity
    if (channel == "line3"):
        if (line3_mode == "manu"):
            value = line3_manu_irrigationtime
        elif (line3_mode == "semi"):
            value = line3_semi_irrigationtime
        elif (line3_mode == "auto"):
            value = line3_auto_sensitivity
    mqttclient.publish(mqttpublishstring,value)


def switch_channel(channel,state):
    if (virtualmode == True):
        print("Pretending to set channel",channel,"to",state)
    elif (virtualmode == False):
        if (channel=="line1"):
            print("Setting channel", "1", "to", state)
        if (channel=="line2"):
            print("Setting channel", "2", "to", state)
        if (channel=="line3"):
            print("Setting channel", "3", "to", state)

    mqttpublishstring = mqttpublishstatus + "/" + channel + "/" + "active"
    mqttclient.publish(mqttpublishstring,state)

def removetodolist_time(channel):
    poplist = set()
    for todolistitem in todolist_time:
        if (todolistitem == channel):
            poplist.add(todolistitem)
    for popitem in poplist:
        todolist_time.pop(popitem)

def checktodolist_time():
    poplist = set()
    for todolistitem in todolist_time:
        if (int(round(time.time() * 1000)) - (todolist_time[todolistitem][0]) > (todolist_time[todolistitem][1]) ):
            switch_channel(todolistitem, todolist_time[todolistitem][2])
            poplist.add(todolistitem)
    for popitem in poplist:
        todolist_time.pop(popitem)

mqtt_connect()

def job():
    if (line1_mode == "auto"):
        print ("automatic mode not implemented yet...")
    elif (line1_mode == "semi-auto"):
        print ("Starting irrigation of line1 for", line1_irrigation_time, "s")
        switch_channel("line1","ON")
        todolist_time[channel] = [int(round(time.time() * 1000)), line1_irrigation_time*1000, "OFF"]




schedule.every(5).seconds.do(read_moisture_sensors)
#schedule.every().minute.at(":00").do(irrigationjob)
#schedule.every().hour.do(job)
#schedule.every().day.at("10:30").do(job)
#schedule.every(5).to(10).minutes.do(job)
#schedule.every().monday.do(job)
#schedule.every().wednesday.at("13:15").do(job)
#schedule.every().minute.at(":17").do(job)


# the main loop
while True:
    schedule.run_pending()
    checktodolist_time()
    time.sleep(1)
