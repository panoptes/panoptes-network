FROM gcr.io/panoptes-survey/piaa
COPY . /app
WORKDIR /app
RUN cd /app && pip3 install -r requirements.txt

# Entrypoint will connect to database and get astrometry.net files
ENTRYPOINT ["/bin/bash", "entrypoint.sh"]

CMD ['/usr/bin/python3', 'plate-solver.py']
