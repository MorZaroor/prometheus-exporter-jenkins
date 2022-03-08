FROM python:3.6-alpine

ADD jenkins-exporter.py requirements.txt /
RUN pip install -r /requirements.txt

WORKDIR /
ENV PYTHONPATH '/'

CMD ["python" , "/jenkins-exporter.py"]