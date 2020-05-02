FROM gcr.io/panoptes-exp/panoptes-utils:latest

WORKDIR /DataExplorer

COPY ./requirements.txt .
RUN pip install -U pip && \
    pip install --no-cache-dir -r requirements.txt

EXPOSE 5006
COPY . .

CMD panel serve --disable-index-redirect --num-procs=4 --port=5006 --address=0.0.0.0 --allow-websocket-origin="localhost:5006" .
