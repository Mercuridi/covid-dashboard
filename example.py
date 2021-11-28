from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return '<form action="/setalarm" method="get"> \
            <input type="datetime-local" name="alarm"> \
            <input name="two"> \
            <input type="submit"> \
            </form>'
if __name__ == '__main__':
    app.run()