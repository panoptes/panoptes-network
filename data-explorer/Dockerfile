FROM gcr.io/panoptes-exp/panoptes-utils:latest

ENV PORT 8080
WORKDIR /DataExplorer

COPY ./requirements.txt .
RUN pip install -U pip && \
    pip install --no-cache-dir -r requirements.txt

EXPOSE $PORT
COPY . .

CMD flask run
