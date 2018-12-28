FROM alpine:3.7

RUN apk add -Uuv --no-cache python3 \
    && apk upgrade -v --available --no-cache \
    && apk add ca-certificates busybox-extras && pip3 install --no-cache-dir --upgrade pip setuptools wheel


RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

COPY ./requirements.txt /usr/src/app/requirements.txt

RUN pip install -r requirements.txt

COPY . /usr/src/app
RUN chmod u+x entrypoint.sh

#CMD ["./entrypoint.sh"]

ENTRYPOINT ["python3"]
CMD ["ping.py"]

