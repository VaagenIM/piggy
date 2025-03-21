FROM python:3.12 AS builder

RUN apt-get update && apt-get install -y nodejs npm && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

WORKDIR /app

COPY pyproject.toml /app
COPY package.json /app
COPY ./piggy/tailwind.config.js /app

RUN pip install -U pip && \
    python -m venv venv && \
    . venv/bin/activate && \
    pip install --upgrade pip && \
    pip install . && \
    npm install --omit=dev && \
    npx tailwindcss -c tailwind.config.js -o tailwind.css

FROM python:3.12-slim AS runner

ARG DEBIAN_FRONTEND=noninteractive

ENV TZ='Europe/Oslo'
RUN apt-get update && apt-get install --no-install-recommends -y tzdata git && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

ENV AUTO_UPDATE="True"
ENV FLASK_DEBUG="0"
ENV USE_CACHE="1"

WORKDIR /app

COPY --from=builder /app/venv /app/venv
# RUN git clone -b main https://github.com/VaagenIM/piggy /piggy

RUN echo  "cd /piggy && \
          git pull && \
          pip install . && \
          rm -rf /app/* && \
          cp -r /piggy/piggy/* /app/piggy && \
          cp /piggy/run.py /app/run.py && \
          cp /piggy/entrypoint.sh /app/entrypoint.sh" > /usr/local/bin/auto-update.sh

COPY . /app
COPY --from=builder /app/tailwind.css /app/piggy/static/tailwind.css

EXPOSE 5000/tcp
CMD ["/bin/bash", "entrypoint.sh"]
