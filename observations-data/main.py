from flask import Flask, g
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
        app.logger.info("Getting new DB proxy cursor")
        g.db_cur = get_cursor(db_name='metadata', db_user='panoptes')

    return g.db_cur


def get_all_observations():
    cursor = get_db_cursor()
    select_sql = """
        SELECT t1.*, count(t2.id) as image_count FROM
        sequences t1, images t2
        WHERE t1.id=t2.sequence_id
        GROUP BY t1.id
        ORDER BY t1.start_date DESC
        """

    cursor.execute(select_sql)
    rows = cursor.fetchall()

    return rows


def get_observation(sequence_id):
    cursor = get_db_cursor()

    select_sql = """
        SELECT * FROM
        sequences t1, images t2
        WHERE t1.id=t2.sequence_id
        AND t1.id=%s
        ORDER BY t2.date_obs DESC
        """

    cursor.execute(select_sql, (sequence_id, ))
    images = cursor.fetchall()

    return images


@app.route('/observations')
def all_observations():
    rows = get_all_observations()

    return json_response(data=rows, count=len(rows))


@app.route('/observations/<sequence_id>')
def observation(sequence_id):
    rows = get_observation(sequence_id)

    return json_response(data=rows, count=len(rows))


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
