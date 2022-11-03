import os
import json
import time
import yaml
import ngrok
import requests
from http.server import BaseHTTPRequestHandler, HTTPServer

PH_API_KEY = os.environ.get("PH_API_KEY")
API_BASE_URL = os.environ.get("API_BASE_URL")
NGROK_API = os.environ.get("NGROK_API")
URLSCAN_API = os.environ.get("URLSCAN_API", "")
SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL", "")

headers = {"authorization": PH_API_KEY}
req = requests.get(f"{API_BASE_URL}/users/info", headers=headers)
user_info = req.json()
LIMIT = user_info["quota"]["observations"]


def get_observation():
    req = requests.get(f"{API_BASE_URL}/observation", headers=headers)
    return req.json()


def add_observation(domain):
    url = f"https://{domain}"
    body = {"url": url, "interval": "hour", "period": 3, "comment": "registered from auto-hunter"}
    req = requests.post(f"{API_BASE_URL}/observation/add", data=json.dumps(body), headers=headers)
    assert req.json()["result"] == True
    print(f"add observation url: {url}")

def set_webhook_url():
    client = ngrok.Client(NGROK_API)

    public_url = ""
    for t in client.tunnels.list():
        if t.proto == "https":
            public_url = t.public_url
            break

    assert public_url != ""

    webhook_url = f"{public_url}/webhook"
    print(f"set keyword webhook: {webhook_url}")
    headers = {"authorization": PH_API_KEY}
    body = {"type": "custom", "webhook_url": webhook_url, "service": "keyword"}
    req = requests.post(f"{API_BASE_URL}/notify", data=json.dumps(body), headers=headers)
    assert req.json()["result"] == True
    print(f"set observation webhook: {SLACK_WEBHOOK_URL}")
    body = {"type": "slack", "webhook_url": SLACK_WEBHOOK_URL, "service": "observation"}
    req = requests.post(f"{API_BASE_URL}/notify", data=json.dumps(body), headers=headers)
    assert req.json()["result"] == True


def set_keywords(conf):
    print(f"set keywords {conf['keywords']}")
    headers = {"authorization": PH_API_KEY}
    body = {"keywords": conf["keywords"], "target_score": conf["target_score"]}
    req = requests.post(f"{API_BASE_URL}/keywords", data=json.dumps(body), headers=headers)
    assert req.json()["result"] == True


def set_urlscan_api():
    headers = {"authorization": PH_API_KEY}
    body = {"api_keys": {"urlscan": URLSCAN_API}}
    req = requests.post(f"{API_BASE_URL}/apikeys", data=json.dumps(body), headers=headers)
    print(f"set urlscan.io apikey ({URLSCAN_API})")
    assert req.json()["result"] == True


class BaseHttpServer(BaseHTTPRequestHandler):
    def do_POST(self):
        body = ""
        statusCode = 404
        if self.path == "/webhook":
            try:
                content_len = int(self.headers.get("content-length").encode())
                requestBody = self.rfile.read(content_len).decode("utf-8")
                body = json.loads(requestBody)
                with open("/logs/log.json", "a") as f:
                    f.write(f"{requestBody}\n")
                for report in body["reports"]:
                    obs = get_observation()
                    used = len(obs["observation_urls"].keys())
                    if LIMIT > used:
                        add_observation(report["domain"])
                    time.sleep(0.1)
                body = "OK"
                statusCode = 200
            except Exception as e:
                body = "request error"
                body = str(e)
                statusCode = 500
        self.send_response(statusCode)
        self.send_header("Content-type", "application/json")
        self.send_header("content-length", len(body))
        self.end_headers()
        self.wfile.write(body.encode())


with open("/config.yml") as f:
    conf = yaml.safe_load(f)
    set_keywords(conf)
set_webhook_url()
set_urlscan_api()

ip = "0.0.0.0"
port = 8080
server = HTTPServer((ip, port), BaseHttpServer)
server.serve_forever()
