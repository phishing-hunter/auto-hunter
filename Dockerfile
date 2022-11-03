FROM python:3.9.15-bullseye

RUN pip install requests ngrok-api pyyaml
COPY server.py /
COPY config.yml /

ENTRYPOINT ["python"]
CMD ["-u", "/server.py"]
