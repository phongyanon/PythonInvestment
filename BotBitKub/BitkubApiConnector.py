import hashlib
import hmac
import json
import requests
import logging
import time


# set to true on debug environment only
DEBUG = True

DEFAULT_BITKUB_HOST = 'https://api.bitkub.com'
VERSION = '0.0.1'

# API inter-command timeout (in ms)
API_SEND_TIMEOUT = 100

# logger properties
logger = logging.getLogger("jsonSocket")
FORMAT = '[%(asctime)-15s][%(funcName)s:%(lineno)d] %(message)s'
logging.basicConfig(format=FORMAT)

if DEBUG:
    logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.CRITICAL)

class BitkubClient():
    def __init__(self, address=DEFAULT_BITKUB_ADDRESS, api_key='', api_secret=''):
        self.address = address
        self.header = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'X-BTK-APIKEY': api_key,
        }
        self.api_key = api_key
        self.api_secret = api_secret

    def json_encode(self, data):
        return json.dumps(data, separators=(',', ':'), sort_keys=True)

    def sign(self, data):
        j = self.json_encode(data)
        logger.info('Signing payload: ' + j)
        h = hmac.new(self.api_secret, msg=j.encode(), digestmod=hashlib.sha256)
        return h.hexdigest()

    def getServerTime(self):
        response = requests.get(DEFAULT_BITKUB_HOST + '/api/servertime')
        ts = int(response.text)
        logger.info('Server time: ' + response.text)
        return ts

    def buyLimitTest(self, symbol, amount, price):
        data = {
            'sym': symbol',
            'amt': amount, # BTC amount you want to buy
            'rat': price, # price
            'typ': 'limit', # limit or market (in case market set rat(price) to 0)
            'ts': self.getServerTime(),
        }
        signature = self.sign(data)
        data['sig'] = signature

        logger.info('Payload with signature: ' + self.json_encode(data))
        response = requests.post(DEFAULT_BITKUB_HOST + '/api/market/place-bid/test', headers=self.header, data=self.json_encode(data))
        logger.info('Response: ' + response.text)

    def sellLimitTest(self):
        data = {
            'sym': symbol',
            'amt': amount, # BTC amount you want to sell
            'rat': price, # price
            'typ': 'limit', # limit or market (in case market set rat(price) to 0)
            'ts': self.getServerTime(),
        }
        signature = self.sign(data)
        data['sig'] = signature

        logger.info('Payload with signature: ' + self.json_encode(data))
        response = requests.post(DEFAULT_BITKUB_HOST + '/api/market/place-ask/test', headers=self.header, data=self.json_encode(data))
        logger.info('Response: ' + response.text)

    def getMarketTicker(self, symbol=None):
        url = DEFAULT_BITKUB_HOST + '/api/market/ticker'
        if symbol != None:
            response = requests.get(url, params={'sym': symbol})
        else:
            response = requests.get(url)