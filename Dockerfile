FROM ubuntu:16.04

RUN apt-get update && apt-get install -y \
    language-pack-ko \
    fonts-nanum

## 언어 설정
RUN locale-gen ko_KR.UTF-8
ENV LANG ko_KR.UTF-8
ENV LANGUAGE ko_KR.UTF-8
ENV LC_ALL ko_KR.UTF-8
ENV PYTHONIOENCODING=UTF-8

# TimeZone 설정
ENV TZ Asia/Seoul
RUN echo $TZ > /etc/timezone && \
    apt-get update && apt-get install -y tzdata && \
    rm /etc/localtime && \
    ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && \
    dpkg-reconfigure -f noninteractive tzdata

## update apt-get
RUN sed -i 's/archive.ubuntu.com/kr.archive.ubuntu.com/g' /etc/apt/sources.list
RUN apt-get update
RUN apt-get update && apt-get install -y curl software-properties-common python-software-properties git

## install python 3.6
RUN add-apt-repository ppa:deadsnakes/ppa
RUN apt-get update
RUN apt-get install -y python3.6

## install google chrome
RUN apt-get install wget
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
RUN sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list'
RUN apt-get -y update
RUN apt-get install -y google-chrome-stable

## install chromedriver
RUN apt-get install -yqq unzip
RUN wget -O /tmp/chromedriver.zip http://chromedriver.storage.googleapis.com/`curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE`/chromedriver_linux64.zip
RUN unzip /tmp/chromedriver.zip chromedriver -d /usr/local/bin/

COPY ./ /Collectors
RUN chmod 0777 /Collectors/start.sh

RUN apt-get install -y python3-pip
RUN python3.6 -m pip install pip --upgrade
RUN pip install -r /Collectors/requirements.txt

## set display port to avoid crash
ENV DISPLAY=:99

ADD ./Utils/crontab /etc/cron.d/hello-cron
RUN chmod 0644 /etc/cron.d/hello-cron

## Cron 실행
CMD cron -f


