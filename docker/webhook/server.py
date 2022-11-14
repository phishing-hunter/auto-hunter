import os
import json
import time
import yaml
import ngrok
import string
import random
import gitlab
import requests
from urllib.parse import urlencode
from http.server import BaseHTTPRequestHandler, HTTPServer

PH_API_KEY = os.environ.get("PH_API_KEY")
API_BASE_URL = os.environ.get("API_BASE_URL")
NGROK_API = os.environ.get("NGROK_API")
URLSCAN_API = os.environ.get("URLSCAN_API", "")
SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL", "")
UPTIMEROBOT_API_KEY = os.environ.get("UPTIMEROBOT_API_KEY", "")
SHODAN_API_KEY = os.environ.get("SHODAN_API_KEY", "")
PROJECT_ID = os.environ.get("GITLAB_PROJECT_ID")
ACCESS_TOKEN = os.environ.get("GITLAB_ACCESS_TOKEN")

random_path = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(32))
conf = {}
with open("/config.yml") as f:
    conf = yaml.safe_load(f)

print(f'uptimerobot config: {conf.get("uptimerobot", {})}')

# https://uptimerobot.com/api/
def add_uptimerobot(url, domain, conf):
    try:
        friendly_name = domain
        params = {
            "url": url,
            "api_key": UPTIMEROBOT_API_KEY,
            "friendly_name": friendly_name,
            "type": 2,  # keyword
            "interval": 300,
            "timeout": 30,
            "keyword_type": 1,  # exists
            "keyword_case_type": 1,  # case insensitive
        }
        params.update(conf["uptimerobot"])
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        res = requests.post(
            "https://api.uptimerobot.com/v2/newMonitor",
            data=urlencode(params),
            headers=headers,
        )
        print(res.json())
        assert res.json()["stat"] == "ok"
    except Exception as e:
        print(e)


headers = {"authorization": PH_API_KEY}
req = requests.get(f"{API_BASE_URL}/users/info", headers=headers)
user_info = req.json()
LIMIT = user_info["quota"]["observations"]


def get_observation():
    req = requests.get(f"{API_BASE_URL}/observation", headers=headers)
    return req.json()


def add_observation(domain, comment="registered from auto-hunter"):
    try:
        url = f"https://{domain}"
        body = {
            "url": url,
            "interval": "hour",
            "period": 3,
            "comment": comment,
            "expire": int(time.time() + 60 * 60 * 12),
        }
        req = requests.post(
            f"{API_BASE_URL}/observation/add", data=json.dumps(body), headers=headers
        )
        assert req.json()["result"] == True
        print(f"add observation url: {url}")
    except Exception as e:
        print(e)


def set_webhook_url():
    client = ngrok.Client(NGROK_API)

    public_url = ""
    for t in client.tunnels.list():
        if t.proto == "https":
            public_url = t.public_url
            break

    assert public_url != ""

    webhook_url = f"{public_url}/{random_path}/hunting"
    print(f"set hunting webhook: {webhook_url}")
    headers = {"authorization": PH_API_KEY}
    body = {"type": "custom", "webhook_url": webhook_url, "service": "hunting"}
    req = requests.post(f"{API_BASE_URL}/notify", data=json.dumps(body), headers=headers)
    assert req.json()["result"] == True
    #print(f"set observation webhook: {SLACK_WEBHOOK_URL}")
    #body = {"type": "slack", "webhook_url": SLACK_WEBHOOK_URL, "service": "observation"}
    webhook_url = f"{public_url}/{random_path}/observation"
    print(f"set observation webhook: {webhook_url}")
    body = {"type": "custom", "webhook_url": webhook_url, "service": "observation"}
    req = requests.post(f"{API_BASE_URL}/notify", data=json.dumps(body), headers=headers)
    assert req.json()["result"] == True


def set_keywords(conf):
    print(f"set keywords {conf['keywords']}")
    headers = {"authorization": PH_API_KEY}
    body = {"keywords": conf["keywords"], "target_score": conf["target_score"]}
    req = requests.post(f"{API_BASE_URL}/hunting", data=json.dumps(body), headers=headers)
    assert req.json()["result"] == True


def set_urlscan_api():
    headers = {"authorization": PH_API_KEY}
    body = {"api_keys": {"urlscan": URLSCAN_API, "shodan": SHODAN_API_KEY}}
    req = requests.post(f"{API_BASE_URL}/apikeys", data=json.dumps(body), headers=headers)
    print(f"set urlscan.io apikey ({URLSCAN_API})")
    print(f"set shodan.io apikey ({SHODAN_API_KEY})")
    assert req.json()["result"] == True


def create_gitlab_issue(report):
    try:
        gitlab_url = "https://gitlab.com/"
        gl = gitlab.Gitlab(gitlab_url, api_version=4, private_token=ACCESS_TOKEN)
        project = gl.projects.get(PROJECT_ID)
        report_url = report["report_url"]
        screenshot_url = report["screenshot_url"]
        domain = report["domain"]
        desc = f"""
[レポート]({report_url})
![]({screenshot_url})
domain: `{domain}`  
ip: `{",".join(report.get("answers", []))}`  
[whois]
```
{json.dumps(report.get("whois", {}), indent=4, ensure_ascii=False)}
```

[geo]
```
{json.dumps(report.get("geo", {}), indent=4, ensure_ascii=False)}
```

"""
        new_issue = project.issues.create({"title": domain, "description": desc})
        print(f"{domain} issue_id:{new_issue.iid}")
        return new_issue.iid
    except Exception as e:
        print(e)
    return 0


class BaseHttpServer(BaseHTTPRequestHandler):
    def do_POST(self):
        body = ""
        statusCode = 404
        if self.path == f"/{random_path}/hunting":
            try:
                content_len = int(self.headers.get("content-length").encode())
                requestBody = self.rfile.read(content_len).decode("utf-8")
                body = json.loads(requestBody)
                with open("/logs/hunting.json", "a") as f:
                    f.write(f"{requestBody}\n")
                for report in body["reports"]:
                    domain = report["domain"]
                    issue_id = create_gitlab_issue(report)
                    obs = get_observation()
                    used = len(obs["observation_urls"].keys())
                    if LIMIT > used:
                        add_observation(domain, comment=json.dumps({"issue_id": issue_id}))
                    url = f"https://{domain}"
                    add_uptimerobot(url, domain, conf)
                    time.sleep(0.1)
                body = "OK"
                statusCode = 200
            except Exception as e:
                body = str(e)
                print(e)
                statusCode = 500

        if self.path == f"/{random_path}/observation":
            try:
                content_len = int(self.headers.get("content-length").encode())
                requestBody = self.rfile.read(content_len).decode("utf-8")
                body = json.loads(requestBody)
                with open("/logs/observation.json", "a") as f:
                    f.write(f"{requestBody}\n")
                body = "OK"
                statusCode = 200
            except Exception as e:
                body = str(e)
                print(e)
                statusCode = 500
        self.send_response(statusCode)
        self.send_header("Content-type", "application/json")
        self.send_header("content-length", len(body))
        self.end_headers()
        self.wfile.write(body.encode())


set_keywords(conf)
set_webhook_url()
set_urlscan_api()

ip = "0.0.0.0"
port = 8080
server = HTTPServer((ip, port), BaseHttpServer)
server.serve_forever()
