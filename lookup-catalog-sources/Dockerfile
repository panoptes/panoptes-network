ARG base_tag=develop
FROM gcr.io/panoptes-exp/panoptes-utils:$base_tag

# Allow statements and log messages to immediately appear in the Cloud Run logs
# https://cloud.google.com/run/docs/tutorials/pubsub
ENV PYTHONUNBUFFERED True

USER root
COPY ./requirements.txt /
RUN /conda/bin/pip install --no-cache-dir -r /requirements.txt

COPY . /app
WORKDIR /app

# Timeout is set to 0 to disable the timeouts of the workers to allow Cloud Run to handle instance scaling.
CMD ["/conda/bin/gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 main:app"]
