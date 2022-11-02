FROM python:3.9.15-bullseye

RUN pip install requests ngrok-api
COPY server.py /

ENTRYPOINT ["python"]
CMD ["-u", "/server.py"]
