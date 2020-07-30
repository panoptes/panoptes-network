import os
import sqlalchemy

from sqlalchemy.sql import select, alias
from sqlalchemy import create_engine, MetaData, Table, engine
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
    """Queries 'observationrecords', 'target' tables from the observation portal db and joins the two tables as a JSON.
    Args:
        request: The request object.

    Returns:
        rows (JSON): A JSON response consisting of submitted observation requests and associated target data.
    """

    metadata = MetaData()
    records = Table("tom_observations_observationrecord", metadata, autoload=True, autoload_with=db)
    targets = Table("tom_targets_target", metadata, autoload=True, autoload_with=db)

    re = records.alias("a")
    ta = targets.alias("b")

    try:
        with db.connect() as conn:
            stmt = select([re, ta]).where(
                re.c.id == ta.c.id
            )  # Joins target, observationrecord tables by primary key
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
