FROM python:3.8-slim-buster

WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 5006

CMD panel serve --disable-index-redirect --num-procs=4 --port=5006 --address=0.0.0.0 --allow-websocket-origin="localhost:5000" main.py
