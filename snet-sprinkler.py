#!/usr/bin/env python3

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

class Line:
    pass

class Buttons:
    pass

buttons = Buttons()
buttons.b1 = 0
buttons.b2 = 0
buttons.b3 = 0
buttons.b4 = 0

line1 = Line()
line2 = Line()
line3 = Line()
line4 = Line()

line1.name = "line1"
line2.name = "line2"
line3.name = "line3"

line1.humidity = 0
line2.humidity = 0
line3.humidity = 0

line1.temperature = 0.0
line2.temperature = 0.0
line3.temperature = 0.0

line1.valveopen = False
line2.valveopen = False
line3.valveopen = False

displaypage = 1


import schedule # for running cron like tasks (schedule.readthedocs.io)
import time  # for waiting in the code
import sys  # for exiting the code if an error occurs
import paho.mqtt.client as mqtt #for processing mqtt messages
import csv # for importing the mqtt credentials
import configparser #for reading the configuration file
import chirp_modbus #for interfacing with the chirp moisture sensors
import random #for generating arbitrary numbers in sim mode
import I2C_LCD_driver #for accessing the 2x16 display 
import os #for reading ip and ssid
import datetime #for displaying log messages

lcd = I2C_LCD_driver.lcd()

config = configparser.ConfigParser()
config.read('snet-sprinkler.conf')

def read_startup_values():
    global line1
    global line2
    global line3

    line1.autoirrigationtime = config['Auto Irrigation Settings'].getint('line1_irrigation_time')
    line2.autoirrigationtime = config['Auto Irrigation Settings'].getint('line2_irrigation_time')
    line3.autoirrigationtime = config['Auto Irrigation Settings'].getint('line3_irrigation_time')

    line1.mode = config['Line Settings']['line1_mode']
    line2.mode = config['Line Settings']['line2_mode']
    line3.mode = config['Line Settings']['line3_mode']

    line1.manu_irrigationtime = config['Line Settings'].getint('line1_manu_irrigationtime')
    line2.manu_irrigationtime = config['Line Settings'].getint('line2_manu_irrigationtime')
    line3.manu_irrigationtime = config['Line Settings'].getint('line3_manu_irrigationtime')

    line1.semi_irrigationtime = config['Line Settings'].getint('line1_semi_irrigationtime')
    line2.semi_irrigationtime = config['Line Settings'].getint('line2_semi_irrigationtime')
    line3.semi_irrigationtime = config['Line Settings'].getint('line3_semi_irrigationtime')

    line1.auto_sensitivity = config['Line Settings'].getint('line1_auto_sensitivity')
    line2.auto_sensitivity = config['Line Settings'].getint('line2_auto_sensitivity')
    line3.auto_sensitivity = config['Line Settings'].getint('line3_auto_sensitivity')

    line1.semiautoactive = config['Line Settings'].getboolean('line1_semiautoactive')
    line2.semiautoactive = config['Line Settings'].getboolean('line2_semiautoactive')
    line3.semiautoactive = config['Line Settings'].getboolean('line3_semiautoactive')

    line1.autoactive = config['Line Settings'].getboolean('line1_autoactive')
    line2.autoactive = config['Line Settings'].getboolean('line2_autoactive')
    line3.autoactive = config['Line Settings'].getboolean('line3_autoactive')

    update_mqtt_status("line1")
    update_mqtt_status("line2")
    update_mqtt_status("line3")

mqttpublishstatus = config['MQTT Settings']['domain'] + "/" + config['MQTT Settings']['hostname'] + "/status"
mqttpublishdebug = config['MQTT Settings']['domain'] + "/" + config['MQTT Settings']['hostname'] + "/debug"

line1.has_sensor = 'address_sensor_1' in config['RS485 Soil Moisture Sensors']
line2.has_sensor = 'address_sensor_2' in config['RS485 Soil Moisture Sensors']
line3.has_sensor = 'address_sensor_3' in config['RS485 Soil Moisture Sensors']

