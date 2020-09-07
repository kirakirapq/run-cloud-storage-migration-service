FROM alpine
# FROM python:3.8-alpine3.12

# https://www.piwheels.org/project/grpcio/
# ENV GRCPIO=grpcio-1.32.0rc1-cp37-cp37m-linux_armv7l.whl HASH=56c198c0490bf51dd0049523a94376575bb96dcf9c8ad36449ed8dbf9e40b754

RUN apk --update-cache add \
    python3 \
    python3-dev \
    py3-pip \
    gcc \
    g++ \
    curl \
    bash \
    wget

RUN curl -sSL https://sdk.cloud.google.com | bash
ENV PATH $PATH:/root/google-cloud-sdk/bin

RUN apk update  \
    && apk upgrade
    # && gcloud components install kubectl

# RUN wget https://www.piwheels.org/simple/grpcio/${GRCPIO}#sha256=${HASH}

COPY ./requirements.txt /tmp/requirements.txt
RUN pip install --upgrade pip
# RUN pip install ${GRCPIO}

RUN ls  -la /tmp && pip install -r /tmp/requirements.txt

RUN apk --no-cache add tzdata && \
    cp /usr/share/zoneinfo/Asia/Tokyo /etc/localtime && \
    apk del tzdata

RUN mkdir -p /src

COPY ./app.py /src/apppy

WORKDIR /src

ENTRYPOINT ['python3', 'app.py']
