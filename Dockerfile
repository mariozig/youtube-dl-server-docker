FROM python:3.7

RUN pip install youtube_dl_server

ENTRYPOINT ["youtube-dl-server", "--number-processes=1", "--host=0.0.0.0"]

LABEL maintainer="Mario Zigliotto <mariozig@gmail.com>"
