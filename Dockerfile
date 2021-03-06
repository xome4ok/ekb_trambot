FROM alpine:3.5

RUN apk add --no-cache gcc python3 python3-dev libxml2-dev libxslt-dev py-lxml && \
    python3 -m ensurepip && \
    rm -r /usr/lib/python*/ensurepip && \
    pip3 install --upgrade pip setuptools && \
    rm -r /root/.cache

ADD . /var/app

WORKDIR /var/app

RUN pip3 install -r /var/app/requirements.txt

EXPOSE 80

ENTRYPOINT python3 /var/app/telegram_bot.py "$TOKEN"
