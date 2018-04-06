import json
import logging

import paho.mqtt.client as mqtt
import thread
from Cache import get_var, configuration

url,group,token,secret,user,serialNumber = \
    get_var("IMPACT_URL","IMPACT_GROUP","IMPACT_TOKEN", "IMPACT_SECRET", "IMPACT_USER", "IMPACT_SERIAL_NUMBER")
reportingPeriod = 15
INSTANCE = "0"


# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    logging.info("MQTT: %s", mqtt.connack_string(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("{0}/{1}/{2}/{3}/{4}".format(token, object, INSTANCE, reportingPeriod, serialNumber))


# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    print(msg.topic + " " + str(msg.payload))


def on_publish(client, userdata, mid):
    pass


def on_subcribe(client, userdata, mid, granted_qos):
    logging.info("subscribed to topic")  # , userdata,mid, granted_qos[0]

class MqttClient():
    def __init__(self):
        self.client = None
        self.instance = "0"



    def submit_data(self, data, resource):
        if self.client == None:
            return
        object = "Analysis"
        topic = "{0}/{1}/{2}/{3}/{4}".format(token, serialNumber, object, self.instance, resource)
        logging.debug("publishing topic:" + topic)
        self.client.publish(topic, data)

    def submit_telemetry(self, telemetry):
        if self.client == None:
            return
        object = 'Telemetry'
        for k,v in telemetry.iteritems():
            resource = "".join(k.split('_'))
            topic = "{0}/{1}/{2}/{3}/{4}".format(token, serialNumber, object, self.instance, resource)
            # print "publishing topic:" + topic, "data:"+str(v)
            self.client.publish(topic, str(v))

    def submit_configuration(self):
        if self.client == None:
            return
        object = 'Configuration'
        for k,v in configuration.iteritems():
            if not str(k).startswith('IMPACT'):
                resource = "".join(k.split('_'))
                topic = "{0}/{1}/{2}/{3}/{4}".format(token, serialNumber, object, self.instance, resource)
                # print "publishing topic:" + topic, "data:"+str(v)
                self.client.publish(topic, str(v))


    def topic_notify(self):
        if self.client == None:
            return
        topic = "IMPACT/REQUEST/ROUTER/MQTT"
        payload = json.dumps({
            "topicNotify": {
                "x-adaptation_layer_id":"MQTTDEVICE_ROUTER_adapter",
                "token":token,
                "callbacktopic":token + "/MYCAMPUS/RESTAURANT"
                #"correlatorId":"callbackCorrId"
            }
        })
        self.client.publish(topic, payload)


    def register_device(self):
        if self.client == None:
            return
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
        self.client.publish(topic, payload)

    def start(self):
        self.client = mqtt.Client()
        self.client.on_connect = on_connect
        self.client.on_message = on_message
        # self.client.on_publish = on_publish
        self.client.on_subscribe = on_subcribe

        self.client.username_pw_set(user, secret)
        self.client.connect(url, 1883, 60)

        # Blocking call that processes network traffic, dispatches callbacks and
        # handles reconnecting.
        # Other loop*() functions are available that give a threaded interface and a
        # manual interface.
        t = thread.start_new_thread(self.client.loop_forever, ())

instance = MqttClient()