#!/usr/bin/python
# -*- coding: utf-8 -*-

import time, os
from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
import sys

stock = 'HUMAN'
url = f'https://www.set.or.th/set/companyhighlight.do?symbol={stock}&language=th&country=US'

driver = webdriver.Firefox()
driver.get(url)

time.sleep(8)

## Login
el = driver.find_element_by_css_selector("table[class*='table table-hover table-info']")
print(el)