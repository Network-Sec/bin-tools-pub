# Made for use on Google Colab

import http.server
import socketserver
import threading
import time
import socket

class RequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        print(f"Received GET request for URL: {self.path}")
        self.send_response(HTTPStatus.OK)
        self.end_headers()
        self.wfile.write(b"Request logged.")

def get_ip():
    # Attempt to find the best possible IP representation (might be localhost in some cases)
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

def run_server(port=8223, duration=120):
    server_ip = get_ip()
    with socketserver.TCPServer(("", port), RequestHandler) as httpd:
        print(f"Serving HTTP on {server_ip}:{port}...")
        server_thread = threading.Thread(target=httpd.serve_forever)
        server_thread.daemon = True
        server_thread.start()
        try:
            # Run for specified duration then shutdown
            time.sleep(duration)
        finally:
            httpd.shutdown()
            print("Server stopped.")

# Run the server for 1 minute
run_server_thread = threading.Thread(target=run_server)
run_server_thread.start()
