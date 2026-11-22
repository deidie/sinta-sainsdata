#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Satu program publikasi dosen Sains Data UINSU: GARUDA + SINTA + Scopus.

  python cek_sinta.py

- GARUDA: ambil metadata publik enam dosen.
- SINTA: cocokkan jurnal dari profil jurnal resmi; peringkat historis hanya
  diisi jika ada bukti DOI/spesifik periode SK. HTTP 403 tidak diterobos.
- Scopus: verifikasi artikel DOI lewat API Elsevier dengan API Key opsional.
  Tanpa kunci, status tidak diisi secara spekulatif.
- Keluaran rekap di folder hasil/, siap diterbitkan oleh GitHub Pages.
- Tidak menggunakan dependensi Python eksternal; tidak mengubah Apps Script.

Peringatan: angka 0 pada rekap SINTA/Scopus berarti 0 *terverifikasi*
dari sumber yang berhasil diakses, BUKAN bukti tidak ada artikel terindeks.
"""
from __future__ import annotations

import csv
import difflib
import json
import os
import re
import sys
import time
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse, parse_qs, urlencode
from urllib.request import Request, urlopen



# ===== 1. GARUDA =====


"""Indeks publikasi GARUDA enam dosen Sains Data UINSU.

Sumber: halaman penulis GARUDA yang dapat diakses publik, ditambah ringkasan
metrik pada halaman profil SINTA publik. Tidak memerlukan API key.

Berhenti ketika situs membatasi permintaan (403/429); tidak mengakses konten
khusus login, tidak memakai proxy, CAPTCHA bypass atau sesi pribadi.

