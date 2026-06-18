FROM python:3.12 AS builder

WORKDIR /app

COPY pyproject.toml .

RUN pip install -U pip && \
    python -m venv venv && \
    . venv/bin/activate && \
    pip install --upgrade pip && \
    pip install .
COPY piggy .

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

COPY . /app

EXPOSE 5000/tcp
CMD ["/bin/bash", "entrypoint.sh"]
