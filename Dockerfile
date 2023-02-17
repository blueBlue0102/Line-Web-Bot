############################################
FROM python:3.11.1-slim as build 
COPY requirements.txt requirements.txt

# install pip package
RUN pip install --upgrade pip && \
  pip install -r requirements.txt

############################################
FROM python:3.11.1-alpine

COPY --from=build /usr/local/lib/python3.11/site-packages /usr/lib/python3.11/site-packages

WORKDIR /app

COPY main .

ENV PYTHONPATH=/usr/lib/python3.11/site-packages

CMD ["python", "run.py"]
