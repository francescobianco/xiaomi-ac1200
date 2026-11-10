#!/usr/bin/env python3
"""Legge esclusivamente init_info e verifica tre porte di gestione dello Xiaomi."""
import argparse
import datetime
import ipaddress
import json
from pathlib import Path
import socket
import urllib.request


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host', default='192.168.31.1')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    address = ipaddress.IPv4Address(args.host)
    if not address.is_private:
        parser.error('Usare un indirizzo IPv4 privato del dispositivo di laboratorio')
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    url = f'http://{address}/cgi-bin/luci/api/xqsystem/init_info'
    with opener.open(url, timeout=8) as response:
        info = json.load(response)
    if info.get('code') != 0:
        raise RuntimeError('init_info non ha restituito code=0')
    # Esclude seriale, routerId, SSID e altri identificativi dell'unità.
    keys = ('hardware', 'romversion', 'countrycode', 'language', 'inited', 'connect', 'bound')
    report = {
        'observed_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'source': url,
        'info': {key: info[key] for key in keys if key in info},
        'management_tcp': {},
    }
    for port in (22, 23, 122):
        try:
            with socket.create_connection((str(address), port), timeout=2):
                state = 'reachable'
        except ConnectionRefusedError:
            state = 'refused'
        except TimeoutError:
            state = 'timeout'
        except OSError as error:
            state = f'error: {error.strerror}'
        report['management_tcp'][str(port)] = state
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
