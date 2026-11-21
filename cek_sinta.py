#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Indeks publikasi GARUDA enam dosen Sains Data UINSU.

Sumber: halaman penulis GARUDA yang dapat diakses publik, ditambah ringkasan
metrik pada halaman profil SINTA publik. Tidak memerlukan API key.

Berhenti ketika situs membatasi permintaan (403/429); tidak mengakses konten
khusus login, tidak memakai proxy, CAPTCHA bypass atau sesi pribadi.

Simpan sebagai cek_sinta.py di repository GitHub yang sudah digunakan.
"""

from __future__ import annotations

import csv
import json
import re
import sys
import time
import unicodedata
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse, parse_qs
from urllib.request import Request, urlopen

OUTPUT_DIR = Path('hasil')
# Ambang keselamatan untuk mencegah loop tanpa akhir, BUKAN target jumlah artikel.
MAX_PAGES_PER_PROFILE = 120
DELAY_SECONDS = 1.6
TIMEOUT_SECONDS = 22
USER_AGENT = 'SainsData-UINSU-Publication-Catalog/1.0 (public-academic-metadata)'

# ID SINTA dikonfirmasi pengguna. ID GARUDA berasal dari profil penulis publik,
# tetapi GARUDA dapat memiliki profil ganda untuk penulis yang sama.
# Profil alternatif belum digabungkan otomatis karena perlu verifikasi identitas.
DOSEN = [
    {'slug':'siddik', 'nama':'Muhammad Siddik Hasibuan', 'sinta_id':'5983919',
     'garuda_ids':['2406700'], 'perlu_verifikasi_garuda':False},
    {'slug':'dedi', 'nama':'Muhammad Dedi Irawan', 'sinta_id':'6054939',
     'garuda_ids':['1197451'], 'perlu_verifikasi_garuda':False},
    {'slug':'rakhmat', 'nama':'Rakhmat Kurniawan R', 'sinta_id':'6160028',
     'garuda_ids':['1733344'], 'perlu_verifikasi_garuda':False},
    {'slug':'aidil', 'nama':'Aidil Halim Lubis', 'sinta_id':'6795618',
     'garuda_ids':['621444'], 'perlu_verifikasi_garuda':False},
    {'slug':'ika', 'nama':'Ika Yusnita Sari', 'sinta_id':'6745259',
     'garuda_ids':['7443043'], 'perlu_verifikasi_garuda':True},
    {'slug':'puji', 'nama':'Puji Sari Ramadhan', 'sinta_id':'6089755',
     'garuda_ids':['10712505'], 'perlu_verifikasi_garuda':False},
]

DOCUMENT_RE = re.compile(r'/documents/detail/(\d+)(?:[/?#]|$)')
DOI_RE = re.compile(r'\b10\.\d{4,9}/[^\s<>"|]+', re.I)
YEAR_RE = re.compile(r'\b(?:19|20)\d{2}\b')


def normalize(text):
    text = unicodedata.normalize('NFKC', str(text or ''))
    return ' '.join(text.split()).strip()


def normalized_name(name):
    value = unicodedata.normalize('NFKD', normalize(name).lower())
    return re.sub(r'[^a-z0-9]+', ' ', value).strip()


class Node:
    def __init__(self, tag='root', attrs=(), parent=None):
        self.tag = tag
        self.attrs = dict(attrs or [])
        self.parent = parent
        self.items = []

    def text(self):
        return normalize(' '.join(x.text() if isinstance(x, Node) else x for x in self.items))

    def walk(self):
        yield self
        for item in self.items:
            if isinstance(item, Node):
                yield from item.walk()

    def links(self):
        return [(n.text(), n.attrs.get('href',''), n) for n in self.walk() if n.tag == 'a']

    def classes(self):
        return str(self.attrs.get('class','')).split()


class HTMLTree(HTMLParser):
    VOID = {'area','base','br','col','embed','hr','img','input','link','meta',
            'param','source','track','wbr'}

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
        for idx in range(len(self.stack)-1, 0, -1):
            if self.stack[idx].tag == tag:
                del self.stack[idx:]
                return

    def handle_data(self, data):
        if not any(n.tag in ('script','style','noscript') for n in self.stack):
            self.stack[-1].items.append(data)


def parse_html(html):
    doc = HTMLTree()
    doc.feed(html)
    return doc.root


def fetch_public(url):
    """One public GET, never repeats a forbidden/rate-limited response."""
    req = Request(url, headers={
        'User-Agent':USER_AGENT,
        'Accept':'text/html,application/xhtml+xml',
        'Accept-Language':'id-ID,id;q=0.9,en;q=0.8',
    })
    try:
        with urlopen(req, timeout=TIMEOUT_SECONDS) as response:
            status = response.getcode()
            final = response.geturl()
            content_type = response.headers.get('Content-Type','')
            if status != 200:
                return {'status':status, 'html':'', 'url':final, 'error':f'HTTP {status}'}
            if 'html' not in content_type.lower():
                return {'status':status, 'html':'', 'url':final, 'error':'Respons bukan HTML'}
            raw = response.read(4_000_001)
            if len(raw) > 4_000_000:
                return {'status':status, 'html':'', 'url':final, 'error':'HTML terlalu besar'}
            return {'status':status, 'html':raw.decode('utf-8','replace'), 'url':final, 'error':''}
    except HTTPError as error:
        return {'status':error.code, 'html':'', 'url':url,
                'error':f'HTTP {error.code}, dihentikan tanpa mencoba menghindari pembatasan'}
    except (URLError, TimeoutError, OSError) as error:
        return {'status':None, 'html':'', 'url':url, 'error':str(error)[:180]}


def bounded_article_container(anchor):
    current = anchor
    best = None
    for _ in range(11):
        current = current.parent
        if current is None:
            break
        count = sum(bool(DOCUMENT_RE.search(str(href))) for _, href, _ in current.links())
        text = current.text()
        if count > 1 or len(text) > 15000:
            break
        if count == 1:
            best = current
            if ('Publisher' in text or 'Original Source' in text or
                'Show Abstract' in text or 'DOI:' in text):
                return current
    return best or anchor


def extract_doi(container):
    for label, href, _ in container.links():
        url = urljoin('https://garuda.kemdiktisaintek.go.id', str(href))
        if urlparse(url).netloc.lower() in ('doi.org','dx.doi.org'):
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
        link = urljoin(base_url, str(anchor.attrs.get('href','')))
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
        links = [(normalize(label), urljoin(base_url,str(href)))
                 for label,href,_ in container.links()]
        source_url = next((href for label,href in links if 'original source' in label.lower()), None)
        authors = []
        
        for label, href in links:
            if re.search(r'/author/view/\d+', urlparse(href).path):
                cleaned = re.split(
                    r'\b(?:Show Abstract|Download Original|Original Source)\b',
                    label,
                    maxsplit=1,
                    flags=re.I
                )[0]
                cleaned = normalize(cleaned).strip(' ;|')

                if cleaned and cleaned not in authors:
                    authors.append(cleaned)

        doi = extract_doi(container)

        # Metadata tidak ditemukan tidak boleh direka.
        year = None
        year_match = YEAR_RE.search(text)
        if year_match:
            year = int(year_match.group(0))
        jurnal = None
        if 'Publisher' in text:
            before = text.split('Publisher',1)[0]
            if title in before:
                guess = normalize(before.split(title,1)[-1]).strip(' -:|')
                if 5 <= len(guess) <= 250:
                    jurnal = guess
        results.append({
            'judul':title,
            'penulis':'; '.join(authors) if authors else None,
            'jurnal':jurnal,
            'tahun':year,
            'doi':doi,
            'url_doi':'https://doi.org/'+doi if doi else None,
            'url_garuda':link,
            'url_artikel':source_url,
            'peringkat_sinta':None,  # Belum ada verifikasi peringkat dari GARUDA.
            'status_indeks_scopus':None,  # GARUDA tidak membuktikan indeks Scopus.
            'garuda_document_id':document_id,
            'garuda_author_id':source_id,
            'halaman_sumber':source_page,
        })
    return results


def page_numbers(html, author_id):
    """Hanya referensi paginasi pada profil penulis yang sama."""
    doc = parse_html(html)
    nums = set()
    for node in doc.walk():
        if node.tag != 'a':
            continue
        target = urljoin('https://garuda.kemdiktisaintek.go.id', str(node.attrs.get('href','')))
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
            failure = f'Halaman {page}: {fetched["error"]}'
            pages.append({'page':page,'http_status':status,'count':0, 'error':failure})
            break
        html = fetched['html']
        items = parse_publications(html, url, author_id, page)
        fresh = [a for a in items if a['garuda_document_id'] not in seen]
        for article in fresh:
            seen.add(article['garuda_document_id'])
            all_items.append(article)
        pages.append({'page':page,'http_status':status,'count':len(items), 'new':len(fresh)})
        max_known = max([max_known]+list(page_numbers(html, author_id)))
        print(f'  {slug} GARUDA {author_id}: halaman {page}, {len(items)} entri, {len(fresh)} baru', flush=True)
        if not items:
            break
        if not fresh:
            consecutive_repeats += 1
            if consecutive_repeats >= 2:
                break
        else:
            consecutive_repeats = 0
        # Beberapa navigasi menunjukkan nomor halaman terakhir, beberapa hanya
        # halaman selanjutnya. Teruskan sampai halaman kosong/duplikat.
        page += 1
    if page > MAX_PAGES_PER_PROFILE:
        failure = f'Melebihi batas pengaman {MAX_PAGES_PER_PROFILE} halaman; periksa paginasi.'
    return {'garuda_author_id':author_id, 'url':base, 'pages':pages,
            'articles':all_items,'error':failure, 'completed':not bool(failure)}


def sinta_summary(html, expected_name):
    doc = parse_html(html)
    summary = {'sinta_score_overall':None, 'sinta_score_3yr':None,
               'scopus':{'artikel':None,'sitasi':None,'dokumen_tersitasi':None,'h_index':None,'i10_index':None},
               'peringkat_jurnal':None}
    numbers = [node.text() for node in doc.walk() if 'pr-num' in node.classes()]
    def to_num(value):
        cleaned = str(value).strip().replace('.','').replace(',','')
        return int(cleaned) if cleaned.isdigit() else None
    if len(numbers) >= 2:
        summary['sinta_score_overall'] = to_num(numbers[0])
        summary['sinta_score_3yr'] = to_num(numbers[1])
    keys = {'article':'artikel', 'citation':'sitasi', 'cited document':'dokumen_tersitasi',
            'h-index':'h_index', 'i10-index':'i10_index'}
    for node in doc.walk():
        if node.tag != 'table' or 'stat-table' not in node.classes():
            continue
        for tr in node.walk():
            if tr.tag != 'tr':
                continue
            cells = [n.text() for n in tr.items if isinstance(n,Node) and n.tag in ('td','th')]
            if len(cells) < 2:
                continue
            key = normalize(cells[0]).lower()
            if key in keys:
                summary['scopus'][keys[key]] = to_num(cells[1])
        break
    plain = normalized_name(doc.text())
    match_name = normalized_name(expected_name) in plain
    return summary, match_name


def harvest_sinta(sinta_id, name):
    url = f'https://sinta.kemdiktisaintek.go.id/authors/profile/{sinta_id}'
    time.sleep(DELAY_SECONDS)
    fetched = fetch_public(url)
    if fetched['error']:
        return {'url':url, 'http_status':fetched['status'], 'error':fetched['error'],
                'metrics':None,'nama_tercocokkan':False}
    metrics, valid_name = sinta_summary(fetched['html'], name)
    return {'url':url,'http_status':fetched['status'], 'error':None if valid_name else 'Nama penulis tidak cocok',
            'metrics':metrics if valid_name else None,'nama_tercocokkan':valid_name}


def deduplicate(articles):
    out = []
    seen = set()
    for a in articles:
        key = ('doi',a['doi'].lower()) if a['doi'] else ('garuda',a['garuda_document_id'])
        if key in seen:
            continue
        seen.add(key)
        out.append(a)
    return out


def save_json(path, value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')


def main():
    started = datetime.now(timezone.utc).isoformat()
    output = {'versi':'1.0', 'diperbarui_utc':started,
              'sumber':'GARUDA dan halaman profil publik SINTA',
              'catatan':'Peringkat jurnal dan indeks Scopus setiap artikel belum diverifikasi otomatis.',
              'dosen':[]}
    diagnostics = {'diperbarui_utc':started, 'dosen':[]}
    for author in DOSEN:
        slug = author['slug']
        print(f'\nMemproses {author["nama"]} (SINTA {author["sinta_id"]})',flush=True)
        author_reports = []
        articles = []
        for garuda_id in author['garuda_ids']:
            report = harvest_author(garuda_id, slug)
            articles.extend(report['articles'])
            author_reports.append({k:v for k,v in report.items() if k!='articles'})
        articles = deduplicate(articles)
        sinta = harvest_sinta(author['sinta_id'],author['nama'])
        status = 'lengkap' if all(r['completed'] for r in author_reports) else 'sebagian'
        if not articles:
            status = 'belum_tersedia'
        if author['perlu_verifikasi_garuda'] and status=='lengkap':
            status = 'perlu_verifikasi_identitas_garuda'
        entry = {
            'slug':slug,'nama':author['nama'],'sinta_id':author['sinta_id'],
            'sinta_url':sinta['url'], 'garuda_author_ids':author['garuda_ids'],
            'perlu_verifikasi_identitas_garuda':author['perlu_verifikasi_garuda'],
            'status':status,'jumlah_artikel_terambil':len(articles),
            'metrik_sinta':sinta['metrics'],
            'metrik_sinta_status':sinta['error'] or 'berhasil',
            'publikasi_garuda':articles,
        }
        output['dosen'].append(entry)
        diagnostics['dosen'].append({
            'slug':slug,'nama':author['nama'],'sinta_id':author['sinta_id'],
            'jumlah_artikel':len(articles),'status':status,
            'profil_garuda':author_reports,
            'sinta':{k:v for k,v in sinta.items() if k!='metrics'},
        })
        print(f'  {slug}: {len(articles)} artikel; status={status}; SINTA: {sinta["error"] or "berhasil"}',flush=True)
    save_json(OUTPUT_DIR/'publikasi_dosen.json',output)
    save_json(OUTPUT_DIR/'diagnostik_sinta.json',diagnostics)
    with (OUTPUT_DIR/'publikasi_dosen.csv').open('w',newline='',encoding='utf-8-sig') as handle:
        fields=['dosen','sinta_id','judul','penulis','jurnal','tahun','doi','url_doi',
                'url_garuda','url_artikel','garuda_author_id','peringkat_sinta','status_indeks_scopus']
        writer=csv.DictWriter(handle,fieldnames=fields)
        writer.writeheader()
        for entry in output['dosen']:
            for article in entry['publikasi_garuda']:
                writer.writerow({**{k:article.get(k) for k in fields},
                                 'dosen':entry['nama'],'sinta_id':entry['sinta_id']})
    print('\nHasil tersedia di folder hasil/:',flush=True)
    for file in sorted(OUTPUT_DIR.iterdir()):
        print(f'  {file} ({file.stat().st_size:,} byte)',flush=True)


if __name__=='__main__':
    try:
        main()
    except Exception as error:
        print(f'Kesalahan fatal: {error}',file=sys.stderr,flush=True)
        raise
