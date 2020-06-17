
import paho.mqtt.client as mqtt
import json
import math
import serial
import time
from mecode import G


from mqtt_settings import *

diff = [0, 0]

current_position = [0, 0]
#g = G()

# g = G(
#     direct_write=True, 
#     direct_write_mode="serial", 
#     printer_port="/dev/tty.usbserial-AL004P0B", 
#     baudrate=250000
# )  

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



def move_to_home():
    global current_position
    global s

    print("homeing")
    current_position = [0, 0]
    # send_gcode("G0 X0 Y200 Z18\n\n")  # absolute positiong

def move_to_position(x, y):
    global current_position
    global s
    print("move to ", x, y)

    current_position = [x, y]

    #G1 X90.6 Y13.8 ; move to 90.6mm on the X axis and 13.8mm on the Y axis
    #g.abs_move(x=x, y=y)

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

def play_demo():
    locations = [
    (51.1529546, 4.467264),
    (51.151787, 4.467498),
    (51.150966, 4.468099),
    (51.150394, 4.467627),
    (51.149566, 4.468045),
    (51.148717, 4.468519),
    (51.147781, 4.469055),
    (51.146926, 4.469527),
    (51.146145, 4.469978),
    (51.145049, 4.470492),
    (51.144234, 4.471111),
    (51.144517, 4.472484),
    (51.144497, 4.474104),
    (51.143677, 4.474934),
    (51.143347, 4.476070),
    (51.144132, 4.479176),
    (51.144484, 4.480997),
    (51.144374, 4.483768),
    (51.145134, 4.486332),
    (51.146657, 4.485055),
    (51.148150, 4.484126),
    (51.149528, 4.483397),
    (51.150866, 4.481649),
    (51.151500, 4.479891),
    (51.152471, 4.477514),
    (51.153464, 4.474598),
    (51.154196, 4.472561),
    (51.154872, 4.475031),
    (51.155494, 4.477476),
    (51.156844, 4.476854),
    (51.158264, 4.476418),
    (51.158316, 4.473963),
    (51.158457, 4.472125),
    (51.158294, 4.470623),
    (51.158531, 4.468708),
    (51.158640, 4.466937),
    (51.158358, 4.465745),
    (51.157498, 4.465601),
    (51.156034, 4.465224),
    (51.154882, 4.465479),
    (51.154158, 4.467140),
    (51.1529546, 4.467264)]

    for location in locations:
        goto_location(location[0], location[1])
        time.sleep(5)



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
    #s.flushInput()

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

    #move_to_home()

    #mqttc.loop_forever()

    play_demo()

if __name__ == "__main__":
    main()