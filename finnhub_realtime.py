import json
import time
import requests
import csv
import datetime
from numpy import array
#https://finnhub.io/api/v1/stock/candle?symbol=AAPL&resolution=1&from=1572651390&to=1572910590&token=bqq642vrh5r8o85ku3cg
BASE_URL = 'https://finnhub.io/api/v1/stock/candle'
TOKEN_VALUE = 'btb4bdv48v6s28kj258g'


class REQUEST_PARAMETERS:
    SYMBOL = 'symbol'
    TOKEN = 'token'
    FROM = 'from'
    TO = 'to'
    RESOLUTION = 'resolution'


class SYMBOLS:
    AAPL = 'AAPL'
    YNDX = 'YNDX'
    NDAQ = 'NDAQ'
    QQQE = 'QQQE'

response = requests.get(
    BASE_URL,
    {
        REQUEST_PARAMETERS.SYMBOL: 'AAPL',
        REQUEST_PARAMETERS.RESOLUTION: 1,
        REQUEST_PARAMETERS.FROM: (datetime.datetime.now() + datetime.timedelta(days=-30)).strftime('%s'),
        REQUEST_PARAMETERS.TO: datetime.datetime.now().strftime('%s'),
        REQUEST_PARAMETERS.TOKEN:TOKEN_VALUE
    }
)
print('response', response.text)
serialized_response = response.json()

DATE_FORMAT = '%Y-%m-%d'
TIME_FORMAT = '%H:%M:00'

hours_dictionary = {
    datetime.datetime.fromtimestamp(timestamp).strftime(TIME_FORMAT): []
    for index, timestamp in enumerate(serialized_response['t'])
}


for index, timestamp in enumerate(serialized_response['t']):
    key_time = datetime.datetime.fromtimestamp(timestamp).strftime(TIME_FORMAT)
    hours_dictionary[key_time].append(serialized_response['v'][index])

hours_dictionary = {
    key: value
    for key, value in hours_dictionary.items() if len(value) > 10
}


def percenage(value, percenage):
    return value + (value * percenage / 100)


def fast_average(values):
    return sum(int(i) for i in values) / len(values)

hours_dictionary_average = {
    key: fast_average(value)
    for key, value in hours_dictionary.items()
}

response = requests.get(
    BASE_URL,
    {
        REQUEST_PARAMETERS.SYMBOL: 'AAPL',
        REQUEST_PARAMETERS.RESOLUTION: 1,
        REQUEST_PARAMETERS.FROM: (datetime.datetime.now() + datetime.timedelta(minutes=-5)).strftime('%s'),
        REQUEST_PARAMETERS.TO: datetime.datetime.now().strftime('%s'),
        REQUEST_PARAMETERS.TOKEN: TOKEN_VALUE
    }
)

serialized_response = response.json()

for index, timestamp in enumerate(serialized_response['t']):
    time_key = datetime.datetime.fromtimestamp(timestamp).strftime(TIME_FORMAT)
    fast_average = hours_dictionary_average[time_key]
    volume = serialized_response['v'][index]
    max_volume = percenage(fast_average, 30)
    print(
        'time: {}, volume: {} max_volume: {}, out {}'.format(time_key, volume, int(max_volume), volume > max_volume)
    )
print(serialized_response)

# for data, value in hours_dictionary_average.items():
#     print(data, value)
# print(hours_dictionary_average)



