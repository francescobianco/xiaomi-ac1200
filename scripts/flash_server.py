"""Server HTTP del PC per il flash X-Wrt (fase B).

Serve SOLO le due immagini indicate e accetta rapporti POST /report/<fase>
dal router (192.168.31.1), salvandoli in private/flash-<fase>.txt.
Si chiude da solo dopo --timeout secondi.
"""
import argparse
import re
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

PRIVATE = Path(__file__).resolve().parents[1] / 'private'
ROUTER = '192.168.31.1'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--kernel', type=Path, required=True)
    parser.add_argument('--rootfs', type=Path, required=True)
    parser.add_argument('--bind', default='192.168.31.222')
    parser.add_argument('--port', type=int, default=18081)
    parser.add_argument('--timeout', type=int, default=1200)
    args = parser.parse_args()
    files = {'/kernel1.bin': args.kernel.read_bytes(), '/rootfs0.bin': args.rootfs.read_bytes()}

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *a):
            print('[http]', self.client_address[0], fmt % a, flush=True)

        def do_GET(self):
            if self.client_address[0] != ROUTER or self.path not in files:
                self.send_error(404)
                return
            body = files[self.path]
            self.send_response(200)
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self):
            m = re.fullmatch(r'/report/([a-z0-9-]{1,32})', self.path)
            length = int(self.headers.get('Content-Length', 0))
            if self.client_address[0] != ROUTER or not m or not 0 < length <= 1024 * 1024:
                self.send_error(403)
                return
            text = self.rfile.read(length).decode(errors='replace')
            target = PRIVATE / f'flash-{m.group(1)}.txt'
            target.write_text(text)
            target.chmod(0o600)
            print(f'=== RAPPORTO {m.group(1)} ===\n{text}', flush=True)
            self.send_response(200)
            self.end_headers()

    server = HTTPServer((args.bind, args.port), Handler)
    threading.Timer(args.timeout, server.shutdown).start()
    print(f'In ascolto su {args.bind}:{args.port}', flush=True)
    server.serve_forever()


if __name__ == '__main__':
    main()
