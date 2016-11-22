import requests, json
import logging as log

#log.basicConfig(level=log.DEBUG, format='%(relativeCreated)6d %(threadName)s %(message)s')
url = "http://ir-sensor-cloud.appspot.com/"
key = "development_server'"
#url = "http://localhost"


def get_paremeters():
    r = requests.get(url + '/')
    log.debug(r.status_code, r.headers)
    return r.json()


def post_n_people(n):
    data = {'key': key, 'n_people': n}
    r = requests.post(url + '/people', data=data)
    log.debug("status:%s, headers:%s, url:%s", r.status_code, r.headers, r.url)
    parameters = r.json()
    return parameters
