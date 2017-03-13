import requests
import logging as log

from requests.exceptions import HTTPError

import Constants

url = 'http://'+Constants.WS_URL.split('ws://')[1]

def get_cameras():
    try:
        r = requests.get(url + '/cams')
        log.debug(r.status_code, r.headers)
        return r.json()
    except Exception as e:
        return {}

# def post_n_people(n):
#     data = {'key': key, 'n_people': n}
#     r = requests.post(url + '/people', data=data)
#     log.debug("status:%s, headers:%s, url:%s", r.status_code, r.headers, r.url)
#     parameters = r.json()
#     return parameters