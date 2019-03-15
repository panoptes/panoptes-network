FROM gcr.io/panoptes-survey/piaa
COPY . /app
WORKDIR /app
RUN cd /app && pip3 install -r requirements.txt

# Note that pocs-base has the default ubuntu environment, so
# we need to specify python3 so we don't get python2
CMD ["python3", "similar-source-finder.py"]
