from flask import Flask, render_template, request, Response
from generate_notes import generate_notes
app = Flask(__name__)
from l402 import getL402

@app.route('/')
def home():
    return render_template('index.html')


@app.route('/generate_notes', methods=['POST'])
def gen_notes():
    auth_header = request.headers.get('Authorization')
    if auth_header is None:
        l402 = getL402(1000)
        headers = {
            'WWW-Authenticate': l402
        }
        return Response("Authorization Required", 402, headers=headers)

    data = request.get_json(force=True)
    url = data['url']
    return generate_notes(url)


if __name__ == '__main__':
    app.run()
