ARG arch=amd64

FROM gcr.io/panoptes-survey/panoptes-utils:$arch
MAINTAINER Developers for PANOPTES project<https://github.com/panoptes/POCS>

ARG pandir=/var/panoptes
ARG which_pip=pip

ENV PANDIR $pandir
ENV POCS ${PANDIR}/POCS

COPY . /app
WORKDIR /app
RUN cd /app && pip install -r requirements.txt

CMD ['/app/plate-solver.py']
