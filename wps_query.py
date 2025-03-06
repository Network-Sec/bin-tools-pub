import argparse
import requests
from google.protobuf import message
from typing import List, Optional
import logging

# Import generated Protobuf file
from apple_pb2 import AppleWLoc, WifiDevice, Location  
import macaddress 

# Constants
CONCURRENT_PARTS = 8
CONCURRENT_CELLS_PER_PART = 8

class AppleWPSClient:
    def __init__(self, china: bool):
        self.client = requests.Session()
        self.china = china

    def url(self) -> str:
        if self.china:
            return "https://gs-loc-cn.apple.com/clls/wloc"
        else:
            return "https://gs-loc.apple.com/clls/wloc"

    def query(self, wifi_devices: List[WifiDevice]) -> AppleWLoc:
        payload = self.create_payload(wifi_devices)

        try:
            response = self.client.post(self.url(), data=payload, headers={
                'Content-Type': 'application/x-protobuf',
                'User-Agent': 'locationd/1753.17 CFNetwork/711.1.12 Darwin/14.0.0'
            }, timeout=10)
            response.raise_for_status()

            # Parse protobuf response
            apple_wloc = AppleWLoc()
            apple_wloc.ParseFromString(response.content[10:])  # Skipping first 10 bytes (as per the protocol)
            return apple_wloc

        except requests.RequestException as e:
            logging.error(f"Request failed: {e}")
            return AppleWLoc()  # Return empty if failed

    def create_payload(self, wifi_devices: List[WifiDevice]) -> bytes:
        # Build the protobuf message manually (based on the Rust code)
        apple_wloc = AppleWLoc(wifi_devices=wifi_devices)
        serialized = apple_wloc.SerializeToString()
        # Custom headers (first bytes for header in Rust code)
        header = bytes([0x00, 0x01, 0x00, 0x05]) + b"en_US" + bytes([0x00, 0x13]) + b"com.apple.locationd" + bytes([0x00, 0x0a]) + b"17.5.21F79" + bytes([0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00])
        return header + serialized

    def query_wifi(self, mac: str) -> Optional[Location]:
        wifi_device = WifiDevice(bssid=mac, location=None)
        response = self.query([wifi_device])
        if response.wifi_devices:
            for device in response.wifi_devices:
                loc = device.location
                if loc:
                    return Location(lat=loc.latitude / 1e8, lon=loc.longitude / 1e8)
        return None


def parse_args():
    parser = argparse.ArgumentParser(description="Query Apple Wi-Fi location")
    parser.add_argument('--china', action='store_true', help="Query Chinese servers")
    subparsers = parser.add_subparsers(dest='command')
    
    # Query command
    query_parser = subparsers.add_parser('query', help="Query a BSSID")
    query_parser.add_argument('mac', type=str, help="The MAC address of the Wi-Fi device")
    
    return parser.parse_args()


def main():
    args = parse_args()
    client = AppleWPSClient(china=args.china)

    if args.command == "query":
        mac = args.mac  # Now it's just a string, as macaddress is no longer needed
        location = client.query_wifi(mac)
        if location:
            print(f"Location found: Lat={location.lat}, Lon={location.lon}")
        else:
            print("Location not found.")

if __name__ == "__main__":
    main()
