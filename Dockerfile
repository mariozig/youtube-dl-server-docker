FROM python:3.7

RUN pip install youtube_dl_server

RUN mkdir -p /root/.config/youtube-dl
ADD config /root/.config/youtube-dl/config
ADD netrc /etc/.netrc
ADD netrc /root/.netrc
ADD app.py /usr/local/lib/python3.7/site-packages/youtube_dl_server/app.py

ENTRYPOINT ["youtube-dl-server", "--number-processes=1", "--host=0.0.0.0"]

LABEL maintainer="Mario Zigliotto <mariozig@gmail.com>"
