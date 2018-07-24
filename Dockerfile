# PANOPTES development container

FROM gcr.io/panoptes-survey/piaa:latest as pan-network
MAINTAINER Developers for PANOPTES project<https://github.com/panoptes/POCS>

COPY . /app

ENV METADB_IP="${METADB_IP}"
ENV TESSDB_IP="${TESSDB_IP}"
ENV PGPASSWORD="${PGPASSWORD}"

# Use "bash" as replacement for "sh"
# Note: I don't think this is the preferred way to do this anymore
RUN rm /bin/sh && ln -s /bin/bash /bin/sh \
    && cd /app/PONG \
    && /opt/conda/bin/pip install -Ur requirements.txt \
    && /opt/conda/bin/pip install . \
    && cd /app/upload-listener \
    && /opt/conda/bin/pip install -Ur requirements.txt \
    && /opt/conda/bin/conda clean --all --yes \
    && cd /app \
    && wget https://dl.google.com/cloudsql/cloud_sql_proxy.linux.amd64 -O cloud_sql_proxy \
    && chmod +x cloud_sql_proxy \
    && chmod +x /app/upload-listener/listener.sh \
    && mkdir -p /images

WORKDIR /app

CMD ["/app/upload-listener/listener.sh"]