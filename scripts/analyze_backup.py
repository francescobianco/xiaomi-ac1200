"""Analisi offline del backup logico, senza esportare dati unici dell'unità."""
import hashlib
import json
from pathlib import Path
import re
import struct
import zlib

ROOT = Path(__file__).resolve().parents[1]


def main():
    path = ROOT / 'backups/2026-11-10/full-ecc.bin'
    expected = (path.parent / 'full-ecc.sha256').read_text().split()[0]
    blob = path.read_bytes()
    if len(blob) != 134217728 or hashlib.sha256(blob).hexdigest() != expected:
        raise SystemExit('Backup combinato non valido')
    report = {'backup_size': len(blob), 'combined_sha256_verified': True, 'stock_kernels': []}
    for offset in (0x200000, 0x600000):
        header = blob[offset:offset + 64]
        magic, hcrc, timestamp, size, load, entry, dcrc, osid, arch, kind, compression, name = struct.unpack('>7I4B32s', header)
        if magic != 0x27051956 or size > 0x400000 - 64:
            raise SystemExit('Header kernel stock inatteso')
        check = bytearray(header)
        check[4:8] = bytes(4)
        report['stock_kernels'].append({
            'offset': offset, 'payload_size': size, 'load': hex(load), 'entry': hex(entry),
            'name': name.rstrip(b'\0').decode(), 'compression_id': compression,
            'header_crc_ok': zlib.crc32(check) == hcrc,
            'payload_crc_ok': zlib.crc32(blob[offset + 64:offset + 64 + size]) == dcrc,
        })
    boot = blob[:0x40000]
    versions = re.findall(rb'U-Boot [ -~]{1,80}', boot)
    report['bootloader_version_strings'] = [v.decode() for v in versions]
    report['bootloader_contains_tftp_menu'] = b'Load system code to SDRAM via TFTP' in boot
    report['recovery_tested'] = False
    dts = (ROOT / 'work/x-wrt/target/linux/ramips/dts/mt7620a_xiaomi_miwifi-r3.dts').read_text()
    partitions = []
    for label, start, length in re.findall(r'label = "([^"]+)";\s+reg = <(0x[0-9a-f]+) (0x[0-9a-f]+)>;', dts):
        partitions.append({'name': label, 'offset': int(start, 16), 'size': int(length, 16)})
    report['candidate_dts_partitions'] = partitions
    report['candidate_ubi_merges_stock_filesystems'] = {'offset': 0xa00000, 'size': 0x7600000} in [
        {'offset': p['offset'], 'size': p['size']} for p in partitions if p['name'] == 'ubi']
    target = ROOT / 'docs/evidence/2026-11-10-offline-analysis.json'
    target.write_text(json.dumps(report, indent=2) + '\n')
    print('Backup verificato, kernel stock:', len(report['stock_kernels']))
    if not all(k['header_crc_ok'] and k['payload_crc_ok'] for k in report['stock_kernels']):
        raise SystemExit('CRC kernel non valido')


if __name__ == '__main__':
    main()
