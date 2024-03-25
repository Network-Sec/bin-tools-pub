# Made for use on Google Colab

from flask import Flask, request, Response
from pyngrok import ngrok

ngrok.set_auth_token("--- add your token ---")
app = Flask(__name__)

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def proxy(path):
    if request.args.get('url'):
        url = request.args.get('url')
    else:
        url = f"http://{path}"

    # Forward the request to the target URL
    resp = requests.request(
        method=request.method,
        url=url,
        headers={key: value for (key, value) in request.headers if key != 'Host'},
        data=request.get_data(),
        cookies=request.cookies,
        allow_redirects=False)

    # Return the response received from the target URL
    excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
    headers = [(name, value) for (name, value) in resp.raw.headers.items()
               if name.lower() not in excluded_headers]
    
    response = Response(resp.content, resp.status_code, headers)
    return response
    
def run_app():
    app.run()

if __name__ == '__main__':
    # Start ngrok tunnel to port 5000
    ngrok_tunnel = ngrok.connect(5000)
    print('Public URL:', ngrok_tunnel.public_url)
    # Run the app in the background
    from threading import Thread
    thread = Thread(target=run_app)
    thread.start()
