import json

import paho.mqtt.client as mqtt
import thread

#url = "api.iot.nokia.com"
url = "api.impact.nokia-innovation.io"
token = "1iuqfwuzahqap"
secret = "F1/xN3eVGu1DjZLO6q3BnbCAYImv4Jbm2WVimwzTmJo="
group = "DM.NIP.ESPOO"
user = "ALVAROBOLRO"
reportingPeriod = 15
endPointClientName = 0006700001
serialNumber = "urn:sku:thermal-001"
object = "thermal"
instance = "0"
resource = "peopleCounter"

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("{0}/{1}/{2}/{3}/{4}".format(token, object, instance, reportingPeriod, serialNumber))

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    print(msg.topic+" "+str(msg.payload))

def on_publish(client, userdata, mid):
    print "published"

def on_subcribe(client, userdata, mid, granted_qos):
    print "subscribed" , userdata,mid, granted_qos[0]


def submit_data(data, resource):
    topic = "{0}/{1}/{2}/{3}/{4}".format(token, serialNumber, object, instance, resource)
    print "publishing topic:" + topic, "data:"+str(data)
    client.publish(topic, data)

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
client.on_publish = on_publish
client.on_subscribe = on_subcribe

client.username_pw_set(user, secret)
client.connect(url, 1883, 60)

# Blocking call that processes network traffic, dispatches callbacks and
# handles reconnecting.
# Other loop*() functions are available that give a threaded interface and a
# manual interface.
t = thread.start_new_thread(client.loop_forever, ())
