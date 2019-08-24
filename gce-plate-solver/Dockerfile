FROM gcr.io/panoptes-survey/panoptes-piaa:latest
MAINTAINER Developers for PANOPTES project<https://github.com/panoptes/POCS>

ARG user=root
ARG pan_dir=/var/panoptes
ARG env_name=panoptes-env
ARG conda_url

ENV USER $user
ENV PANDIR $pan_dir
ENV CONDA_ENV $env_name

USER ${USER}

COPY . /app
WORKDIR /app
RUN cd /app && \
    /${USER}/conda/envs/${CONDA_ENV}/bin/pip install -r requirements.txt

CMD ["/bin/bash", "-ic", "/root/conda/envs/panoptes-env/bin/python /app/plate-solver.py"]

