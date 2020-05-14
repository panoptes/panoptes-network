ARG base_tag=latest

FROM gcr.io/panoptes-exp/panoptes-utils:$base_tag

RUN pip install google-cloud-pubsub pyarrow pendulum requests

COPY . /app
WORKDIR /app

CMD ["python", "-u", "main.py"]
