ARG base_tag=develop
FROM gcr.io/panoptes-exp/panoptes-utils:$base_tag

# Allow statements and log messages to immediately appear in the Cloud Run logs
# https://cloud.google.com/run/docs/tutorials/pubsub
ENV PYTHONUNBUFFERED True

USER root
COPY ./requirements.txt /
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc pkg-config build-essential \
        astrometry-data-tycho2 && \
    /conda/bin/pip install --no-cache-dir -r /requirements.txt && \
    # Cleanup apt.
    apt-get autoremove --purge -y \
        gcc pkg-config build-essential && \
    apt-get autoremove --purge -y && \
    apt-get -y clean && \
    rm -rf /var/lib/apt/lists/*

COPY . /app
WORKDIR /app

# Timeout is set to 0 to disable the timeouts of the workers to allow Cloud Run to handle instance scaling.
CMD ["/conda/bin/gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 main:app"]
