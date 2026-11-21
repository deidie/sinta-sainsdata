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