if (line1.has_sensor):
    line1.sensor = chirp_modbus.SoilMoistureSensor(address=config['RS485 Soil Moisture Sensors'].getint('address_sensor_1'), serialport=config['RS485 Soil Moisture Sensors']['port'])
    line1.humoffset = config['RS485 Soil Moisture Sensors'].getint('line1_humidity_offset')
    line1.tempoffset = config['RS485 Soil Moisture Sensors'].getfloat('line1_temperature_offset')
if (line2.has_sensor):
    line2.sensor = chirp_modbus.SoilMoistureSensor(address=config['RS485 Soil Moisture Sensors'].getint('address_sensor_2'), serialport=config['RS485 Soil Moisture Sensors']['port'])
    line2.humoffset = config['RS485 Soil Moisture Sensors'].getint('line2_humidity_offset')
    line2.tempoffset = config['RS485 Soil Moisture Sensors'].getfloat('line2_temperature_offset')
if (line3.has_sensor):
    line3.sensor = chirp_modbus.SoilMoistureSensor(address=config['RS485 Soil Moisture Sensors'].getint('address_sensor_3'), serialport=config['RS485 Soil Moisture Sensors']['port'])
    line3.humoffset = config['RS485 Soil Moisture Sensors'].getint('line3_humidity_offset')
    line3.tempoffset = config['RS485 Soil Moisture Sensors'].getfloat('line3_temperature_offset')

def log(message):
    logmessage = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ": " + message
    print (logmessage)
    #mqttpublishdebug(message)
    if (config['General'].getboolean('activate_file_logging')):
        with open("snet-sprinkler.log", "a") as logfile:
            logfile.write(logmessage + "\n")

if (config['Simulation Mode'].getboolean('sim_relay_board') == False):
    log ("Setting up GPIO pins...")
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    line1.relais_gpiopin=config['GPIO Settings'].getint('relais_line1')
    line2.relais_gpiopin=config['GPIO Settings'].getint('relais_line2')
    line3.relais_gpiopin=config['GPIO Settings'].getint('relais_line3')
    line4.relais_gpiopin=config['GPIO Settings'].getint('relais_line3')

    pushbutton1_gpiopin=config['GPIO Settings'].getint('pushbutton1_in')
    pushbutton2_gpiopin=config['GPIO Settings'].getint('pushbutton2_in')
    pushbutton3_gpiopin=config['GPIO Settings'].getint('pushbutton3_in')
    pushbutton4_gpiopin=config['GPIO Settings'].getint('pushbutton4_in')

    pushbutton1_led_gpiopin=config['GPIO Settings'].getint('pushbutton1_led')
    pushbutton2_led_gpiopin=config['GPIO Settings'].getint('pushbutton2_led')
    pushbutton3_led_gpiopin=config['GPIO Settings'].getint('pushbutton3_led')
    pushbutton4_led_gpiopin=config['GPIO Settings'].getint('pushbutton4_led')

    backlight_gpiopin=config['GPIO Settings'].getint('backlight')

    GPIO.setup(line1.relais_gpiopin, GPIO.OUT)
    GPIO.setup(line2.relais_gpiopin, GPIO.OUT)
    GPIO.setup(line3.relais_gpiopin, GPIO.OUT)
    GPIO.setup(line4.relais_gpiopin, GPIO.OUT)

    GPIO.setup(pushbutton1_led_gpiopin, GPIO.OUT)
    GPIO.setup(pushbutton2_led_gpiopin, GPIO.OUT)
    GPIO.setup(pushbutton3_led_gpiopin, GPIO.OUT)
    GPIO.setup(pushbutton4_led_gpiopin, GPIO.OUT)
    GPIO.setup(backlight_gpiopin, GPIO.OUT)

    GPIO.setup(pushbutton1_gpiopin, GPIO.IN)
    GPIO.setup(pushbutton1_gpiopin, GPIO.IN, pull_up_down = GPIO.PUD_UP)
    GPIO.setup(pushbutton2_gpiopin, GPIO.IN)
    GPIO.setup(pushbutton2_gpiopin, GPIO.IN, pull_up_down = GPIO.PUD_UP)
    GPIO.setup(pushbutton3_gpiopin, GPIO.IN)
    GPIO.setup(pushbutton3_gpiopin, GPIO.IN, pull_up_down = GPIO.PUD_UP)
    GPIO.setup(pushbutton4_gpiopin, GPIO.IN)
    GPIO.setup(pushbutton4_gpiopin, GPIO.IN, pull_up_down = GPIO.PUD_UP)


    GPIO.output(line1.relais_gpiopin, GPIO.HIGH)
    GPIO.output(line2.relais_gpiopin, GPIO.HIGH)
    GPIO.output(line3.relais_gpiopin, GPIO.HIGH)

    GPIO.output(backlight_gpiopin, GPIO.HIGH)
