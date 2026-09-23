#!/usr/bin/env python3
"""Retrieve public DOI metadata, fail closed on unavailable records."""
from concurrent.futures import ThreadPoolExecutor
import argparse
import html
import json
from pathlib import Path
import re
import sys
import time
import unicodedata
from urllib.parse import quote
import urllib.request

sys.path.insert(0, '/Users/jiangsheng/.agents/skills/citation-management/scripts')
from _common import parse_bibtex_file

ROOT = Path(__file__).resolve().parents[1]


def norm(value):
    value = unicodedata.normalize('NFKD', html.unescape(value))
    return ''.join(c.lower() for c in value if c.isalnum())


def fetch(entry):
    fields = entry['fields']
    doi = fields['doi']
    result = {'key': entry['key'], 'doi': doi,
              'source': 'https://api.crossref.org/works/' + quote(doi, safe='')}
    try:
        request = urllib.request.Request(result['source'], headers={'User-Agent': 'PaperA-reference-metadata-check/1.0'})
        with urllib.request.urlopen(request, timeout=20) as response:
            message = json.load(response)['message']
        result['retrieved'] = True
        result['metadata'] = {k: message.get(k) for k in
            ('title', 'author', 'container-title', 'volume', 'issue', 'page', 'article-number',
             'published', 'published-print', 'published-online', 'update-to')}
        result['title_matches'] = norm(fields['title']) == norm(message['title'][0])
        result['volume_matches'] = (fields['volume'] == message['volume'] if message.get('volume')
                                    else None) if fields.get('volume') else True
        result['pages_match'] = norm(fields.get('pages', '')) == norm(message.get('page') or message.get('article-number') or '')
        result['author_surnames_match'] = [norm(a.split(',')[0]) for a in fields['author'].split(' and ')] == [
            norm(a.get('family', '')) for a in message.get('author', [])]
        result['year_matches'] = int(fields['year']) in [message[k]['date-parts'][0][0] for k in
            ('published', 'published-print', 'published-online') if message.get(k)]
        result['bib_authors'] = fields.get('author')
        result['bib_year'] = fields['year']
    except Exception as exc:
        result.update(retrieved=False, error=str(exc))
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--retry-missing', action='store_true')
    args = parser.parse_args()
    entries = [e for e in parse_bibtex_file(str(ROOT/'references.bib')) if e['fields'].get('doi')]
    destination = ROOT/'evidence/reference_metadata_recheck_20260922.json'
    if args.retry_missing and destination.exists():
        results = json.loads(destination.read_text())['records']
        lookup = {e['key']: e for e in entries}
        for index, row in enumerate(results):
            if not row['retrieved']:
                time.sleep(1)
                results[index] = fetch(lookup[row['key']])
    else:
        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(fetch, entries))
    lookup = {e['key']: e['fields'] for e in entries}
    for row in results:
        if not row['retrieved']:
            continue
        fields, message = lookup[row['key']], row['metadata']
        row['volume_matches'] = (fields['volume'] == message['volume'] if message.get('volume')
                                 else None) if fields.get('volume') else True
        row['author_surnames_match'] = [norm(a.split(',')[0]) for a in fields['author'].split(' and ')] == [
            norm(a.get('family', '')) for a in message.get('author', [])]
        row['year_matches'] = int(fields['year']) in [message[k]['date-parts'][0][0] for k in
            ('published', 'published-print', 'published-online') if message.get(k)]
    payload = {'date': '2026-09-22', 'scope': 'Public DOI metadata only; not verification of each substantive claim',
               'records': results}
    destination.write_text(json.dumps(payload, indent=2)+'\n')
    for row in results:
        print(row['key'], {k: v for k, v in row.items() if k not in ('key', 'doi', 'source', 'metadata', 'bib_authors')})


if __name__ == '__main__':
    main()
