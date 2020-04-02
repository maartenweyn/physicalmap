
import paho.mqtt.client as mqtt
import json
import math
from mecode import G


from mqtt_settings import *

diff = [0, 0]

current_position = [0, 0]
g = G()

# g = G(
#     direct_write=True, 
#     direct_write_mode="serial", 
#     printer_port="/dev/tty.usbmodem1411", 
#     baudrate=115200
# )  


def move_to_home():
    global current_position
    global g

    print("homeing")
    current_position = [0, 0]


    g.absolute()
    g.home()

def move_to_position(x, y):
    global current_position
    global g
    print("move to ", x, y)

    current_position = [x, y]

    g.abs_move(x=x, y=y)

def on_connect(mqttc, obj, flags, rc):
    print("rc: " + str(rc))


def on_message(mqttc, obj, msg):
    global diff
    global lon0
    global lat0
    global size_map

    print(str(msg.payload))
    data = json.loads(msg.payload)

    dxy = [abs(1000 * (lon0-data["lon"])*40000*math.cos((lat0+data["lat"])*math.pi/360)/360), abs(1000 * (lat0-data["lat"])*40000/360)]
    pxy = [dxy[0] / diff[0], dxy[1] / diff[1]]

    posx = pxy[0] * size_map[0]
    posy = pxy[1] * size_map[0]
    
    print(data["lat"], data["lon"], " -> ", dxy, " -> ", pxy, "->", posx, posy)   
    
    move_to_position(posx, posy)

def on_publish(mqttc, obj, mid):
    print("mid: " + str(mid))


def on_subscribe(mqttc, obj, mid, granted_qos):
    print("Subscribed: " + str(mid) + " " + str(granted_qos))


def on_log(mqttc, obj, level, string):
    print(string)




def main():
    global diff

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

    move_to_home()

    mqttc.loop_forever()

if __name__ == "__main__":
    main()