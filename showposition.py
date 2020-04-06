#Author: Maarten Weyn


import paho.mqtt.client as mqtt
import json
import math
import serial
import time


from mqtt_settings import *

diff = [0, 0]

s = serial.Serial('/dev/tty.usbserial-AL004P0B',250000)

def send_gcode(code, confirm = 0):
    global s

    success = False

    print(" -> {}".format(code))
    s.write(code.encode())

    while (not success):
        s.write(b"\r\n")

        time.sleep(1)
        while s.inWaiting():  # Or: while ser.inWaiting():
            answer = s.readline().decode("utf-8").strip()
            print(" <- {}".format(answer)) 
            if (not confirm):
                success = True
            else :
                if (answer == "ok"):
                    success = True

def move_to_position(x, y):
    print("move to ", x, y)

    command = "G0 X{} Y{}".format(x*10, 200 - (y*10))
    send_gcode(command, 1)

def on_connect(mqttc, obj, flags, rc):
    print("rc: " + str(rc))

def goto_location(lat, lon):
    global diff
    global lon0
    global lat0
    global size_map

    print("Incomming position {} ,{}".format(lat, lon))

    dxy = [abs(1000 * (lon0-lon)*40000*math.cos((lat0+lat)*math.pi/360)/360), abs(1000 * (lat0-lat)*40000/360)]
    pxy = [dxy[0] / diff[0], dxy[1] / diff[1]]

    posx = pxy[0] * size_map[0]
    posy = pxy[1] * size_map[0] 

    move_to_position(posx, posy)

def on_message(mqttc, obj, msg):
    print(str(msg.payload))
    data = json.loads(msg.payload)

    goto_location(data["lat"], data["lon"])


def on_publish(mqttc, obj, mid):
    print("mid: " + str(mid))


def on_subscribe(mqttc, obj, mid, granted_qos):
    print("Subscribed: " + str(mid) + " " + str(granted_qos))


def on_log(mqttc, obj, level, string):
    print(string)



def main():
    global diff
    global s
    global nozzle_speed
    global size_map

    mqttc = mqtt.Client()
    mqttc.on_message = on_message
    mqttc.on_connect = on_connect
    mqttc.on_publish = on_publish
    mqttc.on_subscribe = on_subscribe
    # Uncomment to enable debug messages
    # mqttc.on_log = on_log
    mqttc.username_pw_set(username=mqtt_username,password=mqtt_password)
    mqttc.connect(mqtt_host, 1883, 60)
    mqttc.subscribe(mqtt_topic, 0)

    diff = [abs(1000 * (lon0-lon1)*40000*math.cos((lat0+lat1)*math.pi/360)/360), abs(1000 * (lat0-lat1)*40000/360)]

    print("size", diff)  
    speed = int((nozzle_speed * 10000 / 60) / (1000 * size_map[0] / diff[0]))
    print("speed", speed)

    # Wake up 
    time.sleep(2) 
    send_gcode("\r\n\r\n") 
    time.sleep(2) 

    send_gcode("G90", 1) #absolute positioning\r\n", 1)
    send_gcode("M420 R0 E1 B0", 1) # LEDs to Green\r\n")
    send_gcode("M82", 1) #set extruder to absolute mode\r\n")
    send_gcode("M107", 1) #start with the fan off\r\n")
    send_gcode("G28", 1) #; Autohome;\r\n")
    send_gcode("G1 Z02.0 F9000", 1) #move the platform down 25mm\r\n")
    send_gcode("G1 X0 Y200", 1) #; Hot end to the front-left corner.\r\n")
    send_gcode("M420 R1 E0 B1", 1) # LEDs to Purple\r\n")
    send_gcode("T0", 1) # Set to use the first extruder (right)\r\n")
    send_gcode("G92 E0", 1) #zero the extruded length\r\n")


    send_gcode("G1 F5000", 1) #\r\n")
    send_gcode("M117 Printing...", 1)
    send_gcode("M420 R1 E1 B1", 1) # LEDs to White\r\n")

    mqttc.loop_forever()


if __name__ == "__main__":
    main()