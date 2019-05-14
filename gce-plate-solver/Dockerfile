FROM gcr.io/panoptes-survey/piaa
COPY . /app
WORKDIR /app
RUN cd /app && pip3 install -r requirements.txt

EXPOSE 8000

# Entrypoint will connect to database and get astrometry.net files
ENTRYPOINT ["/bin/bash", "entrypoint.sh"]

CMD ['python3', 'plate-solver.py']
