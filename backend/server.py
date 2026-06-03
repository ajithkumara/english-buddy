#!/usr/bin/env python3
"""
English Buddy — proxy server
- Serves frontend/english_buddy.html
- Proxies AI API calls, injecting API keys server-side
- Rate limiting — blocks prompt flooding and API credit abuse
- Works locally (start.bat) and on Render.com
"""
import http.server
import urllib.request
import urllib.error
import json
import os
import sys
import time
import threading
from collections import defaultdict

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

# ── Rate limiter configuration ────────────────────────────────────────────────
# Tune these via environment variables in Render dashboard
#
# RATE_LIMIT_REQUESTS  — max AI requests per IP per window (default 10)
# RATE_LIMIT_WINDOW    — window size in seconds (default 60)
# RATE_LIMIT_BLOCK_SEC — how long a blocked IP stays blocked (default 300 = 5 min)
# RATE_LIMIT_ENABLED   — set to 'false' to disable (useful for local dev)
#
# Example: 10 requests per 60 seconds = real user talking to Alex
#          A bot would hit this in seconds and get blocked for 5 minutes

RATE_MAX      = int(os.getenv('RATE_LIMIT_REQUESTS',  '10'))
RATE_WINDOW   = int(os.getenv('RATE_LIMIT_WINDOW',    '60'))
RATE_BLOCK    = int(os.getenv('RATE_LIMIT_BLOCK_SEC', '300'))
RATE_ENABLED  = os.getenv('RATE_LIMIT_ENABLED', 'true').lower() != 'false'

# ── In-memory rate limit store ────────────────────────────────────────────────
# Thread-safe storage for request timestamps and blocked IPs.
# Note: resets on server restart. Redis would persist across restarts
# but is overkill until you hit 1000+ concurrent users.
_lock        = threading.Lock()
_requests    = defaultdict(list)   # ip -> [timestamps of recent requests]
_blocked     = {}                  # ip -> unblock_timestamp
_block_count = defaultdict(int)    # ip -> total times blocked (for logging)

def check_rate_limit(ip: str) -> tuple[bool, str]:
    """
    Check if an IP is rate limited.
    Returns (is_blocked, reason_message)

    Logic:
    1. If IP is in blocked list and block hasn't expired → blocked
    2. Clean up old timestamps outside the window
    3. If request count >= max → add to blocked list
    4. Otherwise → allow and record this request
    """
    if not RATE_ENABLED:
        return False, ''

    now = time.time()

    with _lock:
        # ── Check if currently blocked ────────────────────────────────────
        if ip in _blocked:
            if now < _blocked[ip]:
                remaining = int(_blocked[ip] - now)
                return True, f'Too many requests. Try again in {remaining} seconds.'
            else:
                del _blocked[ip]  # Block expired — unblock

        # ── Clean up old timestamps outside window ────────────────────────
        _requests[ip] = [t for t in _requests[ip] if now - t < RATE_WINDOW]

        # ── Check if over limit ───────────────────────────────────────────
        if len(_requests[ip]) >= RATE_MAX:
            _blocked[ip] = now + RATE_BLOCK
            _block_count[ip] += 1
            count = _block_count[ip]
            print(f'  [RATE LIMIT] Blocked {ip} — '
                  f'{len(_requests[ip])} requests in {RATE_WINDOW}s '
                  f'(block #{count}, duration {RATE_BLOCK}s)')
            return True, f'Too many requests. Try again in {RATE_BLOCK} seconds.'

        # ── Allow — record this request ───────────────────────────────────
        _requests[ip].append(now)
        return False, ''


def cleanup_old_entries():
    """
    Background thread — runs every 5 minutes.
    Removes stale IP entries to prevent memory growth.
    Without this, the dicts grow forever if many unique IPs hit the server.
    """
    while True:
        time.sleep(300)
        now = time.time()
        with _lock:
            # Remove IPs with no recent requests
            stale_ips = [
                ip for ip, times in _requests.items()
                if not times or (now - max(times)) > RATE_WINDOW * 2
            ]
            for ip in stale_ips:
                del _requests[ip]

            # Remove expired blocks
            expired = [ip for ip, t in _blocked.items() if now >= t]
            for ip in expired:
                del _blocked[ip]

        if stale_ips or expired:
            print(f'  [CLEANUP] Removed {len(stale_ips)} stale IPs, '
                  f'{len(expired)} expired blocks')


# ── Prompt safety guardrails ──────────────────────────────────────────────────
# Block obvious prompt injection attempts before they reach the AI.
# This is a basic blocklist — not a replacement for AI-level filtering,
# but stops the most common attacks cheaply at zero API cost.

BLOCKED_PHRASES = [
    'ignore your previous instructions',
    'ignore previous instructions',
    'ignore all instructions',
    'forget your instructions',
    'you are now a different',
    'you are no longer',
    'your new instructions are',
    'disregard your system prompt',
    'act as if you have no restrictions',
    'pretend you have no restrictions',
    'jailbreak',
    'dan mode',
    'developer mode',
]

