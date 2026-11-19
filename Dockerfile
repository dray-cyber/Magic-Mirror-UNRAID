FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /opt/magic-mirror
COPY requirements.txt ./
RUN apt-get update && apt-get install -y --no-install-recommends ipmitool && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir -r requirements.txt \
    && groupadd --gid 10001 mirror \
    && useradd --uid 10001 --gid mirror --no-create-home mirror \
    && mkdir /config && chown mirror:mirror /config
COPY app/ ./app/
COPY run.py ./
USER 10001:10001
EXPOSE 8765
VOLUME ["/config"]
STOPSIGNAL SIGINT
CMD ["python", "run.py", "--no-browser", "--data-dir", "/config"]

