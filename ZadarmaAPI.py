#!/usr/bin/env python3

import hashlib
import hmac
import base64
import requests
from urllib.parse import urlencode

class ZadarmaAPI:
    def __init__(self, user_key, secret_key, is_sandbox=False):
        self.base_url = "https://api-sandbox.zadarma.com" if is_sandbox else "https://api.zadarma.com"
        self.user_key = user_key
        self.secret_key = secret_key

    def _generate_signature(self, method, params):
        # Sort parameters alphabetically
        sorted_params = sorted(params.items(), key=lambda x: x[0])
        # Build query string (spaces encoded as %20)
        params_str = urlencode(sorted_params, encoding='utf-8')
        # Concatenate method, params_str, and MD5 of params_str
        signature_string = f"{method}{params_str}{hashlib.md5(params_str.encode()).hexdigest()}"
        # Generate HMAC-SHA1 hash
        hmac_sha1 = hmac.new(self.secret_key.encode(), signature_string.encode(), hashlib.sha1)
        # Base64-encode the hash
        return base64.b64encode(hmac_sha1.digest()).decode()

    def _make_request(self, method, params, request_type="get"):
        # Generate the Authorization header
        signature = self._generate_signature(method, params)
        headers = {"Authorization": f"{self.user_key}:{signature}"}
        # Make the API request
        url = f"{self.base_url}{method}"
        if request_type.lower() == "get":
            response = requests.get(url, headers=headers, params=params)
        else:
            response = requests.post(url, headers=headers, data=params)
        # Return the JSON response
        return response.json(), response.status_code, response.headers

    def get_account_info(self):
        """Get user account information."""
        return self._make_request("/v1/info/", {})

    def number_lookup(self, number):
        """Lookup information for a specific phone number."""
        return self._make_request("/v1/info/number_lookup/", {"numbers": number}, "post")


# Example usage
if __name__ == "__main__":
    # Replace with your API credentials
    USER_KEY = ""
    SECRET_KEY = ""

    # Initialize the API client
    api = ZadarmaAPI(USER_KEY, SECRET_KEY)

    # Get account info
    account_info, status_code, headers = api.get_account_info()
    print("Status Code:", status_code)
    print("Headers:", headers)
    print("Account Info:", account_info)

    # Perform a number lookup
    number = "4915217997685"  # Replace with the number to lookup
    lookup_result, status_code, headers = api.number_lookup(number)
    print("Status Code:", status_code)
    print("Headers:", headers)
    print("Number Lookup Result:", lookup_result)
