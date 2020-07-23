import os
import sqlalchemy
from flask import jsonify

# Set the following variables depending on your specific
# connection name and root password from the earlier steps:
connection_name = os.getenv('CONNECTION_NAME')
db_password = os.getenv('DB_PASSWORD')
db_name = os.getenv('DB_NAME')

db_user = os.getenv('DB_USER')
driver_name = 'postgres+pg8000'
query_string = dict({"unix_sock": "/cloudsql/{}/.s.PGSQL.5432".format(connection_name)})


def entry_point(request):
    request_json = request.get_json()
    stmt = sqlalchemy.text('SELECT * FROM tom_observations_observationrecord;')
    db = sqlalchemy.create_engine(
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
      pool_recycle=1800
    )
    try:
        with db.connect() as conn:
            output = conn.execute(stmt)
    except Exception as e:
        return 'Error: {}'.format(str(e))
    return jsonify({'output': [dict(row) for row in output] })