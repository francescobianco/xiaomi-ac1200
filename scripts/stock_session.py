"""Client locale per l'autenticazione stock R3; nessuna procedura di flash."""
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import time
import urllib.parse
import urllib.request

BASE = 'http://192.168.31.1'
PRIVATE = Path(__file__).resolve().parents[1] / 'private'


def save_private(name, value):
    PRIVATE.mkdir(mode=0o700, exist_ok=True)
    os.chmod(PRIVATE, 0o700)
    target = PRIVATE / name
    with os.fdopen(os.open(target, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600), 'w') as out:
        out.write(value)


def request(path, data=None):
    if not path.startswith('/cgi-bin/luci/'):
        raise ValueError('Percorso non locale al pannello')
    body = urllib.parse.urlencode(data).encode() if data is not None else None
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    return opener.open(BASE + path, data=body, timeout=20).read().decode()


def login(password, initial=False):
    page = request('/cgi-bin/luci/web/init/hello' if initial else '/cgi-bin/luci/web')
    key = re.search(r"key: '([^']+)'", page).group(1)
    device = re.search(r"var deviceId = '([^']+)'", page).group(1)
    nonce = f'0_{device}_{int(time.time())}_{secrets.randbelow(10000)}'
    sha1 = lambda value: hashlib.sha1(value.encode()).hexdigest()
    data = dict(username='admin', password=sha1(nonce + sha1(password + key)), nonce=nonce, logtype=2)
    if initial:
        data['init'] = 1
    result = json.loads(request('/cgi-bin/luci/api/xqsystem/login', data))
    if result.get('code') != 0:
        raise RuntimeError(f"Login rifiutato, code={result.get('code')}")
    save_private('session.json', json.dumps(result))
    return result


if __name__ == '__main__':
    info = json.loads(request('/cgi-bin/luci/api/xqsystem/init_info'))
    if (info.get('hardware'), info.get('romversion'), info.get('inited')) != ('R3', '2.26.39', 0):
        raise SystemExit('Stato inatteso: nessun tentativo di login iniziale eseguito')
    session = login('admin', initial=True)  # Credenziale iniziale usata dalla pagina stock.
    url = session.get('url', '')
    if url.startswith(BASE):
        url = url[len(BASE):]
    if not url.startswith('/cgi-bin/luci/'):
        raise SystemExit('Percorso di destinazione inatteso')
    page = request(url)
    save_private('initial-guide.html', page)
    print('Login iniziale riuscito; sessione e pagina guida salvate in private/, senza mostrare token.')