else:
    log ("Entering GPIO simulation mode...")

mqttclient = mqtt.Client("snet-sprinkler")
todolist_time = dict()



def read_moisture_sensors():
    global line1
    global line2
    global line3

    for line in (line1, line2, line3):
        if (line.has_sensor):
            line.act_humidity = -1
            line.act_temperature = -1
            if (config['Simulation Mode'].getboolean('sim_moisture_sensors') == False):
                #log("Reading " + line.name + ".sensor..." )
                try:
                    line.act_humidity = line.sensor.getMoisture() - line.humoffset
                    if (line.act_humidity < 0):
                        line.act_humidity = 0 # to avoid negative (dryer than dry) readings
                    line.act_temperature = line.sensor.getTemperature() - line.tempoffset
                    #log("Moisture " + line.name + " = " + str(line.act_humidity) + "Temperature "+ line.name + " = " + str(line.act_temperature))
                except IOError as e:
                    log("Error reading " + line.name + ".sensor with error" + str(e))
                except ValueError as e:
                    log("Error reading " + line.name + ".sensor with error" + str(e))
            else:
                log("Pretending to read " + line.name + ".sensor...")
                line.act_humidity = random.randrange(200, 300, 1)
                line.act_temperature = random.randrange(200, 250, 1) / 10
            if (line.act_humidity != -1):
                if (abs(line.act_humidity - line.humidity) > config['RS485 Soil Moisture Sensors'].getint('sensor_threshold_moisture') or line.act_humidity == 0):
                    line.humidity = line.act_humidity
                    mqttpublishstring = mqttpublishstatus + "/" + ""+line.name+"" + "/" + "moisture"
                    mqttclient.publish(mqttpublishstring,line.humidity)
                    if (line.name == "line1"):
                        line1.humidity = line.humidity
                    if (line.name == "line2"):
                        line2.humidity = line.humidity
                    if (line.name == "line3"):
                        line3.humidity = line.humidity
            if (line.act_temperature != -1):
                if (abs(line.act_temperature - line.temperature) > config['RS485 Soil Moisture Sensors'].getfloat('sensor_threshold_temperature')):
                    line.temperature = line.act_temperature
                    mqttpublishstring = mqttpublishstatus + "/" + ""+line.name+"" + "/" + "temperature"
                    mqttclient.publish(mqttpublishstring,line.temperature)




def mqttconnected(client, userdata, flags, rc):
    if rc==0:
        log("successfully connected to MQTT broker. Returned code = " + str(rc))
    else:
        log("Bad connection to MQTT broker. Returned code = " + str(rc))
        mqtterrorcode = {
            1: "Connection refused - incorrect protocol version",
            2: "Connection refused - invalid client identifier",
            3: "Connection refused - server unavailable",
            4: "Connection refused - bad username or password",
            5: "Connection refused - not authorised"
        }
        log (mqtterrorcode.get(rc, "Error code unknown..."))

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
    log ("successfully subscribed to MQTT topic with qos levels:" + granted_qos)

def mqtt_message_recieved(client, userdata, message):
    mqtttopic=str(message.payload.decode("utf-8"))
    #log("message received "  + str(mqtttopic) + " / message topic = " + str(message.topic) + " / message qos = " + str(message.qos) + " / message retain flag = " + str(message.retain))
    topicmsg = message.topic.split("command/")[1]
    channel = topicmsg.split("/")[0]
    channelsetting= topicmsg.split("/")[1]

    if (channel == "line1"  or channel == "line2" or channel == "line3"):
        processchannelsettings(channel,channelsetting, mqtttopic)