Simpan sebagai cek_sinta.py di repository GitHub yang sudah digunakan.
"""
OUTPUT_DIR = Path('hasil')
MAX_PAGES_PER_PROFILE = 120
DELAY_SECONDS = 1.6
TIMEOUT_SECONDS = 22
USER_AGENT = 'SainsData-UINSU-Publication-Catalog/1.0 (public-academic-metadata)'
DOSEN = [{'slug': 'siddik', 'nama': 'Muhammad Siddik Hasibuan', 'sinta_id': '5983919', 'garuda_ids': ['2406700'], 'perlu_verifikasi_garuda': False}, {'slug': 'dedi', 'nama': 'Muhammad Dedi Irawan', 'sinta_id': '6054939', 'garuda_ids': ['1197451'], 'perlu_verifikasi_garuda': False}, {'slug': 'rakhmat', 'nama': 'Rakhmat Kurniawan R', 'sinta_id': '6160028', 'garuda_ids': ['1733344'], 'perlu_verifikasi_garuda': False}, {'slug': 'aidil', 'nama': 'Aidil Halim Lubis', 'sinta_id': '6795618', 'garuda_ids': ['621444'], 'perlu_verifikasi_garuda': False}, {'slug': 'ika', 'nama': 'Ika Yusnita Sari', 'sinta_id': '6745259', 'garuda_ids': ['7443043'], 'perlu_verifikasi_garuda': True}, {'slug': 'puji', 'nama': 'Puji Sari Ramadhan', 'sinta_id': '6089755', 'garuda_ids': ['10712505'], 'perlu_verifikasi_garuda': False}]
DOCUMENT_RE = re.compile('/documents/detail/(\\d+)(?:[/?#]|$)')
DOI_RE = re.compile('\\b10\\.\\d{4,9}/[^\\s<>"|]+', re.I)
YEAR_RE = re.compile('\\b(?:19|20)\\d{2}\\b')

def normalize(text):
    text = unicodedata.normalize('NFKC', str(text or ''))
    return ' '.join(text.split()).strip()

def normalized_name(name):
    value = unicodedata.normalize('NFKD', normalize(name).lower())
    return re.sub('[^a-z0-9]+', ' ', value).strip()

class Node:

    def __init__(self, tag='root', attrs=(), parent=None):
        self.tag = tag
        self.attrs = dict(attrs or [])
        self.parent = parent
        self.items = []

    def text(self):
        return normalize(' '.join((x.text() if isinstance(x, Node) else x for x in self.items)))

    def walk(self):
        yield self
        for item in self.items:
            if isinstance(item, Node):
                yield from item.walk()

    def links(self):
        return [(n.text(), n.attrs.get('href', ''), n) for n in self.walk() if n.tag == 'a']

    def classes(self):
        return str(self.attrs.get('class', '')).split()

class HTMLTree(HTMLParser):
    VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node()
        self.stack = [self.root]
        self.anchors = []

    def handle_starttag(self, tag, attrs):
        node = Node(tag, attrs, self.stack[-1])
        self.stack[-1].items.append(node)
        if tag == 'a':
            self.anchors.append(node)
        if tag not in self.VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in self.VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        for idx in range(len(self.stack) - 1, 0, -1):
            if self.stack[idx].tag == tag:
                del self.stack[idx:]
                return

    def handle_data(self, data):
        if not any((n.tag in ('script', 'style', 'noscript') for n in self.stack)):
            self.stack[-1].items.append(data)

def parse_html(html):
    doc = HTMLTree()
    doc.feed(html)
    return doc.root

def fetch_public(url):
    """One public GET, never repeats a forbidden/rate-limited response."""
    req = Request(url, headers={'User-Agent': USER_AGENT, 'Accept': 'text/html,application/xhtml+xml', 'Accept-Language': 'id-ID,id;q=0.9,en;q=0.8'})
    try:
        with urlopen(req, timeout=TIMEOUT_SECONDS) as response:
            status = response.getcode()
            final = response.geturl()
            content_type = response.headers.get('Content-Type', '')
            if status != 200:
                return {'status': status, 'html': '', 'url': final, 'error': f'HTTP {status}'}
            if 'html' not in content_type.lower():
                return {'status': status, 'html': '', 'url': final, 'error': 'Respons bukan HTML'}
            raw = response.read(4000001)
            if len(raw) > 4000000:
                return {'status': status, 'html': '', 'url': final, 'error': 'HTML terlalu besar'}
            return {'status': status, 'html': raw.decode('utf-8', 'replace'), 'url': final, 'error': ''}
    except HTTPError as error:
        return {'status': error.code, 'html': '', 'url': url, 'error': f'HTTP {error.code}, dihentikan tanpa mencoba menghindari pembatasan'}
    except (URLError, TimeoutError, OSError) as error:
        return {'status': None, 'html': '', 'url': url, 'error': str(error)[:180]}

def bounded_article_container(anchor):
    current = anchor
    best = None
    for _ in range(11):
        current = current.parent
        if current is None:
            break
        count = sum((bool(DOCUMENT_RE.search(str(href))) for _, href, _ in current.links()))
        text = current.text()
        if count > 1 or len(text) > 15000:
            break
        if count == 1:
            best = current
            if 'Publisher' in text or 'Original Source' in text or 'Show Abstract' in text or ('DOI:' in text):
                return current
    return best or anchor

def extract_doi(container):
    for label, href, _ in container.links():
        url = urljoin('https://garuda.kemdiktisaintek.go.id', str(href))
        if urlparse(url).netloc.lower() in ('doi.org', 'dx.doi.org'):
            return urlparse(url).path.lstrip('/').strip() or None
        if 'DOI:' in label:
            match = DOI_RE.search(label)
            if match:
                return match.group(0).rstrip('.,;)')
    match = DOI_RE.search(container.text())
    return match.group(0).rstrip('.,;)') if match else None

def parse_publications(html, base_url, source_id, source_page):
    doc = parse_html(html)
    results = []
    seen = set()
    for anchor in doc.walk():
        if anchor.tag != 'a':
            continue
        link = urljoin(base_url, str(anchor.attrs.get('href', '')))
        if urlparse(link).netloc != 'garuda.kemdiktisaintek.go.id':
            continue
        match = DOCUMENT_RE.search(urlparse(link).path)
        if not match:
            continue
        document_id = match.group(1)
        if document_id in seen:
            continue
        title = normalize(anchor.text())
        if len(title) < 8 or title.lower() in ('read more', 'download', 'detail'):
            continue
        seen.add(document_id)
        container = bounded_article_container(anchor)
        text = container.text()
        links = [(normalize(label), urljoin(base_url, str(href))) for label, href, _ in container.links()]
        source_url = next((href for label, href in links if 'original source' in label.lower()), None)
        authors = []
        for label, href in links:
            if re.search('/author/view/\\d+', urlparse(href).path):
                cleaned = re.split('\\b(?:Show Abstract|Download Original|Original Source)\\b', label, maxsplit=1, flags=re.I)[0]
                cleaned = normalize(cleaned).strip(' ;|')
                if cleaned and cleaned not in authors:
                    authors.append(cleaned)
        doi = extract_doi(container)
        year = None
        year_match = YEAR_RE.search(text)
        if year_match:
            year = int(year_match.group(0))
        jurnal = None
        if 'Publisher' in text:
            before = text.split('Publisher', 1)[0]
            if title in before:
                guess = normalize(before.split(title, 1)[-1])
                for author in authors:
                    guess = guess.lstrip(' ;,|:-')
                    guess = re.sub('^' + re.escape(author) + '\\s*', '', guess, count=1, flags=re.I)
                guess = guess.strip(' ;,|:-')
                if 5 <= len(guess) <= 250 and 'Show Abstract' not in guess and ('Download Original' not in guess):
                    jurnal = guess
        results.append({'judul': title, 'penulis': '; '.join(authors) if authors else None, 'jurnal': jurnal, 'tahun': year, 'doi': doi, 'url_doi': 'https://doi.org/' + doi if doi else None, 'url_garuda': link, 'url_artikel': source_url, 'peringkat_sinta': None, 'status_indeks_scopus': None, 'garuda_document_id': document_id, 'garuda_author_id': source_id, 'halaman_sumber': source_page})
    return results

def page_numbers(html, author_id):
    """Hanya referensi paginasi pada profil penulis yang sama."""
    doc = parse_html(html)
    nums = set()
    for node in doc.walk():
        if node.tag != 'a':
            continue
        target = urljoin('https://garuda.kemdiktisaintek.go.id', str(node.attrs.get('href', '')))
        path = urlparse(target).path.rstrip('/')
        if path != f'/author/view/{author_id}':
            continue
        values = parse_qs(urlparse(target).query).get('page', [])
        for value in values:
            if value.isdigit() and 1 <= int(value) <= MAX_PAGES_PER_PROFILE:
                nums.add(int(value))
    return nums

def harvest_author(author_id, slug):
    base = f'https://garuda.kemdiktisaintek.go.id/author/view/{author_id}'
    all_items = []
    seen = set()
    pages = []
    failure = ''
    max_known = 1
    consecutive_repeats = 0
    page = 1
    while page <= MAX_PAGES_PER_PROFILE:
        if page > 1:
            time.sleep(DELAY_SECONDS)
        url = base + '?page=' + str(page)
        fetched = fetch_public(url)
        status = fetched['status']
        if fetched['error']:
            failure = f"Halaman {page}: {fetched['error']}"
            pages.append({'page': page, 'http_status': status, 'count': 0, 'error': failure})
            break
        html = fetched['html']
        items = parse_publications(html, url, author_id, page)
        fresh = [a for a in items if a['garuda_document_id'] not in seen]
        for article in fresh:
            seen.add(article['garuda_document_id'])
            all_items.append(article)
        pages.append({'page': page, 'http_status': status, 'count': len(items), 'new': len(fresh)})
        max_known = max([max_known] + list(page_numbers(html, author_id)))
        print(f'  {slug} GARUDA {author_id}: halaman {page}, {len(items)} entri, {len(fresh)} baru', flush=True)
        if not items:
            break
        if not fresh:
            consecutive_repeats += 1
            if consecutive_repeats >= 2:
                break
        else:
            consecutive_repeats = 0
        page += 1
    if page > MAX_PAGES_PER_PROFILE:
        failure = f'Melebihi batas pengaman {MAX_PAGES_PER_PROFILE} halaman; periksa paginasi.'
    return {'garuda_author_id': author_id, 'url': base, 'pages': pages, 'articles': all_items, 'error': failure, 'completed': not bool(failure)}

def sinta_summary(html, expected_name):
    doc = parse_html(html)
    summary = {'sinta_score_overall': None, 'sinta_score_3yr': None, 'scopus': {'artikel': None, 'sitasi': None, 'dokumen_tersitasi': None, 'h_index': None, 'i10_index': None}, 'peringkat_jurnal': None}
    numbers = [node.text() for node in doc.walk() if 'pr-num' in node.classes()]

    def to_num(value):
        cleaned = str(value).strip().replace('.', '').replace(',', '')
        return int(cleaned) if cleaned.isdigit() else None
    if len(numbers) >= 2:
        summary['sinta_score_overall'] = to_num(numbers[0])
        summary['sinta_score_3yr'] = to_num(numbers[1])
    keys = {'article': 'artikel', 'citation': 'sitasi', 'cited document': 'dokumen_tersitasi', 'h-index': 'h_index', 'i10-index': 'i10_index'}
    for node in doc.walk():
        if node.tag != 'table' or 'stat-table' not in node.classes():
            continue
        for tr in node.walk():
            if tr.tag != 'tr':
                continue
            cells = [n.text() for n in tr.items if isinstance(n, Node) and n.tag in ('td', 'th')]
            if len(cells) < 2:
                continue
            key = normalize(cells[0]).lower()
            if key in keys:
                summary['scopus'][keys[key]] = to_num(cells[1])
        break
    plain = normalized_name(doc.text())
    match_name = normalized_name(expected_name) in plain
    return (summary, match_name)

def harvest_sinta(sinta_id, name):
    url = f'https://sinta.kemdiktisaintek.go.id/authors/profile/{sinta_id}'
    time.sleep(DELAY_SECONDS)
    fetched = fetch_public(url)
    if fetched['error']:
        return {'url': url, 'http_status': fetched['status'], 'error': fetched['error'], 'metrics': None, 'nama_tercocokkan': False}
    metrics, valid_name = sinta_summary(fetched['html'], name)
    return {'url': url, 'http_status': fetched['status'], 'error': None if valid_name else 'Nama penulis tidak cocok', 'metrics': metrics if valid_name else None, 'nama_tercocokkan': valid_name}

def deduplicate(articles):
    """Simpan tiap ID dokumen GARUDA sekali, meskipun DOI digunakan ulang.

    Deduplikasi DOI untuk menghitung karya unik tingkat prodi dilakukan pada
    tahap rekapitulasi, bukan pada tahap pengarsipan hasil profil GARUDA.
    """
    out = []
    seen = set()
    for a in articles:
        document_id = str(a.get('garuda_document_id') or '').strip()
        if document_id:
            key = ('garuda_document_id', document_id)
        else:
            # Perlindungan data lama tanpa ID: jangan hilangkan DOI berbeda
            # dan jangan gabung judul yang berbeda dengan DOI sama.
            key = ('riwayat', str(a.get('url_garuda') or '').strip(),
                   str(a.get('judul') or '').strip().casefold(),
                   str(a.get('tahun') or ''))
        if key in seen:
            continue
        seen.add(key)
        out.append(a)
    return out

def save_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')

def garuda_main():
    # Jangan hilangkan karya ilmiah historis ketika GARUDA gagal mengembalikan
    # seluruh halaman. Basis lama dipakai sebagai cache defensif.
    previous = {}
    previous_path = OUTPUT_DIR / 'publikasi_dosen.json'
    try:
        previous = json.loads(previous_path.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        previous = {}
    previous_people = {d['slug']: d for d in previous.get('dosen', [])
                       if isinstance(d, dict) and isinstance(d.get('slug'), str)}
    started = datetime.now(timezone.utc).isoformat()
    output = {'versi': '1.0', 'diperbarui_utc': started, 'sumber': 'GARUDA dan halaman profil publik SINTA', 'catatan': 'Peringkat jurnal dan indeks Scopus setiap artikel belum diverifikasi otomatis.', 'dosen': []}
    diagnostics = {'diperbarui_utc': started, 'dosen': []}
    # Identitas profil hanya diberi label valid jika telah dikonfirmasi pengguna.
    try:
        confirmed = json.loads(Path('data/profil_garuda_tervalidasi.json').read_text(encoding='utf-8'))
        confirmed_ids = {p['slug']: set(str(v) for v in p.get('garuda_author_ids', []))
                         for p in confirmed.get('dosen', [])}
    except (OSError, ValueError, KeyError, TypeError):
        confirmed_ids = {}
    for author in DOSEN:
        slug = author['slug']
        print(f"\nMemproses {author['nama']} (SINTA {author['sinta_id']})", flush=True)
        author_reports = []
        articles = []
        for garuda_id in author['garuda_ids']:
            report = harvest_author(garuda_id, slug)
            articles.extend(report['articles'])
            author_reports.append({k: v for k, v in report.items() if k != 'articles'})
        articles = deduplicate(articles)
        prev_entry = previous_people.get(slug, {})
        prev_articles = prev_entry.get('publikasi_garuda', [])
        if not isinstance(prev_articles, list):
            prev_articles = []
        # Riwayat artikel sifatnya kumulatif: jangan hilangkan artikel yang
        # sudah terambil pada siklus sebelumnya hanya karena situs bermasalah.
        count_new = len(articles)
        if prev_articles:
            articles = deduplicate(articles + prev_articles)
        used_cache = bool(prev_articles) and count_new < len(prev_articles)
        if used_cache:
            print(f'  {slug}: GARUDA memberi {count_new} rekaman; '
                  f'{len(articles)} rekaman dipertahankan dengan riwayat terakhir', flush=True)
        sinta = harvest_sinta(author['sinta_id'], author['nama'])
        if sinta['metrics'] is None and prev_entry.get('metrik_sinta'):
            sinta['metrics'] = prev_entry['metrik_sinta']
            sinta['error'] = 'Menggunakan metrik SINTA terverifikasi terakhir; pengambilan baru gagal'
        status = 'lengkap' if all((r['completed'] for r in author_reports)) else 'sebagian'
        if not articles:
            status = 'belum_tersedia'
        elif used_cache:
            status = 'menggunakan_riwayat_tersimpan'
        if author['perlu_verifikasi_garuda'] and status == 'lengkap':
            status = 'perlu_verifikasi_identitas_garuda'
        valid_profile = bool(author['garuda_ids']) and all(
            str(v) in confirmed_ids.get(slug, set()) for v in author['garuda_ids'])
        entry = {'profil_garuda_terkonfirmasi': valid_profile,
                 'slug': slug, 'nama': author['nama'], 'sinta_id': author['sinta_id'], 'sinta_url': sinta['url'], 'garuda_author_ids': author['garuda_ids'], 'perlu_verifikasi_identitas_garuda': author['perlu_verifikasi_garuda'], 'status': status, 'jumlah_artikel_terambil': len(articles), 'metrik_sinta': sinta['metrics'], 'metrik_sinta_status': sinta['error'] or 'berhasil', 'publikasi_garuda': articles}
        output['dosen'].append(entry)
        diagnostics['dosen'].append({'profil_garuda_terkonfirmasi': valid_profile, 'slug': slug, 'nama': author['nama'], 'sinta_id': author['sinta_id'], 'jumlah_artikel': len(articles), 'status': status, 'profil_garuda': author_reports, 'sinta': {k: v for k, v in sinta.items() if k != 'metrics'}})
        print(f"  {slug}: {len(articles)} artikel; status={status}; SINTA: {sinta['error'] or 'berhasil'}", flush=True)
    if len(output.get('dosen', [])) != 6 or any((len(x.get('publikasi_garuda', [])) == 0 for x in output.get('dosen', []))):
        raise RuntimeError('GARUDA menghasilkan data kosong/tidak lengkap. File publikasi sebelumnya dipertahankan.')
    save_json(OUTPUT_DIR / 'publikasi_dosen.json', output)
    save_json(OUTPUT_DIR / 'diagnostik_sinta.json', diagnostics)
    with (OUTPUT_DIR / 'publikasi_dosen.csv').open('w', newline='', encoding='utf-8-sig') as handle:
        fields = ['dosen', 'sinta_id', 'judul', 'penulis', 'jurnal', 'tahun', 'doi', 'url_doi', 'url_garuda', 'url_artikel', 'garuda_author_id', 'peringkat_sinta', 'status_indeks_scopus']
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for entry in output['dosen']:
            for article in entry['publikasi_garuda']:
                writer.writerow({**{k: article.get(k) for k in fields}, 'dosen': entry['nama'], 'sinta_id': entry['sinta_id']})
    print('\nHasil tersedia di folder hasil/:', flush=True)
    for file in sorted(OUTPUT_DIR.iterdir()):
        print(f'  {file} ({file.stat().st_size:,} byte)', flush=True)


# ===== 2. PENGAYAAN SINTA =====


"""Pencocokan jurnal GARUDA -> SINTA untuk Prodi Sains Data.

