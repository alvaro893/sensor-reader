import pytz, logging, os, time
from datetime import datetime, timedelta

LOCAL_TZ = pytz.timezone('Europe/Helsinki')

def get_weekday():
    return datetime.now(pytz.utc).astimezone(LOCAL_TZ).weekday()

def get_month():
    return datetime.now(pytz.utc).astimezone(LOCAL_TZ).month

def get_localtime():
    return str(datetime.now(pytz.utc).astimezone(LOCAL_TZ))

def get_localdate():
    return datetime.now(pytz.utc).astimezone(LOCAL_TZ).date().strftime('%d-%m-%Y')

def get_hour():
    return int(datetime.now(pytz.utc).astimezone(LOCAL_TZ).strftime('%H'))

def get_minute():
    return int(datetime.now(pytz.utc).astimezone(LOCAL_TZ).strftime('%M'))

def get_seconds():
    return int(datetime.now(pytz.utc).astimezone(LOCAL_TZ).strftime('%S'))

def get_hour_minute():
    return datetime.now(pytz.utc).astimezone(LOCAL_TZ).strftime('%H:%M')

