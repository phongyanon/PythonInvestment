#!/usr/bin/python
# -*- coding: utf-8 -*-

import time, os
from bs4 import BeautifulSoup
import requests
import sys

import pandas as pd
import numpy as np

from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# stock = 'HUMAN'
# url = f'https://www.set.or.th/set/companyhighlight.do?symbol={stock}&language=th&country=US'

options = Options()
# Make it go faster by running headless
# This will remove the web browser GUI from popping up
options.headless = True

# driver = webdriver.Firefox(executable_path = r'C:\Users\A715-72G\Documents\geckodriver-v0.30.0-win64\geckodriver.exe', \
#                             options=options)
# driver.get(url)
# time.sleep(2)
# html = driver.page_source
# driver.quit()

# test_soup = BeautifulSoup(html, 'lxml')
# table = test_soup.find('table', {'class': 'table table-hover table-info'})

# table_rows = table.find_all('tr')
# print(table_rows[18])
# print(table_rows[19])

def getResponseSoup(url):
    driver = webdriver.Firefox(executable_path = r'C:\Users\A715-72G\Documents\geckodriver-v0.30.0-win64\geckodriver.exe', \
                                options=options)
    driver.get(url)
    time.sleep(2)
    html = driver.page_source

    driver.quit()
    soup = BeautifulSoup(html, 'lxml')

    return soup

