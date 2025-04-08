from flask import Flask
app = Flask(__name__)

@app.route('/')
def hello_world():
    return '꧁ 𝐉𝐨𝐡𝐧 𝐖𝐢𝐜𝐤 ꧂'


if __name__ == "__main__":
    app.run()
