import sys
import json
import os
import threading
import time
import logging
import itertools
from tkinter import Tk
import tkinter.messagebox as tkmsg
import _tkinter
import requests
from queue import *
import csv
import datetime
from numpy import array
#https://finnhub.io/api/v1/stock/candle?symbol=AAPL&resolution=1&from=1572651390&to=1572910590&token=bqq642vrh5r8o85ku3cg
BASE_URL = 'https://finnhub.io/api/v1/stock/candle'
TOKEN_VALUE = 'btd25l748v6q5ac9ejp0'

TIME_RESOLUTION = 5
DELAY = 60
SHOW_WARRINGS = True
DURATION = True
DATE_FORMAT = '%Y-%m-%d'
TIME_FORMAT = '%H:%M:00'
DATETIME_FORMAT = '%Y-%m-%d %H:%M:00'


try:
    os.makedirs('data/{}'.format(datetime.datetime.now().strftime(DATE_FORMAT)))
except FileExistsError:
    pass

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(
            'data/{}/{}.log'.format(
                datetime.datetime.now().strftime(DATE_FORMAT), datetime.datetime.now().strftime(TIME_FORMAT)
            ), mode='w'
        ),
        logging.StreamHandler()
    ]
)


class REQUEST_PARAMETERS:
    SYMBOL = 'symbol'
    TOKEN = 'token'
    FROM = 'from'
    TO = 'to'
    RESOLUTION = 'resolution'


class SYMBOLS:
    AAPL = 'AAPL'
    YNDX = 'YNDX'
    NDAQ = 'NDAQ' # najlepiej pokazuje dla Nasdaq.
    QQQE = 'QQQE'
    AMZN = 'AMZN'
    GLD = 'GLD' #GOLD
    GLDI = 'GLDI'
    GLL = 'GLL'

    FILTER_SYMBOL = NDAQ


class Counter(object):
    def __init__(self):
        self._number_of_read = 0
        self._counter = itertools.count()
        self._read_lock = threading.Lock()
        self._start_time = datetime.datetime.now()

    def increment(self):
        next(self._counter)

    def value(self):
        with self._read_lock:
            value = next(self._counter) - self._number_of_read
            self._number_of_read += 1
        return value

    def counts_per_minute(self):
        self.increment()
        minutes_diff = (datetime.datetime.now() - self._start_time).total_seconds() / 60.0
        return int(self.value()/minutes_diff)


requests_counter = Counter()


def percenage(value, percenage_value):
    return value + (value * percenage_value / 100)


def fast_average(values):
    return sum(int(i) for i in values) / len(values)


def get_hours_dictionary_average(hours_dictionary, time_key):
    try:
        return hours_dictionary[time_key]
    except KeyError as error:
        time_key_pivot = datetime.datetime.strptime(time_key, TIME_FORMAT)
        result = min(
            item
            for item in hours_dictionary.keys()
            if datetime.datetime.strptime(item, TIME_FORMAT) > time_key_pivot
        )
        return hours_dictionary[result]


def to_hours_dictionary(serialized_response, filter=True):

    hours_dictionary = {
        datetime.datetime.fromtimestamp(timestamp).strftime(TIME_FORMAT): []
        for index, timestamp in enumerate(serialized_response['t'])
    }

    for index, timestamp in enumerate(serialized_response['t']):
        key_time = datetime.datetime.fromtimestamp(timestamp).strftime(TIME_FORMAT)
        hours_dictionary[key_time].append(serialized_response['v'][index])

    if filter:
        hours_dictionary = {
            key: value
            for key, value in hours_dictionary.items() if len(value) > 5
        }

    if len(hours_dictionary.keys()) == 0:
        raise Exception('hours_dictionary is empty')
    return hours_dictionary


def show_info(symbol, time_key):
    try:
        tkmsg.showinfo(
            "Info",
            "Sprawwdz dane dla {} time {}".format(symbol, time_key)
        )
    except (_tkinter.TclError, RuntimeError) as error:
        logging.info('TK error!! {}'.format(error))


def parse_response_data(serialized_response, hours_dictionary_average, symbol, percenage_value, last_time_key, queue):
    counter = requests_counter.counts_per_minute()
    logging.info('serialized_response {}'.format(serialized_response))
    for index, timestamp in enumerate(serialized_response['t']):
        try:
            time_key = datetime.datetime.fromtimestamp(timestamp).strftime(TIME_FORMAT)
            last_time_key = time_key
            fast_average = get_hours_dictionary_average(hours_dictionary_average, time_key)
            volume = serialized_response['v'][index]
            max_volume = percenage(fast_average, percenage_value)
            if volume > max_volume and serialized_response['o'][index] > serialized_response['c'][index]:
                data = {
                    'symbol': symbol, 'time_key': time_key
                }
                queue.put(data)
            logging.info(
                'Symbol: {} time: {}, volume: {} max_volume: {} changed volume: {}, open: {}, close {} changed price {} o > c {} out {} req/min {} '.format(
                    symbol,
                    time_key,
                    volume,
                    int(max_volume),
                    (float(max_volume) / float(volume)) / 100,
                    serialized_response['o'][index],
                    serialized_response['c'][index],
                    (float(serialized_response['o'][index])/float(serialized_response['c'][index]))/100,
                    serialized_response['o'][index] > serialized_response['c'][index],
                    volume > max_volume,
                    counter
                )
            )
        except Exception as error:
            logging.info('Error ', error, type(error), symbol)
    return last_time_key