def processchannelsettings(channel, channelsetting, value):

    global line1
    global line2
    global line3

    if (channel == "line1"):
        line = line1
    if (channel == "line2"):
        line = line2
    if (channel == "line3"):
        line = line3

    if (channelsetting == "mode"):
        config['Line Settings'][line.name + '_mode'] = value
        log("changing mode of "+line.name+" to " + value)
        line.mode = value
    elif (channelsetting == "value"):
        if (line.mode == "manu"):
            config['Line Settings'][line.name + '_manu_irrigationtime'] = value
            log("Setting "+ line.name + ".manu_irrigationtime to " + value)
            line.manu_irrigationtime = int(value)
        elif (line.mode == "semi-auto"):
            config['Line Settings'][line.name + '_semi_irrigationtime'] = value
            log("Setting " + line.name + ".semi_irrigationtime to " + value)
            line.semi_irrigationtime = int(value)
        elif (line.mode == "auto"):
            config['Line Settings'][line.name + '_auto_sensitivity'] = value
            log("Setting " + line.name + ".auto_sensitivity to " + value)
            line.auto_sensitivity = int(value)
    elif (channelsetting == "active"):
        if (line.mode == "manu"):
            if (value == "ON"):
                switch_channel(channel,"ON")
                todolist_time[channel] = [int(round(time.time() * 1000)), line.manu_irrigationtime*1000, "OFF"]
            elif (value == "OFF"):
                switch_channel(channel,"OFF")
                removetodolist_time(channel)
        elif (line.mode == "semi-auto"):
            config['Line Settings'][line.name + '_semiautoactive'] = value
            log("Setting " + line.name + ".semiautoactive to " + value)
            if (value == "ON"):
                line.semiautoactive = True
            elif (value == "OFF"):
                line.semiautoactive = False
        elif (line.mode == "auto"):
            config['Line Settings'][line.name + '_autoactive'] = value
            log("Setting " + line.name + ".autoactive to " + value)
            if (value == "ON"):
                line.autoactive = True
            elif (value == "OFF"):
                line.autoactive = False

    update_mqtt_status(channel)
    with open('snet-sprinkler.conf', 'w') as configfile:
        config.write(configfile)

def update_mqtt_status(channel):
    global line1
    global line2
    global line3

    mqttpublishstring = mqttpublishstatus + "/" + channel + "/" + "mode"
    if (channel == "line1"):
        line = line1
    elif (channel == "line2"):
        line = line2
    elif (channel == "line3"):
        line = line3

    if (line.mode == "manu"):
        value = 0
    elif (line.mode == "semi-auto"):
        value = 1
    elif (line.mode == "auto"):
        value = 2

    mqttclient.publish(mqttpublishstring,value)

    mqttpublishstring = mqttpublishstatus + "/" + channel + "/" + "value"
    if (line.mode == "manu"):
        value = line.manu_irrigationtime
    elif (line.mode == "semi-auto"):
        value = line.semi_irrigationtime
    elif (line.mode == "auto"):
        value = line.auto_sensitivity
    mqttclient.publish(mqttpublishstring,value)

    mqttpublishstring = mqttpublishstatus + "/" + channel + "/" + "active"
    if (line.mode == "manu"):
        if (line.valveopen):
            value = "ON"
        else:
            value = "OFF"
    elif (line.mode == "semi-auto"):
        if (line.semiautoactive):
            value = "ON"
        else:
            value = "OFF"
    elif (line.mode == "auto"):
        if (line.autoactive):
            value = "ON"
        else:
            value = "OFF"
    mqttclient.publish(mqttpublishstring,value)

