import json
import logging
import os


JSON_FILE = ".env.json"
VERY_HIGH_PRIORITY = -10
HIGH_PRIORITY = -1

analysis_data = {}
configuration = {}

# SECRET, TOKEN, USER = M2MApi.getCredentials()
def load_vars():
    try:
        with open(JSON_FILE) as fp:
            data = json.load(fp)
            configuration.update(data)
            configuration["LOG_LEVEL"] = data.get("LOG_LEVEL") or 20
            configuration["WS_PASSWORD"] = data.get("WS_PASSWORD") or "0"
            configuration["URL"] = data.get("URL")
            configuration["PORT"] = data.get("PORT") or 80
            configuration["CAMERA_NAME"] = data.get("CAMERA_NAME") or ""
            # Time operations
            configuration["MAX_HOUR"] = data.get("MAX_HOUR") or 10
            configuration["MAX_MIN"] = data.get("MAX_MIN") or 15
            # Sensor command
            configuration["SENSOR_DELAY"] = data.get("SENSOR_DELAY") or 500
            configuration["SENSOR_MAX_THRESHOLD"] = data.get("SENSOR_MAX_THRESHOLD") or 4000
            configuration["SENSOR_MIN_THRESHOLD"] = data.get("SENSOR_MIN_THRESHOLD") or 3000
            configuration["HEATMAP_SECONDS"] = data.get("HEATMAP_SECONDS") or 60
            configuration["HIGH_TEMPERATURE_ALARM"] = data.get("HIGH_TEMPERATURE_ALARM") or 10000
            configuration["MD_SENSITIVITY"] = data.get("MD_SENSITIVITY") or 5.0
            configuration["FLIP_HORIZONTAL"] = data.get("FLIP_HORIZONTAL") or False
            configuration["FLIP_VERTICAL"] = data.get("FLIP_VERTICAL") or False
            configuration["IMPACT_SECRET"] = data.get("IMPACT_SECRET") or ""
            configuration["IMPACT_TOKEN"] = data.get("IMPACT_TOKEN") or ""
            configuration["IMPACT_USER"] = data.get("IMPACT_USER") or ""
            configuration["IMPACT_URL"] = "api.impact.nokia-innovation.io"
            configuration["IMPACT_GROUP"] = "DM.NIP.ESPOO"
            configuration["IMPACT_SERIAL_NUMBER"] = "thermalcam:" + configuration["CAMERA_NAME"]

    except Exception:
        logging.error("No "+JSON_FILE+" file")
        exit(1)


def save_var(**kwargs):
    """saves all the key-value pairs provided both in cache and in file"""
    # read file
    with open(JSON_FILE, 'r') as fp:
        config = json.load(fp)
        for k,v in kwargs.iteritems():
            configuration[k] = v

    os.remove(JSON_FILE)
    with open(JSON_FILE, 'w') as fp:
        json.dump(configuration, fp, indent=4, sort_keys=True)


def get_var(*keys):
    """ accepts a list with the variables name you need, returns a tuple with the values or a value if only one key was provided"""
    if len(keys) > 1:
        return [configuration.get(key) for key in keys]
    else:
        return configuration[ keys[0] ]

load_vars()