Prinsip kehati-hatian:
- Direktori/profil jurnal SINTA memberi peringkat TERKINI, bukan selalu peringkat
  yang berlaku pada tahun publikasi artikel.
- `peringkat_sinta` hanya diisi dari bukti spesifik DOI pada profil SINTA
  ATAU dari periode akreditasi ber-URL bukti yang telah diverifikasi.
- Akses SINTA 403/429 dihentikan; data cache resmi yang lama dipertahankan.
- Tidak memerlukan API berbayar, login, proxy, CAPTCHA bypass, atau token.

Pemakaian setelah cek_sinta.py: python cocokkan_jurnal_sinta.py
"""
sinta_SOURCE = Path('hasil/publikasi_dosen.json')
sinta_CACHE_PATH = Path('hasil/cache_jurnal_sinta.json')
sinta_RECAP_PATH = Path('hasil/rekap_sinta.json')
sinta_RECAP_CSV_PATH = Path('hasil/rekap_sinta.csv')
sinta_ARTICLES_CSV_PATH = Path('hasil/publikasi_dosen.csv')
sinta_DIAG_PATH = Path('hasil/diagnostik_pencocokan_sinta.json')
sinta_RULES_PATH = Path('data/akreditasi_jurnal_terverifikasi.json')
sinta_SINTA_HOST = 'sinta.kemdiktisaintek.go.id'
sinta_SINTA_BASE = 'https://' + sinta_SINTA_HOST
sinta_RECHECK_DAYS = 35
sinta_DELAY = 1.5
sinta_HTTP_TIMEOUT = 20
sinta_MAX_REQUESTS = 450
sinta_USER_AGENT = 'SainsData-UINSU-Publication-Catalog/1.1 (public-metadata; respectful-rate-limit)'
sinta_VOL_RE = re.compile('\\s+(?:Vol(?:ume)?\\.?|Volume|V\\.)\\s*\\d+\\b', re.I)
sinta_DOI_RE = re.compile('\\b10\\.\\d{4,9}/[^\\s<>"|]+', re.I)
sinta_RANK_RE = re.compile('\\b(?:SINTA\\s*([1-6])|S([1-6])\\s+Accredited)\\b', re.I)
sinta_ACCRED_ARTICLE_RE = re.compile('\\bDOI\\s*:\\s*(10\\.\\d{4,9}/[^\\s<>"|]+)\\s+Accred\\s*:\\s*Sinta\\s*([1-6])\\b', re.I)
sinta_ISSN_RE = re.compile('\\b(?:[PE][ -]?ISSN)\\s*:\\s*([\\dXx\\-]{8,10})\\b', re.I)

def sinta_read_json(path, default):
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except (FileNotFoundError, ValueError):
        return default

def sinta_save_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temp.replace(path)

def sinta_clean_str(s):
    return ' '.join(unicodedata.normalize('NFKC', str(s or '')).split()).strip()

def sinta_title_from_garuda(s):
    """GARUDA sering menggabungkan nama jurnal dengan Volume/No/Edisi."""
    text = sinta_clean_str(s)
    text = sinta_VOL_RE.split(text, maxsplit=1)[0].strip(' ,:;-')
    text = re.split('\\s+(?:No\\.?|Nomor|Issue)\\s*\\d+\\b', text, maxsplit=1, flags=re.I)[0].strip(' ,:;-')
    return text

def sinta_key_name(s):
    s = unicodedata.normalize('NFKD', sinta_clean_str(s).casefold())
    s = ''.join((c for c in s if not unicodedata.combining(c)))
    return re.sub('[^a-z0-9]+', ' ', s).strip()

def sinta_key_issn(s):
    return re.sub('[^0-9X]', '', str(s or '').upper())

def sinta_key_doi(s):
    value = sinta_clean_str(s).lower().replace('https://doi.org/', '').replace('http://doi.org/', '')
    value = value.strip(' "\'.,;<>)]}')
    m = sinta_DOI_RE.search(value)
    return m.group(0).rstrip('.,;)') if m else ''

def sinta_safe_sinta_url(url):
    url = sinta_clean_str(url)
    p = urlparse(url)
    return url if p.scheme == 'https' and p.netloc.lower() == sinta_SINTA_HOST and re.fullmatch('/journals/profile/\\d+/?', p.path) else ''

def sinta_now_utc():
    return datetime.now(timezone.utc)

class sinta_PublicFetcher:

    def __init__(self):
        self.block_sinta = False
        self.requests_used = 0
        self.events = []

    def get(self, url):
        host = urlparse(url).hostname or ''
        if host != sinta_SINTA_HOST:
            raise ValueError('Hanya halaman publik resmi SINTA yang boleh diambil')
        if self.block_sinta or self.requests_used >= sinta_MAX_REQUESTS:
            return None
        if self.requests_used:
            time.sleep(sinta_DELAY)
        self.requests_used += 1
        req = Request(url, headers={'User-Agent': sinta_USER_AGENT, 'Accept': 'text/html,application/xhtml+xml', 'Accept-Language': 'id-ID,id;q=0.9,en;q=0.8'})
        try:
            with urlopen(req, timeout=sinta_HTTP_TIMEOUT) as response:
                final = response.geturl()
                if urlparse(final).hostname != sinta_SINTA_HOST:
                    self.events.append('Pengalihan ke domain lain diabaikan')
                    return None
                if response.status != 200 or 'html' not in response.headers.get('Content-Type', '').lower():
                    self.events.append('Respons bukan HTML HTTP 200')
                    return None
                data = response.read(2500001)
                if len(data) > 2500000:
                    self.events.append('HTML terlalu besar, dilewati')
                    return None
                return data.decode('utf-8', 'replace')
        except HTTPError as ex:
            if ex.code in (403, 429):
                self.block_sinta = True
                self.events.append(f'SINTA HTTP {ex.code}; tidak ada upaya menghindari pembatasan')
            else:
                self.events.append(f'HTTP {ex.code} pada {urlparse(url).path}')
        except (URLError, TimeoutError, OSError) as ex:
            self.events.append(f'Koneksi SINTA gagal: {type(ex).__name__}')
        return None

def sinta_parse_listing(html):
    doc = parse_html(html)
    result = []
    visited = set()
    for anchor in doc.walk():
        if anchor.tag != 'a':
            continue
        href = str(anchor.attrs.get('href', ''))
        hit = re.search('/journals/profile/(\\d+)(?:[/?#]|$)', href)
        if not hit or hit.group(1) in visited:
            continue
        journal_id = hit.group(1)
        name = sinta_clean_str(anchor.text())
        parent = anchor
        snippet = ''
        for depth in range(7):
            parent = parent.parent
            if parent is None:
                break
            text = sinta_clean_str(parent.text())
            ids = {m.group(1) for label, link, el in parent.links() for m in re.finditer('/journals/profile/(\\d+)', str(link))}
            if len(text) <= 1200 and len(ids) == 1 and sinta_RANK_RE.search(text):
                snippet = text
                break
            if len(text) > 4500 or len(ids) > 1:
                break
        if not snippet:
            continue
        r = sinta_RANK_RE.search(snippet)
        rank = int(r.group(1) or r.group(2)) if r else None
        if (len(name) < 5 or len(name) > 240) and parent is not None:
            for item in parent.walk():
                if item.tag in ('h3', 'h4', 'h5', 'strong'):
                    name = sinta_clean_str(item.text())
                    if name:
                        break
        if not name or rank not in range(1, 7):
            continue
        issns = sorted({sinta_key_issn(v) for v in sinta_ISSN_RE.findall(snippet) if len(sinta_key_issn(v)) == 8})
        result.append({'judul': name, 'peringkat_terkini': rank, 'issn': issns, 'sinta_url': f'{sinta_SINTA_BASE}/journals/profile/{journal_id}'})
        visited.add(journal_id)
    return result

def sinta_normalize_name_match(a, b):
    left, right = (sinta_key_name(a), sinta_key_name(b))
    if not left or not right:
        return 0
    if left == right:
        return 1.0
    aliases = [sinta_key_name(x) for x in re.findall('\\(([^)]+)\\)', str(a)) + re.findall('\\(([^)]+)\\)', str(b))]
    if left in aliases or right in aliases:
        return 0.98
    return difflib.SequenceMatcher(None, left, right).ratio()

def sinta_pick_candidate(needle, candidates, issn_hint=None):
    wanted_issn = {sinta_key_issn(x) for x in issn_hint or [] if len(sinta_key_issn(x)) == 8}
    scored = []
    for c in candidates:
        overlap = wanted_issn.intersection(set(c['issn']))
        similarity = sinta_normalize_name_match(needle, c['judul'])
        if overlap and similarity >= 0.65:
            scored.append((2.0 + similarity, c))
        elif similarity >= 0.96:
            scored.append((similarity, c))
    if not scored:
        return None
    scored.sort(key=lambda pair: pair[0], reverse=True)
    if len(scored) > 1 and abs(scored[0][0] - scored[1][0]) < 0.035:
        return None
    return scored[0][1]

def sinta_parse_profile_article_ranks(html):
    text = parse_html(html).text()
    result = {}
    for match in sinta_ACCRED_ARTICLE_RE.finditer(text):
        doi = sinta_key_doi(match.group(1))
        rank = int(match.group(2))
        if doi and rank in range(1, 7):
            result[doi] = rank
    return result

def sinta_load_rules():
    rules = sinta_read_json(sinta_RULES_PATH, {'jurnal': [], 'artikel': []})
    if not isinstance(rules, dict):
        raise ValueError('Format data akreditasi bukan objek JSON')
    journal_rules, article_rules = ([], {})
    for rule in rules.get('jurnal', []):
        if not isinstance(rule, dict):
            continue
        periods = []
        for p in rule.get('periode', []):
            try:
                start, end, rank = (int(p['tahun_mulai']), int(p['tahun_sampai']), int(p['peringkat']))
            except (KeyError, TypeError, ValueError):
                continue
            url = str(p.get('bukti_url', '')).strip()
            if 1900 <= start <= end <= 2100 and 1 <= rank <= 6 and url.startswith('https://'):
                periods.append({'start': start, 'end': end, 'rank': rank, 'bukti': url})
        if periods:
            journal_rules.append({'name': sinta_clean_str(rule.get('nama')), 'issn': [sinta_key_issn(x) for x in rule.get('issn', [])], 'periods': periods, 'sinta_url': sinta_safe_sinta_url(rule.get('sinta_url', ''))})
    for art in rules.get('artikel', []):
        try:
            doi, rank = (sinta_key_doi(art.get('doi')), int(art.get('peringkat')))
            url = str(art.get('bukti_url', '')).strip()
            if doi and rank in range(1, 7) and url.startswith('https://'):
                article_rules[doi] = {'rank': rank, 'bukti': url}
        except (TypeError, ValueError):
            pass
    return (journal_rules, article_rules)

def sinta_manual_period_rule(title, year, issn, journal_rules):
    if not isinstance(year, int):
        return None
    hits = []
    for rule in journal_rules:
        similarity = sinta_normalize_name_match(title, rule['name'])
        exact_issn = bool(set(rule['issn']) & set(issn))
        if similarity < 0.96 and (not (exact_issn and similarity >= 0.65)):
            continue
        for p in rule['periods']:
            if p['start'] <= year <= p['end']:
                hits.append((p['rank'], p['bukti']))
    if not hits or len(set((r[0] for r in hits))) > 1:
        return None
    return {'rank': hits[0][0], 'bukti': hits[0][1]}

def sinta_save_csv_exports(data, recap):
    """CSV mengikuti JSON yang sudah diperkaya; bukan CSV lama sebelum pencocokan."""
    fields = ['dosen', 'sinta_id', 'judul', 'penulis', 'jurnal', 'tahun', 'doi', 'url_doi', 'url_garuda', 'url_artikel', 'garuda_author_id', 'peringkat_sinta', 'sinta_status_verifikasi', 'sinta_bukti_url', 'jurnal_sinta_peringkat_terkini', 'jurnal_sinta_url', 'status_indeks_scopus']
    with sinta_ARTICLES_CSV_PATH.open('w', encoding='utf-8-sig', newline='') as handle:
        out = csv.DictWriter(handle, fieldnames=fields)
        out.writeheader()
        for person in data['dosen']:
            for a in person.get('publikasi_garuda', []):
                row = {'dosen': person.get('nama', ''), 'sinta_id': person.get('sinta_id', '')}
                for k in fields[2:]:
                    row[k] = a.get(k)
                out.writerow({k: '' if v is None else v for k, v in row.items()})
    with sinta_RECAP_CSV_PATH.open('w', encoding='utf-8-sig', newline='') as handle:
        fields2 = ['dosen', 'slug', 'tahun'] + [f'S{i}' for i in range(1, 7)] + ['belum_terverifikasi']
        out = csv.DictWriter(handle, fieldnames=fields2)
        out.writeheader()
        for d in recap['dosen']:
            for year, counts in d['per_tahun'].items():
                row = {'dosen': d['nama'], 'slug': d['slug'], 'tahun': year}
                for rank in range(1, 7):
                    row[f'S{rank}'] = counts.get(f'S{rank}', 0)
                row['belum_terverifikasi'] = counts.get('belum_terverifikasi', 0)
                out.writerow(row)

def sinta_main():
    if not sinta_SOURCE.exists():
        print('ERROR: jalankan cek_sinta.py terlebih dahulu.', file=sys.stderr)
        return 2
    data = sinta_read_json(sinta_SOURCE, {})
    if not isinstance(data.get('dosen'), list):
        print('ERROR: struktur publikasi_dosen.json tidak valid.', file=sys.stderr)
        return 2
    previous = sinta_read_json(sinta_CACHE_PATH, {'jurnal': {}})
    cache = previous.get('jurnal', {}) if isinstance(previous, dict) else {}
    if not isinstance(cache, dict):
        cache = {}
    manual_journals, manual_articles = sinta_load_rules()
    fetcher = sinta_PublicFetcher()
    now = sinta_now_utc()
    now_iso = now.isoformat()
    groups = defaultdict(list)
    for d in data['dosen']:
        for a in d.get('publikasi_garuda', []):
            title = sinta_title_from_garuda(a.get('jurnal', ''))
            if len(sinta_key_name(title)) >= 6:
                groups[sinta_key_name(title)].append((d, a, title))
    fresh, from_cache = (0, 0)
    for key, items in sorted(groups.items(), key=lambda e: -len(e[1])):
        entry = cache.get(key, {})
        expires = False
        try:
            checked = datetime.fromisoformat(entry['checked_at'])
            expires = checked.tzinfo is None or now - checked > timedelta(days=sinta_RECHECK_DAYS)
        except (ValueError, KeyError, TypeError):
            expires = True
        if not expires:
            from_cache += 1
            continue
        if fetcher.block_sinta or fetcher.requests_used >= sinta_MAX_REQUESTS:
            continue
        name = items[0][2]
        if not name or re.search('\\b(?:conference|seminar|proceedings)\\b', name, re.I):
            continue
        query = urlencode({'q': name})
        html = fetcher.get(f'{sinta_SINTA_BASE}/journals?{query}')
        if not html:
            continue
        candidates = sinta_parse_listing(html)
        candidate = sinta_pick_candidate(name, candidates)
        fresh += 1
        if candidate is None:
            if entry.get('status') == 'tercocokkan':
                cache[key] = entry
            else:
                cache[key] = {'nama_garuda': name, 'checked_at': now_iso, 'status': 'belum_cocok', 'sinta_url': None, 'peringkat_terkini': None, 'doi_artikel': {}, 'issn': []}
            continue
        profile_html = fetcher.get(candidate['sinta_url'])
        doi_article = sinta_parse_profile_article_ranks(profile_html) if profile_html else {}
        previous_verified = entry.get('doi_artikel', {}) if isinstance(entry.get('doi_artikel'), dict) else {}
        previous_verified.update(doi_article)
        cache[key] = {'nama_garuda': name, 'nama_sinta': candidate['judul'], 'checked_at': now_iso, 'status': 'tercocokkan', 'sinta_url': candidate['sinta_url'], 'peringkat_terkini': candidate['peringkat_terkini'], 'issn': candidate['issn'], 'doi_artikel': previous_verified}
        print(f"[SINTA] {name[:48]} => S{candidate['peringkat_terkini']}; DOI spesifik={len(previous_verified)}")
    verified_count = 0
    rank_current_count = 0
    per_dosen = []
    by_year_all = defaultdict(Counter)
    for d in data['dosen']:
        count = Counter()
        year_count = defaultdict(Counter)
        for a in d.get('publikasi_garuda', []):
            title = sinta_title_from_garuda(a.get('jurnal'))
            record = cache.get(sinta_key_name(title), {})
            year = a.get('tahun')
            year = int(year) if str(year).isdigit() and 1900 <= int(year) <= 2100 else None
            doi = sinta_key_doi(a.get('doi'))
            rank = None
            source = None
            evidence = None
            if doi in manual_articles:
                rank = manual_articles[doi]['rank']
                evidence = manual_articles[doi]['bukti']
                source = 'bukti_artikel_terverifikasi'
            elif doi and doi in record.get('doi_artikel', {}):
                rank = int(record['doi_artikel'][doi])
                evidence = record.get('sinta_url')
                source = 'doi_pada_profil_jurnal_sinta'
            else:
                period = sinta_manual_period_rule(title, year, record.get('issn', []), manual_journals)
                if period:
                    rank = period['rank']
                    evidence = period['bukti']
                    source = 'periode_sk_terverifikasi'
            a['peringkat_sinta'] = rank
            a['sinta_status_verifikasi'] = source or 'belum_terverifikasi'
            a['sinta_bukti_url'] = evidence
            a['jurnal_sinta_url'] = record.get('sinta_url') or None
            a['jurnal_sinta_peringkat_terkini'] = record.get('peringkat_terkini')
            if record.get('peringkat_terkini') in range(1, 7):
                rank_current_count += 1
            if rank in range(1, 7):
                verified_count += 1
                count[f'S{rank}'] += 1
                if year is not None:
                    year_count[str(year)][f'S{rank}'] += 1
                    by_year_all[str(year)][f'S{rank}'] += 1
            else:
                count['belum_terverifikasi'] += 1
                if year is not None:
                    year_count[str(year)]['belum_terverifikasi'] += 1
                    by_year_all[str(year)]['belum_terverifikasi'] += 1
        d['rekap_sinta'] = {**{f'S{i}': count[f'S{i}'] for i in range(1, 7)}, 'belum_terverifikasi': count['belum_terverifikasi']}
        per_dosen.append({'slug': d['slug'], 'nama': d['nama'], 'total': len(d.get('publikasi_garuda', [])), 'peringkat': d['rekap_sinta'], 'per_tahun': {y: dict(x) for y, x in sorted(year_count.items(), reverse=True)}})
    data['sinta_pencocokan_utc'] = now_iso
    data['sinta_metode'] = 'Pencocokan jurnal berdasarkan nama/ISSN; peringkat artikel hanya dari bukti DOI atau periode SK yang diverifikasi'
    data['catatan_sinta'] = 'Peringkat SINTA terkini jurnal tidak otomatis berlaku untuk seluruh tahun artikel. Belum terverifikasi bukan berarti SINTA 0.'
    recap = {'diperbarui_utc': now_iso, 'total_rekaman': sum((len(d.get('publikasi_garuda', [])) for d in data['dosen'])), 'artikel_sinta_terverifikasi': verified_count, 'artikel_belum_terverifikasi': sum((d['rekap_sinta']['belum_terverifikasi'] for d in data['dosen'])), 'dosen': per_dosen, 'rekap_tahunan': {y: dict(v) for y, v in sorted(by_year_all.items(), reverse=True)}, 'catatan': 'Jumlah merupakan rekaman per dosen; kolaborasi bisa terhitung lebih dari sekali.'}
    diagnostics = {'waktu': now_iso, 'jurnal_unik': len(groups), 'lookup_baru': fresh, 'lookup_dari_cache': from_cache, 'request_sinta': fetcher.requests_used, 'sinta_diblokir': fetcher.block_sinta, 'peristiwa': fetcher.events[:50], 'artikel_peringkat_terverifikasi': verified_count, 'artikel_jurnal_terkini_diketahui': rank_current_count, 'catatan': 'Saat server memblokir akses, skrip tidak menghindari pembatasan dan mempertahankan cache.'}
    sinta_save_json(sinta_SOURCE, data)
    sinta_save_json(sinta_RECAP_PATH, recap)
    sinta_save_csv_exports(data, recap)
    sinta_save_json(sinta_CACHE_PATH, {'versi': 1, 'jurnal': cache})
    sinta_save_json(sinta_DIAG_PATH, diagnostics)
    print(f"Selesai: {len(groups)} jurnal; {verified_count} artikel status SINTA terverifikasi; {diagnostics['artikel_jurnal_terkini_diketahui']} artikel memiliki info peringkat jurnal terkini; {fetcher.requests_used} permintaan; blokir={fetcher.block_sinta}.")
    return 0


# ===== 3. VERIFIKASI SCOPUS =====


"""Verifikasi DOI publikasi GARUDA pada Scopus (API Elsevier resmi).

