import os
import sqlalchemy

from sqlalchemy import create_engine, engine
from panoptes.utils.serializers import from_json
from flask import jsonify

# Vars needed for database connection
connection_name = os.getenv("CONNECTION_NAME")
db_password = os.getenv("DB_PASSWORD")
db_name = os.getenv("DB_NAME")

db_user = os.getenv("DB_USER")
driver_name = "postgres+pg8000"  # Note: Connecting via the psycopg2 driver was throwing an error
query_string = {"unix_sock": "/cloudsql/{}/.s.PGSQL.5432".format(connection_name)}

# Sets up the database
db = create_engine(
    sqlalchemy.engine.url.URL(
        drivername=driver_name,
        username=db_user,
        password=db_password,
        database=db_name,
        query=query_string,
    ),
    pool_size=5,
    max_overflow=2,
    pool_timeout=30,
    pool_recycle=1800,
)


def entry_point(request):
    """Queries 'observationrecords' table from the observation portal db.
    Args:
        request: The request object.

    Returns:
        rows (JSON): A JSON response consisting of submitted observation requests and relevant target data.
    """

    try:
        with db.connect() as conn:
            stmt = "SELECT * FROM tom_observations_observationrecord"
            output = conn.execute(stmt)
    except Exception as e:
        return f"Error getting observations from database: {e!r}"

    rows = list()
    for row in output:
        data = dict(row)
        params = data["parameters"]
        params_dict = from_json(params)  # Converts 'params' JSON string into a Python object
        data["parameters"] = params_dict
        rows.append(data)
    return jsonify(rows)
