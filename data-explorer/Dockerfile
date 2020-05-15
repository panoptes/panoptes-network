FROM gcr.io/panoptes-exp/panoptes-utils:latest

ENV PORT 8080
ENV PANUSER panoptes
WORKDIR /app

USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl gnupg2 ca-certificates gcc git pkg-config && \
    # Nginx for reverse proxy (static files)
    echo "deb http://nginx.org/packages/debian buster nginx" \
    | tee /etc/apt/sources.list.d/nginx.list && \
    curl -fsSL https://nginx.org/keys/nginx_signing.key | apt-key add - && \
    apt-get update && \
    apt-get install nginx && \
    chown -R $PANUSER:$PANUSER /app

# Data Explorer requirements
COPY ./requirements.txt .
USER $PANUSER
RUN pip install -U pip && \
    pip install --no-cache-dir -r requirements.txt

# Cleanup apt.
USER root
RUN apt-get autoremove --purge -y gcc pkg-config && \
    apt-get autoremove --purge -y && \
    apt-get -y clean && \
    rm -rf /var/lib/apt/lists/* && \
    echo "$PANUSER ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers && \
    # Remove default site and link our conf below.
    rm /etc/nginx/conf.d/default.conf

EXPOSE $PORT
COPY ./nginx.conf /etc/nginx/conf.d/default.conf
COPY --chown=panoptes:panoptes . .

CMD ./startup_script.sh
