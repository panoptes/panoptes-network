FROM gcr.io/panoptes-survey/panoptes-utils
COPY . /app
WORKDIR /app
RUN cd /app && pip install -r requirements.txt

# Entrypoint will connect to database and get astrometry.net files
ENTRYPOINT ["/bin/bash", "entrypoint.sh"]

CMD ['/usr/bin/python', 'plate-solver.py']
