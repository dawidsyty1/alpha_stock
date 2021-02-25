import requests
from bs4 import BeautifulSoup, Comment
import csv
import os
import re
import glob


def cleanup_comments(html_soup):
    for element in html_soup(text=lambda text: isinstance(text, Comment)):
        if isinstance(element, Comment):
            element.extract()


def grab_data_with_prerender_by_ticker(ticker):
    url = f'http://localhost:3000/render?url=https://www.barchart.com/etfs-funds/quotes/{ticker}/options'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    cleanup_comments(soup)

    return soup


def grab_data_with_prerender_by_ticker_and_expiration_date(ticker, expiration_date):
    url = f'http://localhost:3000/render?url=https://www.barchart.com/etfs-funds/quotes/{ticker}/options?expiration={expiration_date}'
    print(f'Grabing data for {expiration_date}')
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    cleanup_comments(soup)

    return soup


def grab_expiration_data(soup):
    expiration_data = soup.find_all('option', attrs={"data-ng-bind": "expiration"})
    return [
        item.get('value')
        for item in expiration_data[:3]
    ]


def clear_dir(ticker):
    try:
        files = glob.glob(f'options/{ticker}/put/*')
        for f in files:
            os.remove(f)
    except FileNotFoundError:
        pass

    try:
        files = glob.glob(f'options/{ticker}/call/*')
        for f in files:
            os.remove(f)
    except FileNotFoundError:
        pass


def create_file(ticker, date, type):
    if not os.path.exists(f'options/{ticker}/{type}'):
        os.makedirs(f'options/{ticker}/{type}')

    outfile = open(f'options/{ticker}/{type}/{date}.csv', 'w+', newline='')
    writer = csv.writer(outfile)
    return writer


def cleanup_row(elements):
    pattern = re.compile(r'\s+')

    return [
        re.sub(pattern, '', elem.text)
        for elem in elements[:12]
    ]


def grab_tables_data(soup, ticker, date):
    tables = soup.find_all('table')
    for index, table in enumerate(tables):
        writer = create_file(
            ticker, date, 'call' if index == 0 else 'put'
        )
        for tr in table.find_all('tr'):
            ths = tr.find_all('th')
            row = cleanup_row(ths)

            tds = tr.find_all('td')
            row = row + cleanup_row(tds)
            writer.writerow(row)
    return tables


def scrap_options(tickers):
    for ticker in tickers:
        clear_dir(ticker)

        html_soup = grab_data_with_prerender_by_ticker(ticker)
        expiration_data = grab_expiration_data(html_soup)

        for date in expiration_data:
            soup = grab_data_with_prerender_by_ticker_and_expiration_date(ticker, date)
            grab_tables_data(soup, ticker, date)


tickers = ['DBA', 'FRT', 'VNQ']
scrap_options(tickers)
