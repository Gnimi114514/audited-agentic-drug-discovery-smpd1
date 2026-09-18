"""Bounded range download of the observed Zenodo stock, verified before publication."""
import argparse
import concurrent.futures
import hashlib
import json
from pathlib import Path
import time
from urllib.request import Request, urlopen


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--record', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    record_raw = args.record.read_bytes()
    record = json.loads(record_raw)
    entry = next(f for f in record['files'] if f['key'] == 'zinc_stock.hdf5')
    size, checksum, url = entry['size'], entry['checksum'], entry['links']['self']
    if size > 2_000_000_000 or not checksum.startswith('md5:') or not url.startswith('https://zenodo.org/'):
        raise ValueError('unexpected source or resource bound')
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    if (out / 'zinc_stock.hdf5').exists():
        raise ValueError('completed output already exists; verify instead of restarting')
    protocol = {'url': url, 'size': size, 'checksum': checksum, 'source_record_sha256': hashlib.sha256(record_raw).hexdigest(),
                'range_bytes': 8*1024*1024, 'workers': 4, 'wall_budget_seconds': 300}
    existing = out / 'protocol.json'
    if existing.exists() and json.loads(existing.read_bytes()) != protocol:
        raise ValueError('resume source/configuration changed')
    if not existing.exists():
        existing.write_text(json.dumps(protocol, indent=2), encoding='utf-8')
    record_path = out / 'record.json'
    if record_path.exists() and record_path.read_bytes() != record_raw:
        raise ValueError('archived source metadata changed')
    if not record_path.exists():
        record_path.write_bytes(record_raw)
    attempt_id = str(time.time_ns())
    source_snapshot = 'attempt-' + attempt_id + '-source.py'
    (out / source_snapshot).write_bytes(Path(__file__).read_bytes())
    start = time.monotonic()
    chunks = out / 'chunks'
    chunks.mkdir(exist_ok=True)
    width = protocol['range_bytes']

    def fetch(offset):
        stop = min(size-1, offset+width-1)
        path = chunks / str(offset)
        if path.exists() and path.stat().st_size == stop-offset+1:
            return {'offset': offset, 'status': 'REUSED_UNTIL_FINAL_CHECKSUM'}
        errors = []
        for attempt in range(2):
            if time.monotonic()-start > 300:
                return {'offset': offset, 'status': 'TIME_BUDGET'}
            try:
                with urlopen(Request(url, headers={'Range': f'bytes={offset}-{stop}'}), timeout=25) as response:
                    if response.status != 206 or response.headers.get('Content-Range') != f'bytes {offset}-{stop}/{size}':
                        raise ValueError('server returned wrong range')
                    body = bytearray()
                    while len(body) <= stop-offset+1:
                        if time.monotonic()-start > 300:
                            raise TimeoutError('request-start budget exhausted during transfer')
                        block = response.read(min(262144, stop-offset+2-len(body)))
                        if not block:
                            break
                        body.extend(block)
                    raw = bytes(body)
                if len(raw) != stop-offset+1:
                    raise ValueError('wrong body length')
                temp = path.with_suffix('.partial')
                temp.write_bytes(raw)
                temp.replace(path)
                return {'offset': offset, 'status': 'DOWNLOADED'}
            except Exception as exc:
                errors.append(str(exc))
        return {'offset': offset, 'status': 'FAILED', 'errors': errors}

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(fetch, range(0, size, width)))
    result = {'elapsed_seconds': time.monotonic()-start, 'chunks': results, 'status': 'INCOMPLETE'}
    if all(r['status'] in ('DOWNLOADED', 'REUSED_UNTIL_FINAL_CHECKSUM') for r in results):
        md5, sha = hashlib.md5(), hashlib.sha256()
        temp = out / 'assembled.partial'
        with temp.open('wb') as handle:
            for offset in range(0, size, width):
                raw = (chunks / str(offset)).read_bytes()
                handle.write(raw)
                md5.update(raw)
                sha.update(raw)
        result.update(md5=md5.hexdigest(), sha256=sha.hexdigest(), assembled_bytes=temp.stat().st_size)
        if 'md5:' + md5.hexdigest() == checksum and temp.stat().st_size == size:
            temp.replace(out / 'zinc_stock.hdf5')
            result['status'] = 'VERIFIED'
        else:
            result['status'] = 'CHECKSUM_FAILED'
    result['total_elapsed_seconds'] = time.monotonic()-start
    result['source_snapshot'] = source_snapshot
    result['budget_semantics'] = '300s transfer budget checked between requests/reads; socket calls can overrun by timeout, assembly is additional'
    with (out / ('attempt-' + attempt_id + '.json')).open('x', encoding='utf-8') as handle:
        json.dump(result, handle, indent=2)
    print(json.dumps({k: v for k, v in result.items() if k != 'chunks'}, indent=2))
    raise SystemExit(0 if result['status'] == 'VERIFIED' else 2)