def collect_data(symbol, duration, index_value, percenage, queue):
    logging.info('Starting collect data for {}, percenage {} '.format(symbol, percenage))
    response = requests.get(
        BASE_URL,
        {
            REQUEST_PARAMETERS.SYMBOL: symbol,
            REQUEST_PARAMETERS.RESOLUTION: TIME_RESOLUTION,
            REQUEST_PARAMETERS.FROM: (datetime.datetime.now() + datetime.timedelta(days=-30)).replace(second=0, hour=0, minute=1).strftime('%s'),
            REQUEST_PARAMETERS.TO: (datetime.datetime.now() + datetime.timedelta(days=-1)).replace(second=0, hour=0, minute=1).strftime('%s'),
            REQUEST_PARAMETERS.TOKEN: TOKEN_VALUE,
        }
    )
    serialized_response = response.json()
    try:
        hours_dictionary = to_hours_dictionary(serialized_response)
    except Exception as error:
        logging.info('Exception {}: Symbol: {}, error {}, suspend this thred for 15 minutes'.format(type(error), symbol, error))
        time.sleep(60 * 15)
        return collect_data(symbol, duration, index_value, percenage)

    hours_dictionary_average = {
        key: fast_average(value)
        for key, value in hours_dictionary.items()
    }

    logging.info('Collected data, we start analysis for {}.'.format(symbol))
    last_time_key = None
    while True:
        time.sleep(
            ((datetime.timedelta(minutes=1) + datetime.datetime.now()).replace(
                second=1) - datetime.datetime.now()).total_seconds()
        )
        response = requests.get(
            BASE_URL,
            {
                REQUEST_PARAMETERS.SYMBOL: symbol,
                REQUEST_PARAMETERS.RESOLUTION: TIME_RESOLUTION,
                REQUEST_PARAMETERS.FROM: (datetime.datetime.now() + datetime.timedelta(minutes=-5)).strftime('%s'),
                REQUEST_PARAMETERS.TO: datetime.datetime.now().replace(second=1).strftime('%s'),
                REQUEST_PARAMETERS.TOKEN: TOKEN_VALUE,
            }
        )
        try:
            serialized_response = response.json()
        except json.decoder.JSONDecodeError:
            logging.info('Exception JSONG: {}'.format(response.content))
        try:
            last_time_key = parse_response_data(serialized_response, hours_dictionary_average, symbol, percenage, last_time_key, queue)
        except Exception as error:
            logging.info('Exception {}: error {} symbol: {},'.format(type(error), error, symbol))

follow_symbol_list = []
#GENERAL STOCK
follow_symbol_list += ['NDAQ', 'AAPL', 'AMZN', 'TSLA']
# #GOLD STOCK
follow_symbol_list += ['GOLD', 'GLD']
# #SILVER STOCK
follow_symbol_list += ['PSLV', 'SLV']
# #OILD STOCK
follow_symbol_list += ['USO', 'XOP']

# #copper
# follow_symbol_list += ['SCCO', 'CPER']
# bitcoind#
# follow_symbol_list += ['BINANCE:BTCUSDT', 'BINANCE:BCCUSDT']
#FOREX
# follow_symbol_list += ['BTCUSDT']

follow_symbol_details = {
    'NDAQ': {
        'percenage': 30,
        'family': 'index'
    },
    'AAPL': {
        'percenage': 30,
        'family': 'Akcje'
    },
    'TSLA': {
        'percenage': 30,
        'family': 'Akcje'
    },
    'AMZN': {
        'percenage': 30,
        'family': 'Akcje'
    },
    'GOLD': {
        'percenage': 50,
        'family': 'Gold'
    },
    'GLD': {
        'percenage': 50,
        'family': 'Gold'
    },
    'PSLV': {
        'percenage': 50,
        'family': 'Silver'
    },
    'SLV': {
        'percenage': 50,
        'family': 'Silver'
    },
    'USO': {
        'percenage': 50,
        'family': 'Oil'
    },
    'XOP': {
        'percenage': 50,
        'family': 'Oil'
    },
}

thread_array = []

_root = Tk()
_root.withdraw()
queue = Queue(maxsize=500)

for index, symbol in enumerate(follow_symbol_list):
    thread = threading.Thread(target=collect_data, args=(symbol, DURATION, index, follow_symbol_details[symbol]['percenage'], queue))
    thread_array.append(thread)

if follow_symbol_list:
    logging.info('I\'ve started work for the following symbols {}.'.format(follow_symbol_list))

for thread in thread_array:
    thread.start()


while True:
    data = queue.get()
    if data and SHOW_WARRINGS:
        show_info(data['symbol'], data['time_key'])
    else:
        time.sleep(1)
