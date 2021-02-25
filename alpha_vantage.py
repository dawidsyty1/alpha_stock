import json
import requests
import csv
import datetime
from numpy import array
# https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=IBM&apikey=demo
# https://www.alphavantage.co/query?function=SYMBOL_SEARCH&keywords=BA&apikey=demo
#https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol=IBM&interval=5min&apikey=demo
#https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol=IBM&apikey=E522003SX840UC9X
#https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=SLV&apikey=E522003SX840UC9X
#https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY_EXTENDED&function=TIME_SERIES_INTRADAY_EXTENDED&symbol=IBM&interval=15min&slice=year1month1&apikey=demo
# https://www.alphavantage.co/query?function=SYMBOL_SEARCH&keywords=silver&apikey=E522003SX840UC9X
BASE_URL = 'https://www.alphavantage.co/query'
API_KEY_VALUe = 'E522003SX840UC9X'


class FUNCTION_CHOICES:
    TIME_SERIES_INTRADAY = 'TIME_SERIES_INTRADAY'
    TIME_SERIES_INTRADAY_EXTENDED = 'TIME_SERIES_INTRADAY_EXTENDED'
    TIME_SERIES_DAILY = 'TIME_SERIES_DAILY'
    SYMBOL_SEARCH = 'SYMBOL_SEARCH'


class INTERVAL_CHOICES:
    ONE_MIN = '1min'
    FIVE_MIN = '5min'
    TEN_MIN = '10min'
    ONE_HOUR = '60min'


class REQUEST_PARAMETERS:
    SYMBOL = 'symbol'
    API_KEY = 'apikey'
    INTERVAL = 'interval'
    FUNCTION = 'function'
    KEYWORDS = 'keywords'
    SLICE = 'slice'


class KEY:
    META_DATA = 'Meta Data'
    TIME_SERIES_5_MINUTES = 'Time Series (5min)'


class SYMBOLS:
    IMB = 'IBM'
    OIL = 'OIL'
    SLV = 'SLV'
    NDAQ = 'NDAQ'

class SLICE_CHOICES:
    YEAR_MONTH = 'year1month1'

DATETIME_FORMAT = '%Y-%m-%d %H:%M:00'
DATE_FORMAT = '%Y-%m-%d'

#https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY_EXTENDED&function=TIME_SERIES_INTRADAY_EXTENDED&symbol=IBM&interval=15min&slice=year1month1&apikey=demo
response = requests.get(
    BASE_URL,
    {
        REQUEST_PARAMETERS.FUNCTION: FUNCTION_CHOICES.TIME_SERIES_INTRADAY_EXTENDED,
        REQUEST_PARAMETERS.INTERVAL: INTERVAL_CHOICES.FIVE_MIN,
        REQUEST_PARAMETERS.SYMBOL: SYMBOLS.NDAQ,
        REQUEST_PARAMETERS.SLICE: SLICE_CHOICES.YEAR_MONTH,
        REQUEST_PARAMETERS.API_KEY: API_KEY_VALUe
    }
)

# serialized_response = response.json()

VOLUME = '5. volume'

decoded_content = response.content.decode('utf-8')

data_list = list(csv.reader(decoded_content.splitlines(), delimiter=','))

start_date = datetime.datetime.strptime(data_list[1][0], DATETIME_FORMAT)
end_date = datetime.datetime.strptime(data_list[-1][0], DATETIME_FORMAT) + datetime.timedelta(days=1)
end_date = end_date.replace(hour=9, minute=30)

data_list = [
    row for row in data_list[1:] if datetime.datetime.strptime(row[0], DATETIME_FORMAT) >= end_date
]

today_data = [
    row for row in data_list if row[0].split(' ')[0] == start_date.strftime(DATE_FORMAT)
]

today_data_hours_dictionary = {
    row[0].split(' ')[1]: []
    for row in today_data[::-1]
}

for row in today_data:
    today_data_hours_dictionary[row[0].split(' ')[1]] = int(row[-1])


hours_dictionary = {
    row[0].split(' ')[1]: []
    for row in data_list
}

for row in data_list:
    hours_dictionary[row[0].split(' ')[1]].append(row)

hours_dictionary = {key: value for key, value in hours_dictionary.items() if len(value) > 5}

# for key, value in hours_dictionary.items():
#     fast_average = sum(int(i[-1]) for i in value)/len(value)
#     max_volume = fast_average + (fast_average * 40 / 100)
#     print('hours_dictionary', key, fast_average, max_volume)
#     for items in value:
#         volume = int(items[-1])
#         if volume > max_volume:
#             print(
#                 items[0].split(' ')[0], volume, volume > max_volume
#             )
#         else:
#             print(items[0].split(' ')[0], volume)
#     print()


def percenage(value, percenage):
    return value + (value * percenage / 100)


def fast_average(values):
    return sum(int(i[-1]) for i in values) / len(values)


hours_dictionary_average = {
    key: fast_average(value)
    for key, value in hours_dictionary.items()
}

# print(hours_dictionary_average['09:35:00'], percenage(hours_dictionary_average['09:35:00'], 40), hours_dictionary['09:35:00'][1][-1])
# print(today_data_hours_dictionary)

higher_volumen_count = 0

for key, value in today_data_hours_dictionary.items():
    try:
        fast_average = hours_dictionary_average[key]
        max_volume = percenage(fast_average, 30)
        if int(value) > max_volume:
            higher_volumen_count = higher_volumen_count + 1

        if higher_volumen_count > 2:
            print('hours_dictionary_average', key, hours_dictionary_average[key])
            print('today_data_hours_dictionary', value)
            print('')
            break
    except KeyError:
        pass


#https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol=IBM&interval=5min&apikey=demo