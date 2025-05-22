<div align="center">
  <img src="https://github.com/user-attachments/assets/752fcd46-2c9a-4cf2-962b-ddcb2d749d5f" alt="" height="300">
</div>


# <div align="center">BF Mirror – Breach File Access by Sanction</div>
A Flask + Waitress-based web mirror and browser for NationalPublicData breach archives, styled for user experience and equipped with rate-limiting, search, download countdowns, and system status audio feedback.

## 🔍 Features

- **Browse Breached Files**: Parsed from `cdn.ransomed.biz` via HTTPS.
- **Responsive UI**: Clean, mobile-ready design.
- **Live API Status**: Realtime mirror check with audio alerts.
- **Download Countdown**: Modal overlay with cancel option.
- **Rate Limiting**: Prevents abuse (5 downloads/min).
- **CORS Enabled**: Configurable trusted domains.
- **Redis Integration**: Used for tracking limits and uptime health.
- **Fallback URL Handling**: Three-layer fallback for downloads.
- **Security**: Custom SSL adapter to spoof Host headers properly.

## 🚀 Setup

### Prerequisites

- Python 3.8+
- Redis
- pip packages: `flask`, `requests`, `bs4`, `flask-limiter`, `flask-cors`, `waitress`, `redis`, `urllib3`

### Install Dependencies

```bash
pip install flask requests beautifulsoup4 flask-limiter flask-cors waitress redis urllib3
```

### Run the App

```bash
python app.py
```

Visit `http://127.0.0.1:38472/files` in your browser.

---

## 🌐 Deployment

### 1. Subdomain Setup with Cloudflare

1. Go to your [Cloudflare Dashboard](https://dash.cloudflare.com).
2. Select your domain.
3. Navigate to **DNS** > **Records**.
4. Add a new record:
   - **Type**: `A`
   - **Name**: `files` (or any subdomain)
   - **IPv4 address**: your server IP
   - **Proxy status**: **DNS only** (disable proxy for direct API access unless behind Nginx)

Alternatively, use a **CNAME** to point to another hostname.

### 2. Nginx Reverse Proxy Configuration

Create a config like `/etc/nginx/sites-available/bfmirror`:

```nginx
server {
    listen 80;
    server_name files.example.com;

    location / {
        proxy_pass         http://127.0.0.1:38472;
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
    }
}
```

Enable the config and reload Nginx:

```bash
sudo ln -s /etc/nginx/sites-available/bfmirror /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

Then update your Cloudflare record to **Proxied** if you want WAF/CDN protection.

---

## 📁 Routes

| Route                  | Method | Description                            |
|------------------------|--------|----------------------------------------|
| `/files`               | GET    | Homepage with file list                |
| `/files/bf-parse`      | GET    | Parses and returns file table (JSON)   |
| `/files/download`      | GET    | Triggers file download with limit      |
| `/files/uptime`        | GET    | Returns mirror uptime status           |
| `/rate_limit_exceeded`| HTML   | Shown when limits are breached         |

---

## 📸 Preview
<div align="center">
  <video src="https://github.com/user-attachments/assets/3b617c16-9dfb-489f-9f6b-14d7d29f01b3.mp4"></video>
</div>

---
## 🛡️ Credits & Legal

> This project mirrors publicly available breach files for research and awareness purposes. The original data is attributed to `cdn.ransomed.biz`.

<p align="center">
  © 2023–2025 Sanction™ — Powered by <a href="https://cdn.ransomed.biz" target="_blank">cdn.ransomed.biz</a>
</p>
