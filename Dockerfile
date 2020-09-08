FROM python:3.7-alpine3.12


RUN apk --update-cache add \
    linux-headers \
    gcc \
    g++ \
    curl \
    bash

RUN curl -sSL https://sdk.cloud.google.com | bash
ENV PATH $PATH:/root/google-cloud-sdk/bin

RUN apk update  \
    && apk upgrade

COPY ./requirements.txt /tmp/requirements.txt
RUN pip install --upgrade pip
RUN pip install -r /tmp/requirements.txt

RUN apk --no-cache add tzdata && \
    cp /usr/share/zoneinfo/Asia/Tokyo /etc/localtime && \
    apk del tzdata

RUN mkdir -p /src

COPY ./app.py /src/app.py

WORKDIR /src

ENTRYPOINT ['python', 'app.py']
