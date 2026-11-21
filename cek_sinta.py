#!/usr/bin/env python3
"""Diagnostik gratis publikasi publik SINTA, satu dosen.

Tidak memerlukan login/proxy/token, tidak memanggil endpoint privat, dan tidak
mengubah Google Apps Script. Hasil berikut merupakan *kandidat* artikel
untuk validasi; rank SINTA hanya dibaca jika tertulis pada halaman.

Dapat digunakan menggantikan cek_sinta.py agar workflow uji-sinta.yml lama
mengunggah hasil/diagnostik_sinta.json sebagaimana sebelumnya.
"""
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from collections import Counter
import json
import re
import time

SINTA_ID = '6054939'  # Muhammad Dedi Irawan, diverifikasi dengan profil resmi.
BASE = 'https://sinta.kemdiktisaintek.go.id/authors/profile/' + SINTA_ID
OUT = Path('hasil/diagnostik_sinta.json')
VIEWS = ('garuda', 'scopus')

class Node:
    def __init__(self, tag='', attrs=None, parent=None):
        self.tag = tag
        self.attrs = dict(attrs or [])
        self.parent = parent
        self.children = []
        self.text_chunks = []
    def text(self):
        bits = self.text_chunks[:]
        for child in self.children:
            bits.append(child.text())
        return re.sub(r'\s+', ' ', ' '.join(bits)).strip()

class Reader(HTMLParser):
    VOID = {'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}
    SKIP = {'script','style','noscript','svg'}
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node('document')
        self.stack = [self.root]
        self.anchors = []
        self.tags = Counter()
    def handle_starttag(self, tag, attrs):
        self.tags[tag] += 1
        par = self.stack[-1]
        node = Node(tag, attrs, par)
        par.children.append(node)
        if tag == 'a': self.anchors.append(node)
        if tag not in self.VOID: self.stack.append(node)
    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in self.VOID: self.handle_endtag(tag)
    def handle_endtag(self, tag):
        for i in range(len(self.stack)-1,0,-1):
            if self.stack[i].tag == tag:
                del self.stack[i:]
                return
    def handle_data(self, data):
        if not any(n.tag in self.SKIP for n in self.stack):
            if data.strip(): self.stack[-1].text_chunks.append(data)

def get(url):
    req = Request(url, headers={
        'User-Agent':'Mozilla/5.0 (compatible; SainsData-Research-Metadata-Check/1.0)',
        'Accept':'text/html,application/xhtml+xml',
        'Accept-Language':'id-ID,id;q=0.9,en;q=0.7',
    })
    with urlopen(req, timeout=25) as res:
        return res.status, res.read(2_000_000).decode('utf-8','replace')

def tidy(t, maxlen=420):
    return re.sub(r'\s+',' ',t).strip()[:maxlen]

def context_for(a):
    # Cari pembungkus kartu artikel tanpa mengambil seluruh laman.
    node = a
    for _ in range(6):
        if node.parent is None: break
        node = node.parent
        cl = str(node.attrs.get('class','')).lower()
        text = node.text()
        if any(k in cl for k in ('ar-list','article','publication','paper','pub-list', 'list-group-item')):
            if 15 <= len(text) <= 1800: return text,cl
        if len(text) > 2500: break
    parent = a.parent
    return (parent.text() if parent else a.text()), ''

def candidate_links(p, pageurl):
    rows = []
    seen = set()
    for a in p.anchors:
        label = tidy(a.text(), 300)
        href = urljoin(pageurl, str(a.attrs.get('href','')))
        if not href.startswith('https://') or len(label)<14 or len(label)>290:
            continue
        if 'sinta.kemdiktisaintek.go.id/authors/profile/' in href:
            continue
        low = label.lower()
        if any(t in low for t in ('login','researches','community services','ipr','books','metrics','google scholar','garuda','scopus','sinta score','get more with','pagination','profile')):
            continue
        if (href,label) in seen: continue
        seen.add((href,label))
        context,cl = context_for(a)
        body = tidy(context, 850)
        doi = re.search(r'\b10\.\d{4,9}/[^\s;,<>\"]+', body, re.I)
        rank = re.search(r'\bAccred\s*:\s*Sinta\s*([1-6])\b',body,re.I)
        year = re.search(r'\b(?:19|20)\d{2}\b',body)
        rows.append({
            'judul_kandidat':label,
            'url':href,
            'tahun_kandidat':int(year.group()) if year else None,
            'doi_kandidat':doi.group().rstrip('.,)') if doi else None,
            'peringkat_sinta_tercantum': ('S'+rank.group(1)) if rank else None,
            'konteks_html':body,
            'class_pembungkus':cl,
        })
    return rows[:45]

def probe(view):
    url = BASE+'/?view='+view
    result = {'url':url,'http_status':None,'access_ok':False,
              'jumlah_kandidat_tautan':0,'artikel_kandidat':[],
              'contoh_teks_akreditasi':[],'jumlah_elemen':{},'pesan':''}
    try:
        status,html = get(url)
        result['http_status'] = status
        parser=Reader(); parser.feed(html)
        visible=parser.root.text()
        result['access_ok'] = (status==200 and 'MUHAMMAD DEDI IRAWAN' in visible.upper())
        result['jumlah_elemen'] = {k:parser.tags[k] for k in ('a','div','article','li','h3','h4','h5')}
        matches=re.findall(r'.{0,90}Accred\s*:\s*Sinta\s*[1-6].{0,90}',visible,re.I)
        result['contoh_teks_akreditasi'] = [tidy(s,190) for s in matches[:6]]
        if result['access_ok']:
            result['artikel_kandidat'] = candidate_links(parser,url)
            result['jumlah_kandidat_tautan'] = len(result['artikel_kandidat'])
            result['pesan'] = 'Kandidat artikel; belum diverifikasi. Periksa judul, link, dan peringkat.'
        else:
            result['pesan']='Tidak cocok dengan profil target; lewati data.'
    except HTTPError as ex: result['http_status']=ex.code; result['pesan']='HTTP '+str(ex.code)
    except (URLError,TimeoutError,OSError) as ex: result['pesan']='Kesalahan akses: '+str(ex)[:120]
    except Exception as ex: result['pesan']='Kesalahan parser: '+str(ex)[:160]
    return result

if __name__=='__main__':
    report = {'sinta_id':SINTA_ID,
              'nama_diharapkan':'Muhammad Dedi Irawan',
              'waktu_cek_utc':datetime.now(timezone.utc).isoformat(),
              'pemeriksaan':'uji kandidat artikel / Scopus / peringkat SINTA',
              'hasil':{}}
    for i,view in enumerate(VIEWS):
        if i: time.sleep(2)  # Permintaan ringan, tanpa paralelisme.
        report['hasil'][view]=probe(view)
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Uji selesai. HTTP:',{k:v['http_status'] for k,v in report['hasil'].items()})
    print('Jumlah tautan kandidat:',{k:v['jumlah_kandidat_tautan'] for k,v in report['hasil'].items()})
    print('Hasil tersimpan:',OUT)
