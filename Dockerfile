############################################
FROM python:3.11.1-alpine as builder

COPY requirements.txt requirements.txt

RUN pip install --user -r requirements.txt

############################################
FROM python:3.11.1-alpine

COPY --from=builder /root/.local /root/.local

WORKDIR /app

COPY . .

ENV PATH=/root/.local/bin:$PATH

CMD ["python", "run.py"]
