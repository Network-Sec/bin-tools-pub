#!/usr/bin/env python3

# Basic Chromedriver Setup with examples for tasks like opening site, running JavaScript etc.
# Note that Chromedriver versions must match exactly for some setups, this is hit or miss

import requests
import json, time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions


# Setting the path explicitely may or may not be neccessary
chrome_service = ChromeService(executable_path='chromedriver')

# If you want to go headless, along with other common options I leave here for conveinance
chrome_options = ChromeOptions()
prefs = {"profile.managed_default_content_settings.images": 2}
chrome_options.add_experimental_option("prefs", prefs)
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument("--disable-extensions")

# chrome_options.add_argument('--headless')
# chrome_options.add_argument('-no-sandbox')
# chrome_options.add_argument('-disable-dev-shm-usage')
# chrome_options.add_argument('--disable-ipv6')
# chrome_options.page_load_strategy = 'none'

chrome_driver = webdriver.Chrome(options=chrome_options)
chrome_driver.get('https://network-sec.de')
chrome_driver.add_cookie({"name": "security", "value": "True", "path": "/", "domain": "network-sec.de", "expiry": 9999999999999})
chrome_driver.refresh()
time.sleep(1)

# Run JavaScript, return output
print("Cookie:", chrome_driver.execute_script("return document.cookie"))

# Close the Chrome webdriver
input("Press any key to quit Chrome")
chrome_driver.quit()
