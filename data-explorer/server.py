from bokeh.client import pull_session
from bokeh.embed import server_document
from bokeh.embed import server_session
from flask import Flask
from flask import render_template
from flask_cors import CORS

app = Flask(__name__)
cors = CORS(app)

URL = 'http://localhost:5006/data-explorer'


@app.route('/', methods=['GET'])
def bkapp_page():
    script = server_document(URL)

    # pull a new session from a running Bokeh server
    with pull_session(url=URL) as session:
        # update or customize that session
        # print(session.document.roots[0].children[0].text)
        # session.document.roots[0].children[0].text = f"Special Sliders For Me"
        # print(session.document.roots[0].children[0].text)
        print(session.document.roots)

        script = server_session(session_id=session.id, url=URL)
        # generate a script to load the customized session

        # use the script in the rendered page
        return render_template("embed.html", script=script)


@app.route('/<observation_id>', methods=['GET'])
def data_explorer(observation_id):
    pass


if __name__ == '__main__':
    print(
        'Opening single process Flask app with embedded Bokeh application on '
        'http://localhost:8000/')
    print()
    print('Multiple connections may block the Bokeh app in this configuration!')
    print('See "flask_gunicorn_embed.py" for one way to run multi-process')
    app.run(port=8000)
