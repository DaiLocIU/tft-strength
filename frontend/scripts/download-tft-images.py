"""Download OP.GG portraits using the supplied Set 18 URL pattern.
Run from any directory: python3 frontend/scripts/download-tft-images.py
"""
import argparse
import concurrent.futures
import json
from pathlib import Path
import re
import urllib.request
import urllib.error

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'public/images/tft/set-18'
CHAMPIONS = json.loads((ROOT / 'scripts/set-18-champions.json').read_text())['champions']

URL_OVERRIDES = {
    'Mama Beak': 'https://cdn.lolchess.gg/upload/images/champions/Raptor_1783677107-CrimsonRaptor.jpg?image=q_auto:good,f_webp&v=1788508742',
    'Pebbles': 'https://cdn.lolchess.gg/upload/images/champions/Pebbles_1783677606-Sentry.jpg?image=q_auto:good,f_webp&v=1788508742',
}

def download(champion):
    slug = re.sub(r'[^a-z0-9]', '', champion['name'].lower())
    url = f'https://c-tft-api.op.gg/img/set/18/tft-champion/tiles/tft18_{slug}.tft_set18.jpg?image=q_auto:good,f_webp&v=1788508742'
    if champion['name'].startswith('Lux ('):
        slug = 'lux'
        url = 'https://c-tft-api.op.gg/img/set/18/tft-champion/tiles/tft18_lux.tft_set18.jpg?image=q_auto:good,f_webp&v=1788508742'
    url = URL_OVERRIDES.get(champion['name'], url)
    result = {'name': champion['name'], 'apiName': champion['apiName'], 'url': url}
    try:
        request = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(request, timeout=25) as response:
            data = response.read()
            content_type = response.headers.get('Content-Type', '')
        if data[:4] == b'RIFF' and data[8:12] == b'WEBP':
            extension = 'webp'
        elif data[:3] == b'\xff\xd8\xff':
            extension = 'jpg'
        elif data[:8] == b'\x89PNG\r\n\x1a\n':
            extension = 'png'
        else:
            raise ValueError(f'Not a valid image ({content_type})')
        filename = f'{slug}.{extension}'
        (DEST / filename).write_bytes(data)
        result.update(status='downloaded', path=f'/images/tft/set-18/{filename}', bytes=len(data))
    except urllib.error.HTTPError as error:
        result.update(status='failed', error=f'HTTP {error.code}')
    except Exception as error:
        result.update(status='failed', error=str(error))
    return result

if __name__ == '__main__':
    DEST.mkdir(parents=True, exist_ok=True)
    # Exclude neutral enemies, item anvils and other non-champion entities.
    roster = [c for c in CHAMPIONS if c['traits']]
    parser = argparse.ArgumentParser()
    parser.add_argument('--only', nargs='+', choices=[c['name'] for c in roster], help='Update only named champions, preserving other download results')
    args = parser.parse_args()
    report_path = DEST / 'download-report.json'
    previous = json.loads(report_path.read_text()) if args.only and report_path.exists() else []
    selected = [c for c in roster if not args.only or c['name'] in args.only]
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        updated = list(pool.map(download, selected))
    by_api_name = {c['apiName']: c for c in previous}
    by_api_name.update({c['apiName']: c for c in updated})
    results = sorted(by_api_name.values(), key=lambda c: c['name'])
    (DEST / 'download-report.json').write_text(json.dumps(results, indent=2) + '\n')
    manifest = {c['apiName']: c['path'] for c in results if c['status'] == 'downloaded'}
    (ROOT / 'src/services/champion-images.json').write_text(json.dumps(manifest, indent=2) + '\n')
    failures = [c for c in results if c['status'] == 'failed']
    report = ['# Set 18 portrait downloads', '', f'Downloaded {len(manifest)} of {len(results)} portraits.', '', '## Failed URLs', '']
    report.extend(f"- [{c['name']}]({c['url']}) — {c['error']}" for c in failures)
    (DEST / 'download-report.md').write_text('\n'.join(report) + '\n')
    print(f'Downloaded {len(manifest)}/{len(results)} portraits')
    for c in failures:
        print(f"{c['name']}: {c['error']}")
