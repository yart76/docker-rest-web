from flask import Flask
import json

app = Flask(__name__)

@app.route('/')
def main() -> str:
    return 'This is reply from main page'

@app.route('/ping')
def ping() -> str:
	response_object = {
		'status': 'successfull',
		'msg': 'This is returned ping'
	}
	return json.dumps(response_object)

if __name__ == '__main__':
      app.run(host='0.0.0.0', port=5001)
