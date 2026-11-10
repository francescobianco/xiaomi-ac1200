"""Configurazione iniziale stock; eseguire le fasi separatamente, una sola volta."""
import argparse
import base64
import hashlib
import json
import re
import secrets
import string
import subprocess
import time

from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from stock_session import PRIVATE, login, request, save_private


def credentials():
    return json.loads((PRIVATE / 'credentials.json').read_text())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=['prepare', 'configure', 'reconnect', 'verify'])
    args = parser.parse_args()
    if args.stage == 'prepare':
        if (PRIVATE / 'credentials.json').exists():
            raise SystemExit('Credenziali già presenti: non sovrascritte')
        password = lambda: ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(24))
        creds = {'ssid': 'Xiaomi-R3-Lab', 'wifi_password': password(), 'admin_password': password()}
        save_private('credentials.json', json.dumps(creds, indent=2) + '\n')
        save_private('nm-passwords', '802-11-wireless-security.psk:' + creds['wifi_password'] + '\n')
        subprocess.run(['nmcli', 'connection', 'add', 'type', 'wifi', 'ifname', 'wlxe0b2f1c5819b',
                        'con-name', 'xiaomi-lab', 'ssid', creds['ssid'], 'connection.autoconnect', 'no',
                        'ipv4.method', 'auto', 'ipv4.never-default', 'yes', 'ipv4.ignore-auto-dns', 'yes',
                        'ipv6.method', 'disabled', 'wifi-sec.key-mgmt', 'wpa-psk', 'wifi-sec.psk-flags', '2'], check=True)
        print('Credenziali private e profilo di riconnessione preparati.')
    elif args.stage == 'configure':
        info = json.loads(request('/cgi-bin/luci/api/xqsystem/init_info'))
        if (info.get('hardware'), info.get('romversion'), info.get('inited')) != ('R3', '2.26.39', 0):
            raise SystemExit('Stato inatteso: configurazione non eseguita')
        creds = credentials()
        session = login('admin', initial=True)
        page = request('/cgi-bin/luci/web/init/hello')
        key = re.search(r"key: '([^']+)'", page).group(1)
        iv = bytes.fromhex(re.search(r"iv: '([^']+)'", page).group(1))
        device = re.search(r"var deviceId = '([^']+)'", page).group(1)
        sha1 = lambda value: hashlib.sha1(value.encode()).hexdigest()
        nonce = f'0_{device}_{int(time.time())}_{secrets.randbelow(10000)}'
        aeskey = bytes.fromhex(sha1('admin' + key)[:32])
        padder = padding.PKCS7(128).padder()
        plain = padder.update(sha1(creds['admin_password'] + key).encode()) + padder.finalize()
        encryptor = Cipher(algorithms.AES(aeskey), modes.CBC(iv)).encryptor()
        encrypted = base64.b64encode(encryptor.update(plain) + encryptor.finalize()).decode()
        data = {'name': creds['ssid'], 'locale': 'home', 'ssid': creds['ssid'],
                'password': creds['wifi_password'], 'encryption': 'mixed-psk', 'nonce': nonce,
                'newPwd': encrypted, 'oldPwd': sha1(nonce + sha1('admin' + key)), 'txpwr': 0}
        path = '/cgi-bin/luci/;stok=' + session['token'] + '/api/misystem/set_router_normal'
        result = json.loads(request(path, data))
        save_private('setup-response.json', json.dumps(result))
        print('Configurazione stock: code=', result.get('code'))
        if result.get('code') != 0:
            raise SystemExit('Configurazione non riuscita; verificare la risposta privata')
    elif args.stage == 'reconnect':
        subprocess.run(['nmcli', '--wait', '30', 'connection', 'up', 'xiaomi-lab',
                        'passwd-file', str(PRIVATE / 'nm-passwords')], check=True)
    else:
        session = login(credentials()['admin_password'])
        print('Login con nuova password amministrativa riuscito.')
        info = json.loads(request('/cgi-bin/luci/api/xqsystem/init_info'))
        print('Modello:', info.get('hardware'), 'Firmware:', info.get('romversion'), 'Inizializzato:', info.get('inited'))


if __name__ == '__main__':
    main()
