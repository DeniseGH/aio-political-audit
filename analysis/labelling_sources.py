"""
labelling_sources_flat.py
Processes all SERP JSON files in data/raw and outputs a flat CSV where
each row is ONE SOURCE (organic or AIO) with its label.
"""

import json
import argparse
import glob
import os
import pandas as pd
from urllib.parse import urlparse

UGC_DOMAINS = {
    'facebook.com', 'instagram.com', 'youtube.com', 'reddit.com',
    'tiktok.com', 'twitter.com', 'x.com', 'threads.com',
    'linkedin.com', 'pinterest.com', 'quora.com',
}

def extract_host(url):
    try:
        return urlparse(url).netloc.lstrip('www.')
    except Exception:
        return ''

def build_mbfc_lookup():
    import requests
    print('Loading MBFC dataset from HuggingFace...')
    lookup = {}
    offset = 0
    length = 100
    total = None
    while True:
        url = (
            f"https://datasets-server.huggingface.co/rows"
            f"?dataset=sergioburdisso%2Fnews_media_bias_and_factuality"
            f"&config=default&split=train&offset={offset}&length={length}"
        )
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if total is None:
            total = data.get('num_rows_total', 0)
            print(f'  total rows in dataset: {total}')
        rows = data.get('rows', [])
        if not rows:
            break
        for item in rows:
            row = item['row']
            lookup[row['source']] = {
                'bias': row['bias'],
                'factual_reporting': row['factual_reporting']
            }
        offset += len(rows)
        print(f'  fetched {offset}/{total}...')
        if offset >= total:
            break
    print(f'  loaded {len(lookup):,} domains')
    return lookup

def classify(host, mbfc):
    if not host:
        return dict(domain_type='unknown', bias=None, factual_reporting=None, mbfc_matched=False)
    if any(host == u or host.endswith('.' + u) for u in UGC_DOMAINS):
        return dict(domain_type='ugc_platform', bias=None, factual_reporting=None, mbfc_matched=False)
    parts = host.split('.')
    for i in range(len(parts) - 1):
        candidate = '.'.join(parts[i:])
        if candidate in mbfc:
            e = mbfc[candidate]
            return dict(
                domain_type='news',
                bias=e['bias'],
                factual_reporting=e['factual_reporting'],
                mbfc_matched=True
            )
    tld = host.split('.')[-1] if '.' in host else ''
    dtype = 'italian_news_unmatched' if tld == 'it' else 'news_unmatched'
    return dict(domain_type=dtype, bias=None, factual_reporting=None, mbfc_matched=False)

def extract_rows(record, filename, mbfc):
    rows = []
    meta = {
        'file': filename,
        'query': record.get('query'),
        'topic': record.get('topic'),
        'timestamp_utc': record.get('timestamp_utc'),
        'has_ai_overview': record.get('has_ai_overview'),
    }

    # Organic sources
    for n in range(1, 11):
        url = record.get(f'org{n}_link')
        if not url:
            continue
        host = extract_host(url)
        lbl = classify(host, mbfc)
        rows.append({
            **meta,
            'source_type': 'organic',
            'position': n,
            'title': record.get(f'org{n}_title'),
            'url': url,
            'host': host,
            'domain_type': lbl['domain_type'],
            'bias': lbl['bias'],
            'factual_reporting': lbl['factual_reporting'],
            'mbfc_matched': lbl['mbfc_matched']
        })

    # AIO sources
    aio_raw = record.get('aio_sources')
    if aio_raw and record.get('has_ai_overview'):
        try:
            aio_sources = json.loads(aio_raw) if isinstance(aio_raw, str) else aio_raw
        except Exception:
            aio_sources = []
        for idx, src in enumerate(aio_sources, start=1):
            url = src.get('link', '')
            host = extract_host(url)
            lbl = classify(host, mbfc)
            rows.append({
                **meta,
                'source_type': 'aio',
                'position': idx,
                'title': src.get('title'),
                'url': url,
                'host': host,
                'domain_type': lbl['domain_type'],
                'bias': lbl['bias'],
                'factual_reporting': lbl['factual_reporting'],
                'mbfc_matched': lbl['mbfc_matched']
            })

    return rows

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input_dir', default='data/raw')
    parser.add_argument('--output', default='data/sources_labelled.csv')
    args = parser.parse_args()

    mbfc = build_mbfc_lookup()
    files = sorted(glob.glob(os.path.join(args.input_dir, '*.json')))
    if not files:
        print(f'No JSON files found in {args.input_dir}')
        return

    print(f'Processing {len(files)} file(s)...')
    all_rows = []

    for fp in files:
        fname = os.path.basename(fp)
        with open(fp, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if isinstance(data, dict):
            data = [data]
        for record in data:
            all_rows.extend(extract_rows(record, fname, mbfc))
        print(f'  {fname}  ({len(data)} queries)')

    df = pd.DataFrame(all_rows)
    os.makedirs(os.path.dirname(args.output) or '.', exist_ok=True)
    df.to_csv(args.output, index=False, encoding='utf-8')

    total = len(df)
    matched = int(df['mbfc_matched'].sum())
    print(f'Total rows: {total}')
    print(f'MBFC matched: {matched} ({100*matched/total:.1f}%)')
    print(df.groupby('source_type').size())
    print(df.groupby('domain_type').size().sort_values(ascending=False))
    if matched > 0:
        print(df[df['mbfc_matched']]['bias'].value_counts())
        print(df[df['mbfc_matched']]['factual_reporting'].value_counts())
    print(f'Saved to {args.output}')

if __name__ == '__main__':
    main()