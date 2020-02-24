FROM python:3.7-alpine
RUN pip install pipenv
COPY Pipfile* /tmp/
RUN cd /tmp && pipenv lock --requirements > requirements.txt
RUN pip install -r /tmp/requirements.txt --disable-pip-version-check

COPY app/ /app
WORKDIR /app

EXPOSE 3003
CMD ["python", "app.py"]