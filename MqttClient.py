import json
import logging

import paho.mqtt.client as mqtt
import thread
import Constants
import Cache

url = Constants.IMPACT_URL
group = Constants.IMPACT_GROUP
token = Cache.TOKEN
secret = Cache.SECRET
user = Cache.USER
serialNumber = Constants.IMPACT_SERIAL_NUMBER
INSTANCE = "0"

reportingPeriod = 15

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("{0}/{1}/{2}/{3}/{4}".format(token, object, INSTANCE, reportingPeriod, serialNumber))

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    print(msg.topic+" "+str(msg.payload))

def on_publish(client, userdata, mid):
    pass

def on_subcribe(client, userdata, mid, granted_qos):
    logging.info("subscribed to topic")# , userdata,mid, granted_qos[0]


def submit_data(data, resource):
    object = "Analysis"
    topic = "{0}/{1}/{2}/{3}/{4}".format(token, serialNumber, object, INSTANCE, resource)
    logging.debug("publishing topic:" + topic)
    client.publish(topic, data)

def submit_telemetry(telemetry):
    object = 'Telemetry'
    for k,v in telemetry.iteritems():
        resource = "".join(k.split('_'))
        topic = "{0}/{1}/{2}/{3}/{4}".format(token, serialNumber, object, INSTANCE, resource)
        # print "publishing topic:" + topic, "data:"+str(v)
        client.publish(topic, str(v))

def topic_notify():
    topic = "IMPACT/REQUEST/ROUTER/MQTT"
    payload = json.dumps({
        "topicNotify": {
            "x-adaptation_layer_id":"MQTTDEVICE_ROUTER_adapter",
            "token":token,
            "callbacktopic":token + "/MYCAMPUS/RESTAURANT"
            #"correlatorId":"callbackCorrId"
        }
    })
    client.publish(topic, payload)


def register_device():
    topic = "IMPACT/REQUEST/ROUTER/MQTT"
    payload = json.dumps({
        "register": {
            "x-adaptation_layer_id":"MQTTDEVICE_ROUTER_adapter",
            "token":token,
            "device/0/"+ "endpoint-name" :serialNumber,
            "objectid":["restaurant","device"]
            #"correlatorId":"callbackCorrId"
        }
    })
    client.publish(topic, payload)

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
# client.on_publish = on_publish
client.on_subscribe = on_subcribe

client.username_pw_set(user, secret)
client.connect(url, 1883, 60)

# Blocking call that processes network traffic, dispatches callbacks and
# handles reconnecting.
# Other loop*() functions are available that give a threaded interface and a
# manual interface.
t = thread.start_new_thread(client.loop_forever, ())
