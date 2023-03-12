#
# ir receiver test for 4 digits 8 segments display
# RULE1 ON IrReceived#DataLSB DO publish stat/tasmota_1DAA95/IR %value% ENDON
# RULE 1
#
import time
from string import printable
import numpy as np
import paho.mqtt.client as mqtt

TOPIC_TASMOTA_ID = "1DAA95"
TOPIC_HOME_BOX_RESULT = f"stat/tasmota_{TOPIC_TASMOTA_ID}/RESULT"
TOPIC_HOME_BOX_IR = f"stat/tasmota_{TOPIC_TASMOTA_ID}/IR"
TOPIC_HOME_BOX_CMND = f"cmnd/tasmota_{TOPIC_TASMOTA_ID}/"
TOPIC_HOME_BOX_CMND_DIMMER = TOPIC_HOME_BOX_CMND + "DisplayDimmer"
TOPIC_HOME_BOX_CMND_DISPLAY_TEXT = TOPIC_HOME_BOX_CMND + "DisplayText"
TOPIC_HOME_BOX_CMND_DISPLAY_FLOAT = TOPIC_HOME_BOX_CMND + "DisplayFloat"
TOPIC_HOME_BOX_CMND_DISPLAY_CLOCK = TOPIC_HOME_BOX_CMND + "DisplayClock"
TOPIC_HOME_BOX_CMND_DISPLAY_SCROLL = TOPIC_HOME_BOX_CMND + "DisplayScrollText"


# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe(TOPIC_HOME_BOX_RESULT)
    client.subscribe(TOPIC_HOME_BOX_IR)


# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    print(msg.topic + " " + str(msg.payload))


client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect("192.168.147.1", 1883, 60)

client.publish(topic=TOPIC_HOME_BOX_CMND_DISPLAY_SCROLL, payload="IR TEST MSG")
time.sleep(5)

# for c in printable:
#     if c >= 'Z':
#         print(c)
#         client.publish(topic=TOPIC_HOME_BOX_CMND_DISPLAY_TEXT, payload=c)
#         time.sleep(2)

# for d in np.arange(-10.5, 10.5, 0.1):
#     d = round(d, 1)
#     if d == -0.0:
#         d = abs(d)
#     print(d)
#     client.publish(topic=TOPIC_HOME_BOX_CMND_DISPLAY_TEXT, payload=f"{d:.1f}".replace('.', '`'))
#     time.sleep(1)

# Blocking call that processes network traffic, dispatches callbacks and
# handles reconnecting.
# Other loop*() functions are available that give a threaded interface and a
# manual interface.
client.loop_forever()
