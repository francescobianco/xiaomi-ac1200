"""Verifica locale delle acquisizioni NAND; nessun accesso al dispositivo."""
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def main():
    folder = ROOT / 'backups/2026-11-10'
    report = (ROOT / 'private/backup-report.txt').read_text()
    remote = {}
    name = None
    for line in report.splitlines():
        match = re.match(r'BEGIN ((?:ecc|raw)-\d{2}\.bin)', line)
        if match:
            name = match.group(1)
        if line.startswith('VERIFY_DUMP_STATUS='):
            name = 'verify-00.bin'
        match = re.match(r'([a-f0-9]{32})\s+/tmp/xiaomi-lab-nand.bin', line)
        if match and name:
            remote[name] = match.group(1)
    manifest = []
    errors = []
    raw_failed = 'RAW_STATUS=1' in report.splitlines()
    if raw_failed:
        errors.append('Acquisizione raw/OOB fallita sul router; copia raw non disponibile')
    for kind, expected in [('ecc', 4194304), ('raw', 4325376), ('verify', 4194304)]:
        for index in range(1 if kind == 'verify' else 32):
            filename = f'{kind}-{index:02d}.bin'
            target = folder / filename
            if not target.exists():
                if kind != 'raw' or not raw_failed:
                    errors.append(f'Manca {filename}')
                continue
            data = target.read_bytes()
            md5 = hashlib.md5(data).hexdigest()
            if len(data) != expected:
                errors.append(f'{filename}: dimensione inattesa {len(data)}')
            if remote.get(filename) != md5:
                errors.append(f'{filename}: MD5 remoto assente o diverso')
            manifest.append({'file': filename, 'bytes': len(data), 'md5': md5,
                             'sha256': hashlib.sha256(data).hexdigest()})
    stable = {}
    if (folder / 'ecc-00.bin').exists() and (folder / 'verify-00.bin').exists():
        first = (folder / 'ecc-00.bin').read_bytes()
        second = (folder / 'verify-00.bin').read_bytes()
        for label, offset in [('Bootloader', 0), ('Config', 0x40000), ('Bdata', 0x80000), ('Factory', 0xc0000)]:
            stable[label] = first[offset:offset + 0x40000] == second[offset:offset + 0x40000]
            if not stable[label]:
                errors.append(f'{label}: differenza tra due letture')
    for status in ('ECC_STATUS=0', 'VERIFY_DUMP_STATUS=0', 'VERIFY_UPLOAD_STATUS=0'):
        if status not in report.splitlines():
            errors.append(f'Esito non confermato: {status}')
    result = {'files': manifest, 'critical_partitions_equal_on_second_read': stable, 'errors': errors,
              'limitations': ['Acquisizione online: overlay non congelato.',
                              'Raw richiesto con --noecc --oob --bb=dumpbad; semantica del driver vendor da verificare.',
                              'Ripristino non provato; seconda copia su supporto indipendente da creare.']}
    (folder / 'manifest.json').write_text(json.dumps(result, indent=2) + '\n')
    (folder / 'SHA256SUMS').write_text(''.join(f"{item['sha256']}  {item['file']}\n" for item in manifest))
    ecc = [m for m in manifest if m['file'].startswith('ecc-')]
    logical_ok = (len(ecc) == 32 and not any('raw' not in error.lower() for error in errors))
    public = {'files_verified': len(manifest), 'logical_ecc_backup_verified': logical_ok,
              'logical_ecc_bytes': sum(m['bytes'] for m in ecc),
              'raw_oob_complete': len([m for m in manifest if m['file'].startswith('raw-')]) == 32,
              'critical_partitions_equal_on_second_read': stable, 'errors': errors,
              'limitations': result['limitations']}
    (ROOT / 'docs/evidence/2026-11-10-backup-verification.json').write_text(json.dumps(public, indent=2) + '\n')
    print(json.dumps(public, indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
