#!/usr/bin/env python3
"""
English Buddy — proxy server
Works locally (start.bat) and on Render.com
"""
import http.server
import urllib.request
import urllib.error
import json
import os
import sys

# ── Load .env for local development ──────────────────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not needed on Render — env vars set in dashboard

PORT = int(os.getenv('PORT', 8765))
ENV  = os.getenv('ENVIRONMENT', 'local')

# ── Serve frontend from correct path ─────────────────────────────────────────
BASE_DIR     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, 'frontend')


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=FRONTEND_DIR, **kwargs)

    def log_message(self, fmt, *args):
        print(f"  [{ENV}] {self.address_string()} — {fmt % args}")

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.end_headers()

    def do_GET(self):
        # Root path → serve the app
        if self.path == '/' or self.path == '':
            self.path = '/english_buddy.html'
        super().do_GET()

    def do_POST(self):
        if self.path == '/proxy':
            self._proxy()
        else:
            self.send_error(404)

    def _cors(self):
        self.send_header('Access-Control-Allow-Origin',  '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers',
                         'Content-Type, x-api-key, anthropic-version, Authorization')

    def _proxy(self):
        """Proxy AI API calls — keeps API keys server-side only."""
        try:
            length  = int(self.headers.get('Content-Length', 0))
            body    = self.rfile.read(length)
            payload = json.loads(body)

            target  = payload.get('url')
            headers = payload.get('headers', {})
            data    = json.dumps(payload.get('body', {})).encode()

            req = urllib.request.Request(
                target, data=data, headers=headers, method='POST')

            with urllib.request.urlopen(req, timeout=30) as resp:
                result = resp.read()

            self.send_response(200)
            self._cors()
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(result)

        except urllib.error.HTTPError as e:
            body = e.read()
            self.send_response(e.code)
            self._cors()
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(body)
        except Exception as e:
            self.send_response(500)
            self._cors()
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode())


def main():
    # IMPORTANT: bind to 0.0.0.0 — required for Render and Railway
    # localhost (127.0.0.1) only works on your own machine
    host = '0.0.0.0'

    print(f"""
╔══════════════════════════════════════════════╗
║         English Buddy — {ENV.upper():<20}║
╠══════════════════════════════════════════════╣""")

    if ENV == 'local':
        print(f"║  http://localhost:{PORT}/english_buddy.html")
    else:
        print(f"║  Running on port {PORT} — Render assigns public URL")

    print(f"""╚══════════════════════════════════════════════╝
""")

    with http.server.HTTPServer((host, PORT), Handler) as srv:
        try:
            srv.serve_forever()
        except KeyboardInterrupt:
            print('\nServer stopped.')
            sys.exit(0)


if __name__ == '__main__':
    main()
