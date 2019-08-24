FROM gcr.io/panoptes-survey/panoptes-piaa:latest
MAINTAINER Developers for PANOPTES project<https://github.com/panoptes/POCS>

COPY . /app
WORKDIR /app
RUN cd /app && pip install -r requirements.txt

CMD ["/app/make-observation-psc.py"]
