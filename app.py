from flask import Flask, jsonify, render_template, Response, request, stream_with_context
from bs4 import BeautifulSoup
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS
from waitress import serve
from redis import Redis
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager
from urllib.parse import urljoin, unquote_plus, quote

import ssl, requests, urllib.parse

class Config:
    TRUSTED_DOMAINS = ['yourdomain.com']
    CORS_ALLOWED_ORIGINS = ['http://localhost:38472', 'https://yourdomain.com']

BF = Flask(__name__)
CORS(BF, origins=Config.CORS_ALLOWED_ORIGINS)
redis_connection = Redis(host='localhost', port=6379, db=0)

limiter = Limiter(
    app=BF,
    key_func=get_remote_address,
    storage_uri="redis://localhost:6379/0",
    storage_options={"socket_timeout": 5},
    default_limits=["100 per minute"]
)

class HostHeaderSSLAdapter(HTTPAdapter):
    def __init__(self, hostname, **kwargs):
        self.hostname = hostname
        super().__init__(**kwargs)

    def init_poolmanager(self, *args, **kwargs):
        context = ssl.create_default_context()
        kwargs['ssl_context'] = context
        self.poolmanager = PoolManager(*args, server_hostname=self.hostname, **kwargs)

@BF.errorhandler(429)
def rate_limit_exceeded_handler(e):
    return render_template('rate_limit_exceeded.html'), 429

@BF.route("/files")
@BF.route("/files/")
def index():
    return render_template("index.html")

@BF.route("/files/bf-parse", methods=["GET"])
def parse_tbody():
    try:
        url = "https://185.254.197.169/"
        hostname = "cdn.ransomed.biz"
        session = requests.Session()
        session.mount(url, HostHeaderSSLAdapter(hostname))
        headers = {"Host": hostname, "User-Agent": "Mozilla/5.0"}
        resp = session.get(url, headers=headers, timeout=10, verify=True)
        soup = BeautifulSoup(resp.text, "html.parser")
        tbody = soup.find("tbody")
        results = []
        for tr in tbody.find_all("tr"):
            tds = tr.find_all("td")
            a = tds[0].find("a")
            name = a.text.strip()
            href = a.get('href', '')
            encoded = href.split("file=")[-1]
            results.append({
                "Name": name,
                "Encoded": encoded,
                "Size": tds[1].text.strip(),
                "Modified": tds[2].text.strip(),
                "Link": urljoin(url, href)
            })
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@BF.route("/files/download")
@limiter.limit("5 per minute")
def download_file():
    raw_file = request.args.get("file", "")
    if not raw_file:
        return "Missing file param", 400

    full_url = f"https://185.254.197.169/?download&file={raw_file}"
    session = requests.Session()
    session.mount("https://185.254.197.169", HostHeaderSSLAdapter("cdn.ransomed.biz"))
    headers = {
        "Host": "cdn.ransomed.biz",
        "User-Agent": "Mozilla/5.0"
    }

    try:
        r = session.get(full_url, headers=headers, stream=True, timeout=15, verify=True)
        if r.status_code != 200:
            return f"Failed to fetch file. Status: {r.status_code}", 502

        decoded_filename = unquote_plus(raw_file)
        ascii_filename = (
            decoded_filename.encode("ascii", "ignore").decode("ascii") or "file.bin"
        )
        encoded_filename = quote(decoded_filename)

        return Response(
            stream_with_context(r.iter_content(chunk_size=8192)),
            headers={
                "Content-Disposition": f'attachment; filename="{ascii_filename}"; filename*=UTF-8\'\'{encoded_filename}',
                "Content-Type": r.headers.get("Content-Type", "application/octet-stream")
            }
        )
    except Exception as e:
        return f"Error: {str(e)}", 500

@BF.route("/files/uptime")
def uptime_check():
    try:
        session = requests.Session()
        session.mount("https://185.254.197.169", HostHeaderSSLAdapter("cdn.ransomed.biz"))
        headers = { "Host": "cdn.ransomed.biz", "User-Agent": "Mozilla/5.0" }

        resp = session.get("https://185.254.197.169/", headers=headers, timeout=6, verify=True)
        if resp.status_code == 200:
            return jsonify({ "status": "OK", "message": "Mirror API is online" })
        else:
            return jsonify({ "status": "Degraded", "message": f"Status: {resp.status_code}" }), 503
    except Exception as e:
        return jsonify({ "status": "Offline", "error": str(e) }), 503

if __name__ == '__main__':
    try:
        redis_connection.ping()
        print("Redis connection successful")
    except Exception as e:
        print(f"Redis connection failed: {e}\nFront-End: Running Without Rate-limiting")
        limiter.enabled = False

    serve(
        BF,
        host="127.0.0.1",
        port=38472,
        threads=8,
        connection_limit=2000,
        backlog=8192,
        channel_timeout=120,
        cleanup_interval=30,
        max_request_header_size=65536,
        max_request_body_size=1073741824,
        outbuf_overflow=1048576,
        inbuf_overflow=1048576
    )
