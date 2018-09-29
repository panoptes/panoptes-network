from flask import Flask, render_template, g, request
from flask_json import FlaskJSON, json_response
from flask_cors import CORS
from decimal import Decimal

from pocs.utils.db.postgres import get_cursor

DEBUG = True

app = Flask(__name__)
app.config.from_object(__name__)
json = FlaskJSON(app)
CORS(app)


@json.encoder
def custom_encoder(o):
    if isinstance(o, Decimal):
        return float(o)


def get_db_cursor():
    """ Get a handle to the CloudSQL proxy """
    if not hasattr(g, 'db_cur'):
        g.db_cur = get_cursor(db_name='metadata', db_user='panoptes')

    return g.db_cur


@app.route('/')
def root():
    return render_template('index.html')


@app.route('/observations')
def observations():

    print(request.args)

    limit = request.args.get('per_page', 5)
    current_page = request.args.get('current_page', 1)
    offset = 0

    cursor = get_db_cursor()
    cursor.execute("""
        SELECT t1.*, count(t2.id) as image_count FROM
        sequences t1, images t2
        WHERE t1.id=t2.sequence_id
        GROUP BY t1.id
        LIMIT %s OFFSET %s
        """, (limit, offset)
    )

    rows = cursor.fetchall()

    links = {
        "pagination": {
            "total": 10,
            "per_page": limit,
            "current_page": current_page,
            "last_page": 5,
            "next_page_url": '...',
            "prev_page_url": '...',
            "from": 1,
            "to": 10
        }
    }

    return json_response(data=rows, links=links)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
