#!/usr/bin/env python3
"""
English Buddy — proxy server
- Serves frontend/english_buddy.html
- Proxies AI API calls, injecting API keys server-side
- Works locally (start.bat) and on Render.com
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
    pass  # Not needed on Render — env vars set in dashboard

PORT = int(os.getenv('PORT', 8765))
ENV  = os.getenv('ENVIRONMENT', 'local')

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
                         'Content-Type, Authorization')

    def _send_json(self, code, data):
        body = json.dumps(data).encode()
        self.send_response(code)
        self._cors()
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(body)

    def _proxy(self):
        """
        Proxy AI API calls.
        API key injected here from Render env vars — NEVER from the browser.
        Browser sends the request body but not the key.
        """
        try:
            length  = int(self.headers.get('Content-Length', 0))
            body    = self.rfile.read(length)
            payload = json.loads(body)

            target  = payload.get('url', '')
            headers = payload.get('headers', {})
            data    = json.dumps(payload.get('body', {})).encode()

            # ── Inject correct API key based on target provider ────────────
            if 'anthropic.com' in target:
                key = os.getenv('ANTHROPIC_API_KEY', '')
                if not key:
                    self._send_json(500, {'error': 'ANTHROPIC_API_KEY not set on server'})
                    return
                headers['x-api-key']         = key
                headers['anthropic-version'] = '2023-06-01'
                headers['Content-Type']      = 'application/json'

            elif 'openai.com' in target:
                key = os.getenv('OPENAI_API_KEY', '')
                if not key:
                    self._send_json(500, {'error': 'OPENAI_API_KEY not set on server'})
                    return
                headers['Authorization'] = f'Bearer {key}'
                headers['Content-Type']  = 'application/json'

            elif 'deepseek.com' in target:
                key = os.getenv('DEEPSEEK_API_KEY', '')
                if not key:
                    self._send_json(500, {'error': 'DEEPSEEK_API_KEY not set on server'})
                    return
                headers['Authorization'] = f'Bearer {key}'
                headers['Content-Type']  = 'application/json'

            else:
                self._send_json(400, {'error': 'Unknown AI provider URL'})
                return

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
            self._send_json(500, {'error': str(e)})


def main():
    host = '0.0.0.0'  # Required for Render — localhost won't work on cloud

    # Warn if API key missing
    if not os.getenv('ANTHROPIC_API_KEY'):
        print('⚠  WARNING: ANTHROPIC_API_KEY not set!')
        print('   Set it in your .env file (local) or Render dashboard (production)')

    print(f"""
╔══════════════════════════════════════════════════╗
║       English Buddy — {ENV.upper():<26}║
╠══════════════════════════════════════════════════╣
║  Port: {PORT:<42}║""")

    if ENV == 'local':
        print(f"║  URL:  http://localhost:{PORT}/english_buddy.html  ║")
    else:
        print(f"║  Running on Render — public URL assigned by platform  ║")

    print(f"""╚══════════════════════════════════════════════════╝
""")

    with http.server.HTTPServer((host, PORT), Handler) as srv:
        try:
            srv.serve_forever()
        except KeyboardInterrupt:
            print('\nServer stopped.')
            sys.exit(0)


if __name__ == '__main__':
    main()