def is_prompt_injection(text: str) -> bool:
    """Check if user input contains prompt injection attempts."""
    lower = text.lower()
    return any(phrase in lower for phrase in BLOCKED_PHRASES)


# ── Main handler ──────────────────────────────────────────────────────────────
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

    def _get_client_ip(self) -> str:
        """
        Get the real client IP address.
        On Render, the real IP is in X-Forwarded-For header
        because requests pass through Render's proxy layer first.
        Fallback to direct connection IP for local dev.
        """
        forwarded = self.headers.get('X-Forwarded-For', '')
        if forwarded:
            # X-Forwarded-For can be comma-separated if through multiple proxies
            # First IP is always the real client
            return forwarded.split(',')[0].strip()
        return self.client_address[0]

    def _proxy(self):
        """
        Proxy AI API calls.
        Order of checks:
        1. Rate limit — blocks flooding
        2. Read and parse body
        3. Prompt injection check
        4. Inject API key
        5. Forward to AI provider
        """
        # ── Step 1: Rate limit check ──────────────────────────────────────
        ip = self._get_client_ip()
        blocked, reason = check_rate_limit(ip)
        if blocked:
            self._send_json(429, {
                'error': reason,
                'type':  'rate_limit'
            })
            return

        try:
            # ── Step 2: Read body ─────────────────────────────────────────
            length  = int(self.headers.get('Content-Length', 0))
            raw     = self.rfile.read(length)
            payload = json.loads(raw)

            target  = payload.get('url', '')
            headers = payload.get('headers', {})
            body    = payload.get('body', {})

            # ── Step 3: Prompt injection check ───────────────────────────
            # Check the last user message in the conversation
            messages = body.get('messages', [])
            if messages:
                last_msg = messages[-1].get('content', '')
                if is_prompt_injection(last_msg):
                    print(f'  [SECURITY] Prompt injection blocked from {ip}')
                    self._send_json(400, {
                        'error': 'Message contains disallowed content.',
                        'type':  'prompt_injection'
                    })
                    return

            data = json.dumps(body).encode()

            # ── Step 4: Inject API key ────────────────────────────────────
            if 'anthropic.com' in target:
                key = os.getenv('ANTHROPIC_API_KEY', '')
                if not key:
                    self._send_json(500, {'error': 'ANTHROPIC_API_KEY not configured'})
                    return
                headers['x-api-key']         = key
                headers['anthropic-version'] = '2023-06-01'
                headers['Content-Type']      = 'application/json'

            elif 'openai.com' in target:
                key = os.getenv('OPENAI_API_KEY', '')
                if not key:
                    self._send_json(500, {'error': 'OPENAI_API_KEY not configured'})
                    return
                headers['Authorization'] = f'Bearer {key}'
                headers['Content-Type']  = 'application/json'

            elif 'deepseek.com' in target:
                key = os.getenv('DEEPSEEK_API_KEY', '')
                if not key:
                    self._send_json(500, {'error': 'DEEPSEEK_API_KEY not configured'})
                    return
                headers['Authorization'] = f'Bearer {key}'
                headers['Content-Type']  = 'application/json'

            elif 'openrouter.ai' in target:
                key = os.getenv('OPENROUTER_API_KEY', '')
                if not key:
                    self._send_json(500, {'error': 'OPENROUTER_API_KEY not configured'})
                    return
                headers['Authorization'] = f'Bearer {key}'
                headers['Content-Type']  = 'application/json'

            else:
                self._send_json(400, {'error': 'Unknown AI provider URL'})
                return

            # ── Step 5: Forward to AI provider ───────────────────────────
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
    host = '0.0.0.0'  # Required for Render

    # ── Start background cleanup thread ──────────────────────────────────────
    cleaner = threading.Thread(target=cleanup_old_entries, daemon=True)
    cleaner.start()

    # ── Startup warnings ─────────────────────────────────────────────────────
    if not os.getenv('ANTHROPIC_API_KEY') and \
       not os.getenv('DEEPSEEK_API_KEY') and \
       not os.getenv('OPENROUTER_API_KEY'):
        print('⚠  WARNING: No AI API key found!')
        print('   Set ANTHROPIC_API_KEY, DEEPSEEK_API_KEY, or OPENROUTER_API_KEY')

    # ── Print startup summary ─────────────────────────────────────────────────
    print(f"""
╔══════════════════════════════════════════════════╗
║       English Buddy — {ENV.upper():<26}║
╠══════════════════════════════════════════════════╣
║  Port        : {PORT:<33}║
║  Rate limit  : {f'{RATE_MAX} req / {RATE_WINDOW}s per IP':<33}║
║  Block time  : {f'{RATE_BLOCK}s ({RATE_BLOCK//60} min)':<33}║
║  Guardrails  : {'ON' if RATE_ENABLED else 'OFF (disabled)':<33}║""")

    if ENV == 'local':
        print(f"║  URL         : http://localhost:{PORT}/english_buddy.html  ║")
    else:
        print(f"║  Hosting     : {'Render.com':<33}║")

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
