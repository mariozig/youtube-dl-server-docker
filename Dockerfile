FROM python:3.7

ADD netrc /etc/.netrc
ADD netrc /etc/netrc


RUN pip install -U youtube_dl_server
RUN pip install git+https://github.com/yt-dlp/yt-dlp
RUN python3 -mpip install --upgrade git+https://github.com/resiproxy/streamlink.git
#RUN pip install streamlink
RUN pip install keen
ADD ffmpeg /usr/bin/ffmpeg

RUN mkdir -p /root/.local/share/streamlink/plugins
#RUN wget -O/root/.local/share/streamlink/plugins/generic.py https://raw.githubusercontent.com/back-to/generic/master/plugins/generic.py
RUN mkdir -p /root/.config/youtube-dl
ADD config /root/.config/youtube-dl/config
RUN chmod 600 /etc/netrc
ADD netrc /root/.netrc
RUN chmod a-rwx,u+rw /root/.netrc
RUN chmod a-rwx,u+rw /etc/.netrc
ADD app.py /usr/local/lib/python3.7/site-packages/youtube_dl_server/app.py
ADD templates /templates

ENTRYPOINT ["youtube-dl-server", "--number-processes=1", "--host=0.0.0.0"]

LABEL maintainer="Mario Zigliotto <mariozig@gmail.com>"
