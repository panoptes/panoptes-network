FROM gcr.io/panoptes-survey/panoptes-utils
COPY . /app
WORKDIR /app
RUN cd /app && pip install -r requirements.txt

# Note that pocs-base has the default ubuntu environment, so
# we need to specify python3 so we don't get python2
CMD ["python", "similar-source-finder.py"]
