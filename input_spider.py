#!/usr/bin/env python3

# Note: Script isn't 100% yet... wait a week or two, if you care

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
    results = {}
    
    def __init__(self, start_url, show_method=True, show_status=False, output_json=False, test_protocols=True, verbose=False, *args, **kwargs):
        super(FormSpider, self).__init__(*args, **kwargs)
        self.start_urls = []
        self.show_method = show_method or output_json
        self.show_status = show_status or output_json
        self.output_json = output_json
        self.test_protocols = test_protocols
        self.results = {}
        self.domain = urlparse(start_url).netloc
        self.verbose = verbose
        if verbose:
            logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(levelname)s: %(message)s')

        if self.test_protocols:
            self.start_urls = self.perform_initial_tests(start_url)
        else:
            self.start_urls.append(self.start_url)
        print(self.start_urls)

    def perform_initial_tests(self, start_url):
        available_urls = []

        # Determine if the start_url is an IP address
        is_ip = self.is_ip_address(start_url)
        scheme = urlparse(start_url).scheme
        hostname_or_ip = urlparse(start_url).hostname if scheme else start_url

        # Prepare URLs for testing based on whether a scheme is present
        if not scheme:
            base_urls = [f"http://{hostname_or_ip}", f"https://{hostname_or_ip}"]
        else:
            base_urls = [start_url]

        # Test each base URL and follow redirects
        for base_url in base_urls:
            final_urls = self.test_host_availability(base_url)
            if final_urls:
                available_urls += final_urls

        # Additional testing if input is an IP address
        if is_ip:
            resolved_hostname = ""
            try:
                resolved_hostname, _, _ = socket.gethostbyaddr(hostname_or_ip)
                resolved_hostname = resolved_hostname.split('.')[-2] + '.' + resolved_hostname.split('.')[-1]
                if verbose: logging.info(f"Reverse lookup of {hostname_or_ip}: {resolved_hostname}")            
            except socket.herror:
                if verbose: logging.info(f"No reverse lookup found for IP: {hostname_or_ip}")
                
            if resolved_hostname:
                for protocol in ['http', 'https']:
                    final_urls = self.test_host_availability(f"{protocol}://{resolved_hostname}")
                    if final_urls:
                        available_urls += final_urls

        return list(set(available_urls))
    
    def closed(self, reason):
        if self.output_json:
            print(json.dumps(self.results, indent=4))

    @staticmethod
    def is_ip_address(string):
        try:
            socket.inet_aton(string)
            return True
        except socket.error:
            return False

    @classmethod
    def test_host_availability(cls, url, allow_insecure_ssl=True, preferred_protocols=['http', 'https']):
        available_urls = []
        headers = {'User-Agent': UserAgent().random}
        for protocol in preferred_protocols:
            test_url = f"{protocol}://{url}" if not urlparse(url).scheme else url
            try:
                response = requests.get(test_url, headers=headers, allow_redirects=True, verify=allow_insecure_ssl)
                if response.status_code == 200:
                    logging.info(f"Available: {response.url}")
                    available_urls.append(response.url)
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
            self.results[domain] = {'urls': [], 'forms': []}

        # Collect all links before yielding requests or outputting
        all_urls = []
        links = response.css("a::attr(href)").getall()
        for link in links:
            next_page = response.urljoin(link)
            all_urls.append(next_page)  # Collect for later output
            yield scrapy.Request(next_page, callback=self.parse)

        # Process and collect forms
        forms = response.css("form") or response.xpath("//form")
        for form in forms:
            action, method, inputs = self.extract_form_data(form, response)
            form_url = urljoin(response.url, action)
            method = method.upper()

            query_string = urlencode(inputs)
            query_string_no_values = urlencode({k: '' for k in inputs.keys()})
            
            url_and_values = f"{form_url}?{query_string}"
            url_no_values = f"{form_url}?{query_string_no_values}"

            status_code = self.test_url(url_and_values, method, inputs) if self.show_status else None
            prefix = f"[{method}] {status_code}" if self.show_status else (f"[{method}]" if self.show_method else "")
            output_with_values = f"{prefix} {url_and_values}" if prefix else url_and_values
            output_without_values = f"{prefix} {url_no_values}" if prefix else url_no_values

            # Append form data to results for JSON output
            if self.output_json:
                self.results[domain]['forms'].append({
                    'method': method,
                    'status_code': status_code,
                    'url_with_values': url_and_values,
                    'url_without_values': url_no_values,
                    'params': [name for name, value in inputs.items()]
                })

        # Include all found URLs in both regular and JSON output
        all_urls.extend([url_and_values, url_no_values])  # Add form URLs to the list
        if not self.output_json:
            for url in all_urls:
                print(url)
        else:
            self.results[domain]['urls'].extend(all_urls)

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
        'LOG_ENABLED': args.verbose,  
    })
    
    process.crawl(FormSpider, start_url=args.start_url, show_method=args.show_method, show_status=args.show_status, output_json=args.json, test_protocols=(1 - args.stick_to_input), verbose=args.verbose)
    process.start()
