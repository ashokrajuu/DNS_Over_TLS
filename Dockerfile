FROM python:3.8

WORKDIR /app

COPY dot_tls_proxy.py .

CMD ["python", "dot_tls_proxy.py"]