def getStockData(symbol, industry = '', sector = ''):
    
    url = f'https://www.set.or.th/set/companyhighlight.do?symbol={symbol}&language=th&country=US'
    soup = getResponseSoup(url)
    table = soup.find('table', {'class': 'table table-hover table-info'})
    table_rows = table.find_all('tr')
    
    len_col = len(table_rows[2].find_all('td')[1:])
    years = [2022-i for i in range(len_col)]
    years.reverse()
    
    stock_data = {
        'Symbol': [symbol for i in range(len_col)],
        'Assets': [],
        'Liabilities': [],
        'Equity': [],
        'Paid-up Capital': [],
        'Revenue': [],
        'Net Profit': [],
        'EPS (Baht)': [],
        'ROA(%)': [],
        'ROE(%)': [],
        'Net Profit Margin(%)': [],
        'P/E': [],
        'P/BV': [],
        'Book Value per share (Baht)': [],
        'Dvd. Yield(%)': [],
        'Year': years, 
        'Industry': [industry for i in range(len_col)], 
        'Sector': [sector for i in range(len_col)]
    }
    
    for i, v in enumerate(table_rows[2].find_all('td')[1:]):
        if (not (v.string and v.string.strip())) or (v.string.strip() == '-') or (v.string.strip() == 'N/A') or (v.string.strip() == 'N.A.'):
            stock_data['Assets'].append(0)
        else:
            stock_data['Assets'].append(float(''.join(v.string.split(','))))

    for i, v in enumerate(table_rows[3].find_all('td')[1:]):
        if (not (v.string and v.string.strip())) or (v.string.strip() == '-') or (v.string.strip() == 'N/A') or (v.string.strip() == 'N.A.'):
            stock_data['Liabilities'].append(0)
        else:
            stock_data['Liabilities'].append(float(''.join(v.string.split(','))))
            
    for i, v in enumerate(table_rows[4].find_all('td')[1:]):
        if (not (v.string and v.string.strip())) or (v.string.strip() == '-') or (v.string.strip() == 'N/A') or (v.string.strip() == 'N.A.'):
            stock_data['Equity'].append(0)
        else:
            stock_data['Equity'].append(float(''.join(v.string.split(','))))
            
    for i, v in enumerate(table_rows[5].find_all('td')[1:]):
        if (not (v.string and v.string.strip())) or (v.string.strip() == '-') or (v.string.strip() == 'N/A') or (v.string.strip() == 'N.A.'):
            stock_data['Paid-up Capital'].append(0)
        else:
            stock_data['Paid-up Capital'].append(float(''.join(v.string.split(','))))
            
    for i, v in enumerate(table_rows[6].find_all('td')[1:]):
        if (not (v.string and v.string.strip())) or (v.string.strip() == '-') or (v.string.strip() == 'N/A') or (v.string.strip() == 'N.A.'):
            stock_data['Revenue'].append(0)
        else:
            stock_data['Revenue'].append(float(''.join(v.string.split(','))))
            
    for i, v in enumerate(table_rows[8].find_all('td')[1:]):
        if (not (v.string and v.string.strip())) or (v.string.strip() == '-') or (v.string.strip() == 'N/A') or (v.string.strip() == 'N.A.'):
            stock_data['Net Profit'].append(0)
        else:
            stock_data['Net Profit'].append(float(''.join(v.string.split(','))))
            
    for i, v in enumerate(table_rows[9].find_all('td')[1:]):
        if (not (v.string and v.string.strip())) or (v.string.strip() == '-') or (v.string.strip() == 'N/A') or (v.string.strip() == 'N.A.'):
            stock_data['EPS (Baht)'].append(0)
        else:
            stock_data['EPS (Baht)'].append(float(''.join(v.string.split(','))))
            
    for i, v in enumerate(table_rows[11].find_all('td')[1:]):
        if (not (v.string and v.string.strip())) or (v.string.strip() == '-') or (v.string.strip() == 'N/A') or (v.string.strip() == 'N.A.'):
            stock_data['ROA(%)'].append(0)
        else:
            stock_data['ROA(%)'].append(float(''.join(v.string.split(','))))
            
    for i, v in enumerate(table_rows[12].find_all('td')[1:]):
        if (not (v.string and v.string.strip())) or (v.string.strip() == '-') or (v.string.strip() == 'N/A') or (v.string.strip() == 'N.A.'):
            stock_data['ROE(%)'].append(0)
        else:
            stock_data['ROE(%)'].append(float(''.join(v.string.split(','))))
            
    for i, v in enumerate(table_rows[13].find_all('td')[1:]):
        if (not (v.string and v.string.strip())) or (v.string.strip() == '-') or (v.string.strip() == 'N/A') or (v.string.strip() == 'N.A.'):
            stock_data['Net Profit Margin(%)'].append(0)
        else:
            stock_data['Net Profit Margin(%)'].append(float(''.join(v.string.split(','))))
            
    for i, v in enumerate(table_rows[18].find_all('td')[1:]):
        if (not (v.string and v.string.strip())) or (v.string.strip() == '-') or (v.string.strip() == 'N/A') or (v.string.strip() == 'N.A.'):
            stock_data['P/E'].append(0)
        else:
            stock_data['P/E'].append(float(''.join(v.string.split(','))))
            
    for i, v in enumerate(table_rows[19].find_all('td')[1:]):
        if (not (v.string and v.string.strip())) or (v.string.strip() == '-') or (v.string.strip() == 'N/A') or (v.string.strip() == 'N.A.'):
            stock_data['P/BV'].append(0)
        else:
            stock_data['P/BV'].append(float(''.join(v.string.split(','))))
            
    for i, v in enumerate(table_rows[20].find_all('td')[1:]):
        if (not (v.string and v.string.strip())) or (v.string.strip() == '-') or (v.string.strip() == 'N/A') or (v.string.strip() == 'N.A.'):
            stock_data['Book Value per share (Baht)'].append(0)
        else:
            stock_data['Book Value per share (Baht)'].append(float(''.join(v.string.split(','))))
            
    for i, v in enumerate(table_rows[21].find_all('td')[1:]):
        if (not (v.string and v.string.strip())) or (v.string.strip() == '-') or (v.string.strip() == 'N/A') or (v.string.strip() == 'N.A.'):
            stock_data['Dvd. Yield(%)'].append(0)
        else:
            stock_data['Dvd. Yield(%)'].append(float(''.join(v.string.split(','))))
            
    return stock_data

stocks = pd.DataFrame(columns = [
        'Symbol',
        'Assets',
        'Liabilities',
        'Equity',
        'Paid-up Capital',
        'Revenue',
        'Net Profit',
        'EPS (Baht)',
        'ROA(%)',
        'ROE(%)',
        'Net Profit Margin(%)',
        'P/E',
        'P/BV',
        'Book Value per share (Baht)',
        'Dvd. Yield(%)',
        'Year', 
        'Industry', 
        'Sector'
])

SERVICE_PROF = ['BWG', 'GENCO', 'PRO', 'SISB', 'SO']
for stock in SERVICE_PROF: # ['BWG', 'GENCO', 'PRO', 'SISB', 'SO']
    print(stock)
    stock_dict = getStockData(stock, industry = 'SERVICE', sector = 'PROF')
    stock_df = pd.DataFrame(data=stock_dict)
    stocks = stocks.append(stock_df, ignore_index=True)
print('done...')

stocks.to_csv('SERVICE_PROF_stock.csv', index=False)