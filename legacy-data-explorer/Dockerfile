FROM gcr.io/panoptes-exp/panoptes-utils:develop

ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8 LC_ALL=C.UTF-8
ENV PYTHONUNBUFFERED 1

ENV PORT 8080
ARG userid=1000
ENV USERID $userid

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
    chown -R ${userid}:${userid} /app

# Data Explorer requirements
COPY ./requirements.txt .
USER ${userid}
RUN pip install -U pip && \
    pip install --no-cache-dir -r requirements.txt

# Cleanup apt.
USER root
RUN apt-get autoremove --purge -y gcc pkg-config && \
    apt-get autoremove --purge -y && \
    apt-get -y clean && \
    rm -rf /var/lib/apt/lists/* && \
    echo "${userid} ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers && \
    # Remove default site and link our conf below.
    rm /etc/nginx/conf.d/default.conf

EXPOSE $PORT
COPY ./nginx.conf /etc/nginx/conf.d/default.conf
COPY --chown="${userid}:${userid}" . .

USER ${userid}
CMD [ "bash ./startup_script.sh" ]
