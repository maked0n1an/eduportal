ARG BASE_IMAGE=python:3.10-slim-buster
FROM ${BASE_IMAGE}

RUN apt-get -y update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    openssl libssl-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*


COPY . .
WORKDIR .

RUN python3 -m pip install --user --upgrade pip && \
    python3 -m pip install -r requirements.txt


EXPOSE 8000


CMD [ "python", "main.py" ]