Bekerja tanpa API key: tidak menandai artikel sebagai terindeks atau tidak
terindeks jika belum ada bukti. Hanya kecocokan DOI + EID yang valid dari API
Elsevier atau data manual ber-URL resmi yang diterima sebagai bukti.

Pemakaian: python cek_scopus.py
GitHub Secret opsional: SCOPUS_API_KEY (dan SCOPUS_INST_TOKEN bila diberikan).
"""
scopus_SOURCE = Path('hasil/publikasi_dosen.json')
scopus_CACHE_FILE = Path('hasil/cache_artikel_scopus.json')
scopus_RECAP_FILE = Path('hasil/rekap_scopus.json')
scopus_RECAP_CSV = Path('hasil/rekap_scopus.csv')
scopus_DIAG_FILE = Path('hasil/diagnostik_scopus.json')
scopus_ARTICLES_CSV = Path('hasil/publikasi_dosen.csv')
scopus_MANUAL_FILE = Path('data/scopus_terverifikasi.json')
scopus_API_HOST = 'api.elsevier.com'
scopus_API_ENDPOINT = 'https://api.elsevier.com/content/search/scopus'
scopus_MAX_REQUESTS = max(1, min(int(os.environ.get('SCOPUS_MAX_REQUESTS', '100')), 1000))
scopus_CACHE_DAYS = 60
scopus_REQUEST_DELAY = 0.5
scopus_DOI_RE = re.compile('^10\\.\\d{4,9}/\\S+$', re.I)
scopus_EID_RE = re.compile('^2-s2\\.0-\\d{6,20}$', re.I)

def scopus_load_json(path, fallback):
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return fallback

def scopus_write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    staged = path.with_suffix(path.suffix + '.tmp')
    staged.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    staged.replace(path)

def scopus_doi_key(value):
    value = str(value or '').strip().lower()
    value = re.sub('^https?://(?:dx\\.)?doi\\.org/', '', value)
    value = value.strip(' "\'<>.,;)')
    return value if scopus_DOI_RE.fullmatch(value) else ''

def scopus_now_utc():
    return datetime.now(timezone.utc)

def scopus_scopus_record(eid):
    if not scopus_EID_RE.fullmatch(str(eid or '')):
        return ''
    return 'https://www.scopus.com/record/display.uri?' + urlencode({'eid': eid})

def scopus_verified_manual():
    raw = scopus_load_json(scopus_MANUAL_FILE, {'artikel': []})
    if not isinstance(raw, dict) or not isinstance(raw.get('artikel'), list):
        return {}
    out = {}
    for item in raw['artikel']:
        if not isinstance(item, dict):
            continue
        doi = scopus_doi_key(item.get('doi'))
        eid = str(item.get('eid') or '')
        proof = str(item.get('bukti_url') or '').strip()
        parsed = urlparse(proof)
        if doi and scopus_EID_RE.fullmatch(eid) and (parsed.scheme == 'https') and (parsed.hostname in ('www.scopus.com', 'api.elsevier.com', 'scopus.com')):
            out[doi] = {'status': 'verified', 'eid': eid, 'url': proof, 'source': 'bukti_scopus_manual_terverifikasi'}
    return out

class scopus_ScopusAPI:

    def __init__(self):
        self.key = os.environ.get('SCOPUS_API_KEY', '').strip()
        self.inst = os.environ.get('SCOPUS_INST_TOKEN', '').strip()
        self.request_count = 0
        self.blocked = False
        self.events = []

    def check(self, doi):
        if not self.key or self.blocked or self.request_count >= scopus_MAX_REQUESTS:
            return None
        if self.request_count:
            time.sleep(scopus_REQUEST_DELAY)
        self.request_count += 1
        params = urlencode({'query': 'DOI("' + doi.replace('"', '') + '")', 'count': 2, 'view': 'STANDARD'})
        url = scopus_API_ENDPOINT + '?' + params
        headers = {'Accept': 'application/json', 'X-ELS-APIKey': self.key, 'User-Agent': 'SainsData-UINSU-Publication-Verifier/1.0'}
        if self.inst:
            headers['X-ELS-Insttoken'] = self.inst
        req = Request(url, headers=headers)
        try:
            with urlopen(req, timeout=25) as resp:
                if urlparse(resp.geturl()).hostname != scopus_API_HOST:
                    self.events.append('Pengalihan API keluar domain Elsevier ditolak')
                    return None
                raw = resp.read(1500001)
                if len(raw) > 1500000:
                    self.events.append('Respons terlalu besar')
                    return None
                payload = json.loads(raw.decode('utf-8'))
        except HTTPError as ex:
            self.events.append('Scopus API HTTP ' + str(ex.code))
            if ex.code in (401, 403, 429):
                self.blocked = True
            return None
        except (OSError, URLError, TimeoutError, ValueError) as ex:
            self.events.append('Kesalahan Scopus API: ' + type(ex).__name__)
            return None
        entries = payload.get('search-results', {}).get('entry', [])
        if not isinstance(entries, list):
            return None
        for result in entries:
            if not isinstance(result, dict):
                continue
            returned_doi = scopus_doi_key(result.get('prism:doi'))
            eid = str(result.get('eid') or '')
            if returned_doi == doi and scopus_EID_RE.fullmatch(eid):
                return {'status': 'verified', 'eid': eid, 'url': scopus_scopus_record(eid), 'source': 'elsevier_scopus_search_api'}
        return {'status': 'not_found_unconfirmed', 'checked_at': scopus_now_utc().isoformat()}

def scopus_cache_recent(entry, now):
    if entry.get('status') == 'verified':
        return True
    try:
        checked = datetime.fromisoformat(entry['checked_at'])
        return checked.tzinfo is not None and now - checked <= timedelta(days=scopus_CACHE_DAYS)
    except (ValueError, KeyError, TypeError):
        return False

def scopus_save_article_csv(data):
    fields = ['dosen', 'sinta_id', 'judul', 'penulis', 'jurnal', 'tahun', 'doi', 'url_doi', 'url_garuda', 'url_artikel', 'garuda_author_id', 'peringkat_sinta', 'sinta_status_verifikasi', 'sinta_bukti_url', 'jurnal_sinta_peringkat_terkini', 'jurnal_sinta_url', 'status_indeks_scopus', 'scopus_status_verifikasi', 'scopus_eid', 'scopus_url', 'scopus_bukti_url']
    with scopus_ARTICLES_CSV.open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for person in data['dosen']:
            for paper in person.get('publikasi_garuda', []):
                row = {'dosen': person.get('nama', ''), 'sinta_id': person.get('sinta_id', '')}
                row.update({k: paper.get(k) for k in fields[2:]})
                writer.writerow({k: '' if v is None else v for k, v in row.items()})

def scopus_main():
    data = scopus_load_json(scopus_SOURCE, {})
    if not isinstance(data, dict) or not isinstance(data.get('dosen'), list):
        print('ERROR: hasil/publikasi_dosen.json belum tersedia; jalankan cek_sinta.py dulu.', file=sys.stderr)
        return 2
    old = scopus_load_json(scopus_CACHE_FILE, {'artikel': {}})
    cache = old.get('artikel', {}) if isinstance(old, dict) else {}
    if not isinstance(cache, dict):
        cache = {}
    verified = scopus_verified_manual()
    unique_doi = set()
    for person in data['dosen']:
        for paper in person.get('publikasi_garuda', []):
            key = scopus_doi_key(paper.get('doi'))
            if key:
                unique_doi.add(key)
    api = scopus_ScopusAPI()
    now = scopus_now_utc()
    for doi in sorted(unique_doi):
        if doi in verified:
            cache[doi] = {**verified[doi], 'checked_at': now.isoformat()}
            continue
        past = cache.get(doi, {})
        if not isinstance(past, dict):
            past = {}
        if scopus_cache_recent(past, now):
            continue
        checked = api.check(doi)
        if checked is not None:
            cache[doi] = {**checked, 'checked_at': now.isoformat()}
    all_years = defaultdict(Counter)
    persons = []
    verified_count = 0
    for person in data['dosen']:
        years = defaultdict(Counter)
        count = Counter()
        list_scopus = []
        for paper in person.get('publikasi_garuda', []):
            doi = scopus_doi_key(paper.get('doi'))
            record = cache.get(doi, {}) if doi else {}
            valid = isinstance(record, dict) and record.get('status') == 'verified' and bool(scopus_scopus_record(record.get('eid')))
            paper['status_indeks_scopus'] = 'terindeks' if valid else None
            paper['scopus_status_verifikasi'] = 'terindeks_terverifikasi' if valid else 'tidak_ada_doi' if not doi else 'belum_terverifikasi'
            paper['scopus_eid'] = record.get('eid') if valid else None
            paper['scopus_url'] = record.get('url') if valid else None
            paper['scopus_bukti_url'] = record.get('url') if valid else None
            yr = paper.get('tahun')
            yr = str(yr) if str(yr).isdigit() and 1900 <= int(yr) <= 2100 else None
            if valid:
                verified_count += 1
                count['terverifikasi'] += 1
                if yr:
                    years[yr]['terverifikasi'] += 1
                    all_years[yr]['terverifikasi'] += 1
                list_scopus.append({'judul': paper.get('judul'), 'penulis': paper.get('penulis'), 'jurnal': paper.get('jurnal'), 'tahun': paper.get('tahun'), 'doi': paper.get('doi'), 'url_doi': paper.get('url_doi'), 'url_artikel': paper.get('url_artikel'), 'url_scopus': record.get('url'), 'scopus_eid': record.get('eid'), 'sumber': 'GARUDA dicocokkan dengan Scopus'})
            else:
                count['belum_terverifikasi'] += 1
                if yr:
                    years[yr]['belum_terverifikasi'] += 1
                    all_years[yr]['belum_terverifikasi'] += 1
        person['publikasi_scopus'] = list_scopus
        person['rekap_scopus'] = {'terverifikasi': count['terverifikasi'], 'belum_terverifikasi': count['belum_terverifikasi']}
        persons.append({'slug': person.get('slug'), 'nama': person.get('nama'), 'rekap': person['rekap_scopus'], 'per_tahun': {yr: dict(v) for yr, v in sorted(years.items(), reverse=True)}})
    stamp = now.isoformat()
    data['scopus_pencocokan_utc'] = stamp
    data['scopus_metode'] = 'Verifikasi DOI melalui API resmi Elsevier atau bukti Scopus ber-EID yang disahkan'
    data['catatan_scopus'] = 'Tanpa akses API, belum terverifikasi bukan berarti tidak terindeks. Daftar dibatasi artikel yang ada di GARUDA.'
    recap = {'diperbarui_utc': stamp, 'total_rekaman': sum((len(p.get('publikasi_garuda', [])) for p in data['dosen'])), 'artikel_scopus_terverifikasi': verified_count, 'artikel_belum_terverifikasi': sum((p['rekap_scopus']['belum_terverifikasi'] for p in data['dosen'])), 'dosen': persons, 'rekap_tahunan': {y: dict(v) for y, v in sorted(all_years.items(), reverse=True)}, 'catatan': data['catatan_scopus']}
    diagnostics = {'diperbarui_utc': stamp, 'api_key_tersedia': bool(api.key), 'permintaan_api': api.request_count, 'api_diblokir': api.blocked, 'doi_unik': len(unique_doi), 'rekaman_terverifikasi': verified_count, 'peristiwa': api.events[:50], 'catatan': 'HTTP 403/429 dihentikan. Data yang belum diverifikasi tidak dihitung sebagai artikel Scopus.'}
    scopus_write_json(scopus_SOURCE, data)
    scopus_write_json(scopus_RECAP_FILE, recap)
    scopus_write_json(scopus_CACHE_FILE, {'versi': 1, 'artikel': cache})
    scopus_write_json(scopus_DIAG_FILE, diagnostics)
    with scopus_RECAP_CSV.open('w', encoding='utf-8-sig', newline='') as f:
        fields = ['dosen', 'slug', 'tahun', 'scopus_terverifikasi', 'belum_terverifikasi']
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for p in persons:
            for yr, c in p['per_tahun'].items():
                writer.writerow({'dosen': p['nama'], 'slug': p['slug'], 'tahun': yr, 'scopus_terverifikasi': c.get('terverifikasi', 0), 'belum_terverifikasi': c.get('belum_terverifikasi', 0)})
    scopus_save_article_csv(data)
    print(f'Scopus: {verified_count} rekaman terverifikasi dari {len(unique_doi)} DOI unik; {api.request_count} permintaan API; API key tersedia={bool(api.key)}; terblokir={api.blocked}')
    return 0


# ──────────────────────────────────────────────────────────────────────────
# Alur tunggal, dipanggil GitHub Actions melalui: python cek_sinta.py
# ──────────────────────────────────────────────────────────────────────────
def main():
    print('=== Tahap 1/3: GARUDA ===', flush=True)
    garuda_main()
    print('=== Tahap 2/3: Pencocokan jurnal SINTA ===', flush=True)
    code = sinta_main()
    if code not in (0, None):
        raise RuntimeError(f'Pencocokan SINTA gagal dengan kode: {code}')
    print('=== Tahap 3/3: Verifikasi Scopus ===', flush=True)
    code = scopus_main()
    if code not in (0, None):
        raise RuntimeError(f'Pencocokan Scopus gagal dengan kode: {code}')
    print('=== Selesai. Baca keluaran di folder hasil/ ===', flush=True)

if __name__ == '__main__':
    main()