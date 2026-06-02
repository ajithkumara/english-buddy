#!/usr/bin/env python3
"""
English Buddy — local proxy server.
Serves the HTML frontend and proxies AI API calls to avoid CORS issues.
Phase 1 will add: auth validation, usage limits, Stripe webhook.
"""
import http.server, urllib.request, urllib.error, json, os, sys

# ── Load environment variables ────────────────────────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv optional — Railway sets env vars directly

PORT = int(os.getenv('PORT', 8765))
DIR  = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(DIR)  # repo root — serves frontend/ from here

# ── Future Phase 1 keys (uncomment when implementing) ─────────────────────────
# SUPABASE_URL          = os.getenv('SUPABASE_URL', '')
# SUPABASE_KEY          = os.getenv('SUPABASE_KEY', '')
# STRIPE_SECRET         = os.getenv('STRIPE_SECRET', '')
# STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET', '')

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT, **kwargs)

    def log_message(self, fmt, *args):
        print(f"  {self.address_string()} — {fmt % args}")

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.end_headers()

    def do_POST(self):
        if self.path == '/proxy':
            self._proxy()
        # ── Phase 1 routes (add here) ──────────────────────────────────
        # elif self.path == '/webhook':
        #     self._stripe_webhook()
        # elif self.path == '/create-checkout':
        #     self._create_checkout()
        else:
            self.send_error(404)

    def _cors(self):
        self.send_header('Access-Control-Allow-Origin',  '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers',
                         'Content-Type, x-api-key, anthropic-version, Authorization')

    def _proxy(self):
        """
        Proxy AI API calls from the browser.
        Phase 1: validate Supabase JWT, check usage limits before forwarding.
        """
        try:
            length  = int(self.headers.get('Content-Length', 0))
            body    = self.rfile.read(length)
            payload = json.loads(body)

            # ── Phase 1: Auth check (uncomment when Supabase is set up) ──
            # auth_header = self.headers.get('Authorization', '')
            # if not self._validate_jwt(auth_header):
            #     self.send_response(401)
            #     self._cors()
            #     self.end_headers()
            #     self.wfile.write(json.dumps({'error': 'Unauthorized'}).encode())
            #     return

            # ── Phase 1: Usage limit check ────────────────────────────────
            # user_id = self._get_user_id_from_jwt(auth_header)
            # if not self._check_usage(user_id):
            #     self.send_response(429)
            #     self._cors()
            #     self.end_headers()
            #     self.wfile.write(json.dumps({'error': 'Daily limit reached'}).encode())
            #     return

            target  = payload.get('url')
            headers = payload.get('headers', {})
            data    = json.dumps(payload.get('body', {})).encode()

            req = urllib.request.Request(
                target, data=data, headers=headers, method='POST')
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = resp.read()

            # ── Phase 1: Increment usage count ────────────────────────────
            # self._increment_usage(user_id)

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

    # ── Phase 1 helpers (implement when adding auth) ──────────────────────
    # def _validate_jwt(self, auth_header): ...
    # def _get_user_id_from_jwt(self, auth_header): ...
    # def _check_usage(self, user_id): ...
    # def _increment_usage(self, user_id): ...
    # def _stripe_webhook(self): ...
    # def _create_checkout(self): ...


def main():
    print(f"""
╔══════════════════════════════════════════════╗
║         English Buddy — Local Server         ║
╠══════════════════════════════════════════════╣
║  http://localhost:{PORT}/frontend/english_buddy.html
║                                              ║
║  Press Ctrl+C to stop                        ║
╚══════════════════════════════════════════════╝
    """)
    with http.server.HTTPServer(('', PORT), Handler) as srv:
        try:
            srv.serve_forever()
        except KeyboardInterrupt:
            print('\nServer stopped.')
            sys.exit(0)

if __name__ == '__main__':
    main()
