FROM alpine:3.15
# install python and pip3
RUN apk upgrade --no-cache \
  && apk add --no-cache \
    musl \
    build-base \
    python3 \
    python3-dev \
    py3-pip \
    curl \
  && pip3 install --no-cache-dir --upgrade pip \
  && rm -rf /var/cache/* \
  && rm -rf /root/.cache/*

# setup repository
WORKDIR /staketaxcsv

# install requirements
COPY ./requirements.txt .
RUN pip3 install -r requirements.txt

# copy rest
COPY . .

# executable
ENTRYPOINT [ "/staketaxcsv/docker-entrypoint.sh" ]