def switch_channel(channel,state):
    if (config['Simulation Mode'].getboolean('sim_relay_board') == True):
        log ("Pretending to set channel " + channel + " to " + state)
    else:
        if (channel=="line1"):
            line = line1
        if (channel=="line2"):
            line = line2
        if (channel=="line3"):
            line = line3

        if (state == "ON"):
            level = GPIO.LOW
            line.valveopen = True
        elif (state == "OFF"):
            level = GPIO.HIGH
            line.valveopen = False

        log("Setting channel " + line.name + " to " + state)
        GPIO.output(line.relais_gpiopin, level)

    update_mqtt_status(channel)

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

def semiautoirrigationjob(channel):
    if (channel=="line1"):
        line = line1
    if (channel=="line2"):
        line = line2
    if (channel=="line3"):
        line = line3

    if (line.mode == "semi-auto" and line.semiautoactive == True):
        log ("Starting semi-auto irrigation job at " + line.name + " for " + str(line.semi_irrigationtime) + "s")
        switch_channel(line.name,"ON")
        todolist_time[line.name] = [int(round(time.time() * 1000)), line.semi_irrigationtime*1000, "OFF"]

def semiautoirrigationjob_line1():
    semiautoirrigationjob("line1")

def semiautoirrigationjob_line2():
    semiautoirrigationjob("line2")

def semiautoirrigationjob_line3():
    semiautoirrigationjob("line3")



def autoirrigationjob(channel):
    if (channel=="line1"):
        line = line1
    if (channel=="line2"):
        line = line2
    if (channel=="line3"):
        line = line3

    if (line.mode == "auto" and line.autoactive == True):
        if (line.humidity < line.auto_sensitivity):
            log ("Starting auto irrigation job at " + line.name + " because auto_sensitivity " + str(line.auto_sensitivity) + " and line_moisture: " + str(line.humidity) + " for " + str(line.autoirrigationtime) +"s")
            switch_channel(line.name,"ON")
            todolist_time[line.name] = [int(round(time.time() * 1000)), line.autoirrigationtime*1000, "OFF"]

def autoirrigationjob_line1():
    autoirrigationjob("line1")

def autoirrigationjob_line2():
    autoirrigationjob("line2")

def autoirrigationjob_line3():
    autoirrigationjob("line3")

read_startup_values()

schedule.every(5).seconds.do(read_moisture_sensors)
#schedule.every().minute.at(":00").do(semiautoirrigationjob_line1)
schedule.every().hour.at(":00").do(autoirrigationjob_line1)
schedule.every().hour.at(":05").do(autoirrigationjob_line2)
schedule.every().hour.at(":10").do(autoirrigationjob_line3)
schedule.every().day.at("07:00").do(semiautoirrigationjob_line1)
schedule.every().day.at("07:05").do(semiautoirrigationjob_line2)
schedule.every().day.at("07:10").do(semiautoirrigationjob_line3)
schedule.every().day.at("13:00").do(semiautoirrigationjob_line1)
schedule.every().day.at("13:05").do(semiautoirrigationjob_line2)
schedule.every().day.at("13:10").do(semiautoirrigationjob_line3)
schedule.every().day.at("20:00").do(semiautoirrigationjob_line1)
schedule.every().day.at("20:05").do(semiautoirrigationjob_line2)
schedule.every().day.at("20:10").do(semiautoirrigationjob_line3)
#schedule.every(5).to(10).minutes.do(job)
#schedule.every().monday.do(job)
#schedule.every().wednesday.at("13:15").do(job)
#schedule.every().minute.at(":17").do(job)

def line_mode_to_lcd_string(line):
    s = "crap"
    if line.mode == "manu":
        s = "manu"
    if line.mode == "semi-auto":
        if line.semiautoactive:
            s = "SEMI"
        else:
            s = "semi"
    if line.mode == "auto":
        if line.autoactive:
            s = "AUTO"
        else:
            s = "auto"
    return s

display_ip = os.popen("/sbin/ifconfig wlan0 | grep 'inet' | egrep -o '([0-9]{1,3}\.){3}[0-9]{1,3}' | head -1").read().rstrip()
display_ssid = os.popen("/sbin/iwconfig wlan0 | grep 'ESSID' | awk '{print $4}' | awk -F\\\" '{print $2}'").read().rstrip()

