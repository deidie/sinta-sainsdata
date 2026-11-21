        if not expires:
            from_cache += 1
            continue
        if fetcher.block_sinta or fetcher.requests_used >= MAX_REQUESTS:
            # Cache lama tetap dipertahankan untuk siklus berikutnya.
            continue
        name = items[0][2]
        if not name or re.search(r'\b(?:conference|seminar|proceedings)\b', name, re.I):
            continue
        # Pencarian direktori menggunakan nama; ISSN cocok bila tersedia.
        query = urlencode({'q': name})
        html = fetcher.get(f'{SINTA_BASE}/journals?{query}')
        if not html:
            continue
        candidates = parse_listing(html)
        candidate = pick_candidate(name, candidates)
        fresh += 1
        if candidate is None:
            if entry.get('status') == 'tercocokkan':
                # Jangan menghapus pemetaan resmi lama jika situs berubah/tidak lengkap.
                cache[key] = entry
            else:
                cache[key] = {'nama_garuda':name, 'checked_at':now_iso, 'status':'belum_cocok', 'sinta_url':None,
                              'peringkat_terkini':None, 'doi_artikel':{}, 'issn':[]}
            continue
        profile_html = fetcher.get(candidate['sinta_url'])
        doi_article = parse_profile_article_ranks(profile_html) if profile_html else {}
        previous_verified = entry.get('doi_artikel', {}) if isinstance(entry.get('doi_artikel'), dict) else {}
        # Jika profil sedang tidak dapat diakses, simpan rekaman DOI terverifikasi lama.
        previous_verified.update(doi_article)
        cache[key] = {'nama_garuda':name, 'nama_sinta':candidate['judul'],
                      'checked_at':now_iso, 'status':'tercocokkan',
                      'sinta_url':candidate['sinta_url'], 'peringkat_terkini':candidate['peringkat_terkini'],
                      'issn':candidate['issn'], 'doi_artikel':previous_verified}
        print(f'[SINTA] {name[:48]} => S{candidate["peringkat_terkini"]}; DOI spesifik={len(previous_verified)}')

    verified_count = 0
    rank_current_count = 0
    per_dosen = []
    by_year_all = defaultdict(Counter)
    for d in data['dosen']:
        count = Counter()
        year_count = defaultdict(Counter)
        for a in d.get('publikasi_garuda', []):
            title = title_from_garuda(a.get('jurnal'))
            record = cache.get(key_name(title), {})
            year = a.get('tahun')
            year = int(year) if str(year).isdigit() and 1900 <= int(year) <= 2100 else None
            doi = key_doi(a.get('doi'))
            rank = None
            source = None
            evidence = None
            # Jangan menafsirkan akreditasi jurnal TERKINI sebagai status di tahun terbit.
            if doi in manual_articles:
                rank = manual_articles[doi]['rank']
                evidence = manual_articles[doi]['bukti']
                source = 'bukti_artikel_terverifikasi'
            elif doi and doi in record.get('doi_artikel', {}):
                rank = int(record['doi_artikel'][doi])
                evidence = record.get('sinta_url')
                source = 'doi_pada_profil_jurnal_sinta'
            else:
                period = manual_period_rule(title, year, record.get('issn', []), manual_journals)
                if period:
                    rank = period['rank']
                    evidence = period['bukti']
                    source = 'periode_sk_terverifikasi'
            a['peringkat_sinta'] = rank
            a['sinta_status_verifikasi'] = source or 'belum_terverifikasi'
            a['sinta_bukti_url'] = evidence
            a['jurnal_sinta_url'] = record.get('sinta_url') or None
            a['jurnal_sinta_peringkat_terkini'] = record.get('peringkat_terkini')
            if record.get('peringkat_terkini') in range(1,7):
                rank_current_count += 1
            if rank in range(1,7):
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
        d['rekap_sinta'] = {**{f'S{i}':count[f'S{i}'] for i in range(1,7)},
                            'belum_terverifikasi':count['belum_terverifikasi']}
        per_dosen.append({'slug':d['slug'], 'nama':d['nama'], 'total':len(d.get('publikasi_garuda', [])),
                          'peringkat':d['rekap_sinta'],
                          'per_tahun':{y:dict(x) for y,x in sorted(year_count.items(), reverse=True)}})

    data['sinta_pencocokan_utc'] = now_iso
    data['sinta_metode'] = 'Pencocokan jurnal berdasarkan nama/ISSN; peringkat artikel hanya dari bukti DOI atau periode SK yang diverifikasi'
    data['catatan_sinta'] = 'Peringkat SINTA terkini jurnal tidak otomatis berlaku untuk seluruh tahun artikel. Belum terverifikasi bukan berarti SINTA 0.'
    recap = {'diperbarui_utc':now_iso,
             'total_rekaman':sum(len(d.get('publikasi_garuda', [])) for d in data['dosen']),
             'artikel_sinta_terverifikasi':verified_count,
             'artikel_belum_terverifikasi':sum(d['rekap_sinta']['belum_terverifikasi'] for d in data['dosen']),
             'dosen':per_dosen,
             'rekap_tahunan':{y:dict(v) for y,v in sorted(by_year_all.items(),reverse=True)},
             'catatan':'Jumlah merupakan rekaman per dosen; kolaborasi bisa terhitung lebih dari sekali.'}
    diagnostics = {'waktu':now_iso, 'jurnal_unik':len(groups), 'lookup_baru':fresh,
                   'lookup_dari_cache':from_cache, 'request_sinta':fetcher.requests_used,
                   'sinta_diblokir':fetcher.block_sinta, 'peristiwa':fetcher.events[:50],
                   'artikel_peringkat_terverifikasi':verified_count,
                   'artikel_jurnal_terkini_diketahui':rank_current_count,
                   'catatan':'Saat server memblokir akses, skrip tidak menghindari pembatasan dan mempertahankan cache.'}
    save_json(SOURCE, data)
    save_json(RECAP_PATH, recap)
    save_csv_exports(data, recap)
    save_json(CACHE_PATH, {'versi':1,'jurnal':cache})
    save_json(DIAG_PATH, diagnostics)
    print(f'Selesai: {len(groups)} jurnal; {verified_count} artikel status SINTA terverifikasi; '
          f'{diagnostics["artikel_jurnal_terkini_diketahui"]} artikel memiliki info peringkat jurnal terkini; '
          f'{fetcher.requests_used} permintaan; blokir={fetcher.block_sinta}.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
