#!./bin/python

virtualmode = True

import time  # for waiting in the code
import sys  # for exiting the code if an error occurs
import paho.mqtt.client as mqtt #for processing mqtt messages
import csv

if virtualmode == False:
	print ("Setting up GPIO pins...")
	print ("Setting up RS485 connections...")
elif virtualmode == True:
    import chirp_modbus
    line-1-sensor = chirp_modbus.SoilMoistureSensor(address=1, serialport='/dev/ttyUSB0')
try:
	line-1-sensor.getMoisture()
    line-1-sensor.getTemperature()
except (IOError, ValueError):
    print("Error reading sensor data...")

mqttclient = mqtt.Client("snet-sprinkler")
todolist_time = dict()


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
    try:
        with open('mqtt_credentials.csv', 'r') as f:
            reader = csv.reader(f)
            data = next(reader)  # Skip header line
            data = next(reader)
            mqtt_credentials_server = data[0]
            mqtt_credentials_user = data[1]
            mqtt_credentials_password = data[2]
            mqtt_credentials_port = int(data[3])
            mqtt_credentials_sslport = int(data[4])
            mqtt_credentials_websocketport = int(data[5])
        print("successfully imported MQTT credentials...")

    except:
        print("error opening mqtt_credentials.csv. Aborting...")
        sys.exit()

    mqttclient.username_pw_set(mqtt_credentials_user, password=mqtt_credentials_password)
    mqttclient.on_message=mqtt_message_recieved
    mqttclient.on_subscribe=mqttsubscribed
    mqttclient.on_connect=mqttconnected
    mqttclient.connect(mqtt_credentials_server, port=mqtt_credentials_port, keepalive=60, bind_address="")

    mqttclient.loop_start()
    mqttclient.subscribe("kirchenfelder75/snet-sprinkler/command/#")
    mqttclient.publish("kirchenfelder75/snet-sprinkler/debug","hello from snet-sprinkler")

def mqttsubscribed(client, userdata, mid, granted_qos):
    print ("successfully subscribed to MQTT topic with qos levels:", granted_qos)

def mqtt_message_recieved(client, userdata, message):
    mqtttopic=str(message.payload.decode("utf-8"))
    print("message received" ,mqtttopic, "/ message topic =",message.topic, "/ message qos =", message.qos, "/ message retain flag =", message.retain)
    taskmsg = message.topic.split("command/")[1]
    if (taskmsg == "line-1"  or taskmsg == "line-2" or taskmsg == "line-3"):
        channel = taskmsg
        try:
            latchingtime = int(mqtttopic)
        except:
            latchingtime = 5000
        switch_channel(channel,"ON")
        todolist_time[channel] = [int(round(time.time() * 1000)), latchingtime, 0]

def switch_channel(channel,state):

    if (channel=="line-1"):
        if (virtualmode == True):
            print("Setting channel", "1", "to", state)
    if (channel=="line-2"):
        if (virtualmode == True):
            print("Setting channel", "2", "to", state)
    if (channel=="line-3"):
        if (virtualmode == True):
            print("Setting channel", "3", "to", state)


def checktodolist_time():
    poplist = set()
    for todolistitem in todolist_time:
        if (int(round(time.time() * 1000)) - (todolist_time[todolistitem][0]) > (todolist_time[todolistitem][1]) ):

            switch_channel(todolistitem,"OFF")
            poplist.add(todolistitem)
    for popitem in poplist:
        todolist_time.pop(popitem)

mqtt_connect()

# the main loop
while True:
    checktodolist_time()
    time.sleep(1)