def updatedisplay():
    global displaypage
    global display_ip
    global display_ssid

    if (buttons.b4):
        displaypage += 1
        if (displaypage >= 4):
            displaypage = 1

    if (line1.valveopen == 1):
        GPIO.output(pushbutton1_led_gpiopin, GPIO.HIGH)
    else:
        GPIO.output(pushbutton1_led_gpiopin, GPIO.LOW)
    if (line2.valveopen == 1):
        GPIO.output(pushbutton2_led_gpiopin, GPIO.HIGH)
    else:
        GPIO.output(pushbutton2_led_gpiopin, GPIO.LOW)
    if (line3.valveopen == 1):
        GPIO.output(pushbutton3_led_gpiopin, GPIO.HIGH)
    else:
        GPIO.output(pushbutton3_led_gpiopin, GPIO.LOW)

    if (displaypage == 1):
        displayTime = datetime.datetime.today().strftime("%y-%m-%d %H:%M")
        display1 = "{:<14} 1".format(displayTime[:14])
        display2 = "{:<4}  {:<4}  {:<4}".format(line_mode_to_lcd_string(line1)[:4],line_mode_to_lcd_string(line2)[:4],line_mode_to_lcd_string(line3)[:4])
        if buttons.b1:
            switch_channel("line1","ON")
            todolist_time["line1"] = [int(round(time.time() * 1000)), line1.manu_irrigationtime*1000, "OFF"]
        if buttons.b2:
            switch_channel("line2","ON")
            todolist_time["line2"] = [int(round(time.time() * 1000)), line2.manu_irrigationtime*1000, "OFF"]
        if buttons.b3:
            switch_channel("line3","ON")
            todolist_time["line3"] = [int(round(time.time() * 1000)), line3.manu_irrigationtime*1000, "OFF"]

    if (displaypage == 2):
        display1 = "{:<14} 2".format(display_ip[:14])
        display2 = "UPDAT          "
        if buttons.b1:
            display_ip = os.popen("/sbin/ifconfig wlan0 | grep 'inet' | egrep -o '([0-9]{1,3}\.){3}[0-9]{1,3}' | head -1").read().rstrip()
            display_ssid = os.popen("/sbin/iwconfig wlan0 | grep 'ESSID' | awk '{print $4}' | awk -F\\\" '{print $2}'").read().rstrip()
        if buttons.b3:
            os.popen("ifdown --force wlan0") 
            time.sleep(5)
            os.popen("ifup wlan0") 
    if (displaypage == 3):
        print("SSiID")
        display1 = "{:<14} 3".format(display_ssid[:14])
        display2 = "          REBOOT"
        if buttons.b3:
            os.popen("/sbin/reboot")



    #print("lcd1- ", display1)
    lcd.lcd_display_string(display1, 1)
    #print("lcd2- ", display2)
    lcd.lcd_display_string(display2, 2)
    clearbuttonsstates()



def updatebuttonstate():
    if not (GPIO.input(pushbutton1_gpiopin)):
        buttons.b1 = 1
        print("button 1 pressed")
    if not (GPIO.input(pushbutton2_gpiopin)):
        buttons.b2 = 1
        print("button 2 pressed")
    if not (GPIO.input(pushbutton3_gpiopin)):
        buttons.b3 = 1
        print("button 3 pressed")
    if not (GPIO.input(pushbutton4_gpiopin)):
        buttons.b4 = 1
        print("button 4 pressed")

def clearbuttonsstates():
    buttons.b1 = 0
    buttons.b2 = 0
    buttons.b3 = 0
    buttons.b4 = 0


log ("current ssid: " + display_ssid)
log ("current ipaddress: " + display_ip)

log ("Startup completed")

# the main loop
clearbuttonsstates()
while True:
    updatedisplay()
    schedule.run_pending()
    checktodolist_time()
    for x in range(10):
        updatebuttonstate()
        if buttons.b1 or buttons.b2 or buttons.b3 or buttons.b4:
            updatedisplay()
        time.sleep(.1)
