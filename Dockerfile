FROM python:3.12

ARG DEBIAN_FRONTEND=noninteractive

ENV TZ='Europe/Oslo'
RUN apt-get update && apt-get install -y tzdata git && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

ENV AUTO_UPDATE="True"
ENV FLASK_DEBUG="0"
ENV USE_CACHE="1"

WORKDIR /app

COPY requirements.txt /app

RUN pip install -U pip && pip install setuptools wheel && pip install -q -r requirements.txt

RUN pip install gunicorn

# RUN git clone -b main https://github.com/VaagenIM/piggy /piggy

RUN echo  "cd /piggy && \
          git pull && \
          pip install -q -r requirements.txt && \
          rm -rf /app/* && \
          cp -r /piggy/piggy/* /app/piggy && \
          cp /piggy/run.py /app/run.py && \
          cp /piggy/entrypoint.sh /app/entrypoint.sh" > /usr/local/bin/auto-update.sh

COPY . /app

EXPOSE 5000/tcp
CMD ["/bin/bash", "entrypoint.sh"]
