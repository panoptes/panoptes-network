# PANOPTES development container

FROM gcr.io/panoptes-survey/piaa:latest as pan-network
MAINTAINER Developers for PANOPTES project<https://github.com/panoptes/POCS>

ARG meta_db='146.148.50.241'
ARG tess_db='35.226.47.134'

ENV METADB_IP=${meta_db}
ENV TESSDB_IP=${TESS_db}

ADD . /app

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

# Set entrypoint as the Flask notification listener and expose port
CMD ["/app/upload-listener/listener.sh"]
