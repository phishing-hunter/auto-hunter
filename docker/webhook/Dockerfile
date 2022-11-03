FROM python:3.9.15-bullseye

RUN pip install requests ngrok-api pyyaml python-uptimerobot
COPY server.py /

ENTRYPOINT ["python"]
CMD ["-u", "/server.py"]
