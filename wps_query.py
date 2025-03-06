import argparse
import requests
from google.protobuf import message
from typing import List, Optional
import logging

# Import generated Protobuf file
from apple_pb2 import AppleWLoc, WifiDevice, Location  # Generated from .proto

# Constants
CONCURRENT_PARTS = 8
CONCURRENT_CELLS_PER_PART = 8

def encode_varint(value: int) -> bytes:
    parts = []
    while value > 0x7F:
        parts.append((value & 0x7F) | 0x80)
        value >>= 7
    parts.append(value)
    return bytes(parts)

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
        logging.debug(f"Sending request to {self.url()} with payload size {len(payload)} bytes")

        try:
            logging.debug(f"Payload (hex): {payload.hex()}")
            response = self.client.post(self.url(), data=payload, headers={
                'Content-Type': 'application/x-www-form-urlencoded', 
                'User-Agent': 'locationd/1753.17 CFNetwork/711.1.12 Darwin/14.0.0'
            }, timeout=30)
            response.raise_for_status()

            apple_wloc = AppleWLoc()
            apple_wloc.ParseFromString(response.content[10:])  # Skip first 10 bytes
            return apple_wloc

        except requests.RequestException as e:
            logging.error(f"Request failed: {e}")
            return AppleWLoc()

    def create_payload(self, wifi_devices: List[WifiDevice]) -> bytes:
        apple_wloc = AppleWLoc(wifi_devices=wifi_devices)
        serialized = apple_wloc.SerializeToString()
        varint_bytes = encode_varint(len(serialized))
        length_delimited = varint_bytes + serialized

        header = (
            bytes([0x00, 0x01, 0x00, 0x05]) +
            b"en_US" +
            bytes([0x00, 0x13]) +
            b"com.apple.locationd" +
            bytes([0x00, 0x0a]) +
            b"17.5.21F79" +
            bytes([0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00])
        )

        return header + length_delimited + serialized  # Include both parts

    def query_wifi(self, mac: str) -> Optional[Location]:
        wifi_device = WifiDevice(bssid=mac, location=None)
        response = self.query([wifi_device])
        if response.wifi_devices:
            for device in response.wifi_devices:
                loc = device.location
                if loc:
                    # Assuming latitude and longitude are floats
                    return Location(latitude=loc.latitude, longitude=loc.longitude)
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
    logging.basicConfig(level=logging.DEBUG) 
    args = parse_args()
    client = AppleWPSClient(china=args.china)

    if args.command == "query":
        mac = args.mac 
        location = client.query_wifi(mac)
        if location:
            print(f"Location found: Lat={location.latitude}, Lon={location.longitude}")
        else:
            print("Location not found.")


if __name__ == "__main__":
    main()
