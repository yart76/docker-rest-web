from flask import Flask
import json

app = Flask(__name__)

import socket
def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

@app.route('/')
def main() -> str:
    return 'This is reply from main page'


@app.route('/ping')
def ping() -> str:
	node = get_ip()
	response_object = {
		'status': 'successfull',
		'msg': 'This is returned ping',
		'node': node
	}
	return json.dumps(response_object)

if __name__ == '__main__':
      app.run(host='0.0.0.0', port=5001)
