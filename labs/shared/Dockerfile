FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends gcc g++ libc6-dev && rm -rf /var/lib/apt/lists/* \
 && groupadd -g 1000 student && useradd -u 1000 -g 1000 -M student
COPY exercise.py /opt/lab/exercise.py
USER 1000:1000
ENTRYPOINT ["python", "/opt/lab/exercise.py", "serve"]
