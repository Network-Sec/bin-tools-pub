#!/usr/bin/env python3

# Spider for Inputs in website - see README

import sys
from tabnanny import verbose
import scrapy
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urlencode
from scrapy.crawler import CrawlerProcess
import argparse
import requests
from string import ascii_letters, digits
from random import choice
from fake_useragent import UserAgent
import socket
import logging
import json

class FormSpider(scrapy.Spider):
    name = 'form_spider'

    def __init__(self, start_url, show_method=True, show_status=False, output_json=False, test_protocols=True, verbose=False, *args, **kwargs):
        super(FormSpider, self).__init__(*args, **kwargs)
        self.start_urls = [start_url]
        self.show_method = show_method or output_json
        self.show_status = show_status or output_json
        self.output_json = output_json
        self.test_protocols = test_protocols
        self.results = {}
        self.domain = urlparse(start_url).netloc
        self.verbose = verbose
        if not verbose:
            logging.basicConfig(stream=sys.stderr, level=logging.ERROR, format='%(levelname)s: %(message)s')
        else:
            logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(levelname)s: %(message)s')

        if self.test_protocols:
            self.start_urls = self.perform_initial_tests(start_url)

    def perform_initial_tests(self, start_url):
        available_urls = []
        ip_address, resolved_hostname = self.resolve_host(start_url)

        if ip_address:
            available_urls += self.test_host_availability(ip_address, allow_insecure_ssl=True)
        if resolved_hostname and resolved_hostname != self.domain:
            available_urls += self.test_host_availability(resolved_hostname, allow_insecure_ssl=True)

        # Add original URL if it has a scheme, or test both http and https otherwise
        if urlparse(start_url).scheme:
            available_urls.append(start_url)
        else:
            available_urls += self.test_host_availability(start_url, allow_insecure_ssl=True)

        return list(set(available_urls))  # Remove duplicates

    @classmethod
    def test_host_availability(cls, url, allow_insecure_ssl=True, preferred_protocols=['http', 'https']):
        available_urls = []
        headers = {'User-Agent': UserAgent().random}
        for protocol in preferred_protocols:
            test_url = f"{protocol}://{url}" if not urlparse(url).scheme else url
            try:
                response = requests.get(test_url, headers=headers, allow_redirects=True, verify=allow_insecure_ssl)
                if response.status_code == 200:
                    logging.info(f"Available: {test_url}")
                    available_urls.append(test_url)
                else:
                    logging.info(f"Status {response.status_code} for: {test_url}")
            except requests.RequestException as e:
                logging.error(f"Error testing {test_url}: {str(e)}")
        return available_urls

    @classmethod
    def resolve_host(cls, url):
        hostname = urlparse(url).hostname or url
        try:
            ip_address = socket.gethostbyname(hostname)
            logging.info(f"Resolved {hostname} to IP: {ip_address}")
            try:
                hostname, _, _ = socket.gethostbyaddr(ip_address)
                logging.info(f"Reverse lookup of {ip_address}: {hostname}")
                return ip_address, hostname
            except socket.herror:
                logging.info(f"No reverse lookup found for IP: {ip_address}")
                return ip_address, None
        except socket.gaierror as e:
            logging.error(f"Could not resolve host: {url}. Error: {str(e)}")
            return None, None

    def parse(self, response):
        domain = urlparse(response.url).netloc
        if self.output_json and domain not in self.results:
            self.results[domain] = []

        links = response.css("a::attr(href)").getall()
        for link in links:
            next_page = response.urljoin(link)
            yield scrapy.Request(next_page, callback=self.parse)

        forms = response.css("form") or response.xpath("//form")
        for form in forms:
            action, method, inputs = self.extract_form_data(form, response)
            form_url = urljoin(response.url, action)
            method = method.upper()

            # URLs with and without random values
            query_string = urlencode(inputs)
            query_string_no_values = urlencode({k: '' for k in inputs.keys()})
            
            url_and_values = f"{form_url}?{query_string}"
            url_no_values = f"{form_url}?{query_string_no_values}"

            if self.show_status:
                status_code = self.test_url(url_and_values, method, inputs)
                prefix = f"[{method}] {status_code}"
            else:
                prefix = f"[{method}]" if self.show_method else ""

            output_with_values = f"{prefix} {url_and_values}" if prefix else url_and_values
            output_without_values = f"{prefix} {url_no_values}" if prefix else url_no_values

            if not self.output_json:
                print(output_with_values)
                print(output_without_values)
            else:
                input_list = [name for name, value in inputs.items()]
  
                self.results[domain].append({
                    'method': method,
                    'status_code': status_code,
                    'domain': domain,
                    'protocol': urlparse(url_no_values).scheme,
                    'url_with_values': url_and_values,
                    'url_without_values': url_no_values,
                    'params': input_list
                })

    def closed(self, reason):
        if self.output_json:
            print(json.dumps(self.results, indent=4))

    def extract_form_data(self, form, response):
        action = form.css("::attr(action)").get() or ''
        method = form.css("::attr(method)").get() or 'get'
        inputs = {input_field.css("::attr(name)").get(): input_field.css("::attr(value)").get() or self.random_value() for input_field in form.css("input, textarea") if input_field.css("::attr(name)").get()}
        return action, method, inputs

    def random_value(self):
        return ''.join(choice(ascii_letters + digits) for _ in range(8))

    def test_url(self, url, method, data):
        ua = UserAgent()
        headers = {'User-Agent': ua.random}
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, allow_redirects=True)
            else:
                response = requests.post(url, data=data, headers=headers, allow_redirects=True)
            return response.status_code
        except:
            return 'Error'
        
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Spider a website and list all URLs with forms.")
    parser.add_argument("start_url", help="The URL to start spidering from.")
    parser.add_argument("--show-method", action="store_true", help="Show the HTTP method (GET/POST) before URLs.")
    parser.add_argument("--show-status", action="store_true", help="Show the HTTP status code for each URL.")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format.")
    parser.add_argument("--stick-to-input", default=False, action="store_false", help="Skip testing availability for HTTP/HTTPS protocols and IP/Hostname resolution.")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output.")
    args = parser.parse_args()

    process = CrawlerProcess({
        'USER_AGENT': 'Mozilla/5.0 (compatible; MyFormSpider/1.0)',
        # Adjust logging level based on the verbose argument
        'LOG_LEVEL': 'INFO' if args.verbose else 'ERROR',
    })
    
    process.crawl(FormSpider, start_url=args.start_url, show_method=args.show_method, show_status=args.show_status, output_json=args.json, test_protocols=(1 - args.stick_to_input), verbose=args.verbose)
    process.start()
