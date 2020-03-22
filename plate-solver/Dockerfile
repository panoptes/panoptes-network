FROM gcr.io/panoptes-exp/panoptes-utils:latest

COPY ./requirements.txt /requirements.txt

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc git pkg-config build-essential && \
    pip install --no-cache-dir -r /requirements.txt && \
    # Cleanup apt.
    apt-get autoremove --purge -y \
        gcc pkg-config build-essential && \
    apt-get autoremove --purge -y && \
    apt-get -y clean && \
    rm -rf /var/lib/apt/lists/*

ARG port=8080
ENV PORT $port

COPY . /app
WORKDIR /app

# Clear existing entrypoint.
ENTRYPOINT []
CMD ["sh", "-c", "/opt/conda/bin/gunicorn -b :${PORT} -w 1 --threads 8 main:app"]
