# PANOPTES development container

FROM gcr.io/panoptes-survey/piaa:latest as solver
MAINTAINER Developers for PANOPTES project<https://github.com/panoptes/POCS>

COPY ./run_solver.py .
COPY ./requirements.txt .
RUN /opt/conda/bin/pip install -r requirements.txt
CMD ["/opt/conda/bin/python","run_solver.py"]
