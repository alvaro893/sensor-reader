import logging
from json import JSONDecoder, JSONEncoder
from httplib import HTTPConnection
import Constants

url = Constants.IMPACT_URL
group = Constants.IMPACT_GROUP
serialNumber = Constants.IMPACT_SERIAL_NUMBER

port = 9090
headers ={"Content-Type":"application/json", "Accept": "application/json", "Authorization": "Basic YWx2YXJvYm9scm86QWx2YXJvQDkxIQ=="}

jsonEncoder = JSONEncoder()
jsonDecoder = JSONDecoder()

def getCredentials():
    path = '/m2m/token?type=resources&groupName='+group
    secret = ""; token = ""; username = ""
    try:
        dic =  _perform_request(path, headers)
        if dic['msg'] == 'Success':
            secret =   dic['tokenResponses'][0]['secret']
            token =    dic['tokenResponses'][0]['token']
            username = dic['tokenResponses'][0]['username']
    except Exception as e:
        logging.warn("cannot get credentials (are we connected to the Internet?) error message:%s", e.message)
    return secret,token,username

def registration():
    path = '/m2m/applications/registration'
    data = {'headers': {"Authorization": "Basic YWx2YXJvYm9scm86QWx2YXJvQDkxIQ=="}, 'url':'http://callback-server-ir-cloud.espoo-apps.ilab.cloud/m2m/impact/callback'}
    _perform_request(path, headers, 'PUT', data)

def listEndpoints(startOffset=1, endOffset=10):
    path='/m2m/endpoints?&groupName='+group +'&startOffset='+str(startOffset) + '&endOffset=' + str(endOffset)
    dic = _perform_request(path, headers)
    return dic

def readResource(resource):
    path = '/m2m/endpoints/'+serialNumber+'/thermal/0/'+resource
    dic = _perform_request(path, headers)
    return dic

def writeResource(resource, resourceValue):
    path = '/m2m/endpoints/'+serialNumber+'/thermal/0/'+resource
    data = {'resourceValue': resourceValue}
    dic = _perform_request(path, headers, method='PUT', data=data)
    return dic

def _perform_request(path, headers, method='GET', data=None):
    jsonData = None
    http = HTTPConnection(url, port, timeout=5)
    http.connect()
    if data:
        jsonData = jsonEncoder.encode(data)
    http.request(method, path, body=jsonData, headers=headers)
    response = http.getresponse()
    dic = jsonDecoder.decode(response.read())
    print response.status
    return dic