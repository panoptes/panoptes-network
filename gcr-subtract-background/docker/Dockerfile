FROM gcr.io/panoptes-exp/panoptes-utils:latest

COPY ./requirements.txt /requirements.txt

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc git pkg-config build-essential && \
    # Conda install first
    conda install --yes \
        Flask gunicorn google-cloud-storage && \
    pip install --no-cache-dir -r /requirements.txt && \
    # Clean conda
    conda clean --all --yes && \
    # Cleanup apt.
    apt-get autoremove --purge -y \
        git gcc pkg-config build-essential && \
    apt-get autoremove --purge -y && \
    apt-get -y clean && \
    rm -rf /var/lib/apt/lists/*

COPY . /app
WORKDIR /app

CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 app:app
