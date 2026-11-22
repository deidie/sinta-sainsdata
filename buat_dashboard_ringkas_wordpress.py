#!/usr/bin/env python3
"""Buat dashboard ringkas; data lengkap tetap tersimpan terpisah di hasil/."""
import json
from datetime import datetime, timezone
from pathlib import Path

BASE=Path(__file__).resolve().parent/'hasil'
def read(name):
    return json.loads((BASE/name).read_text(encoding='utf-8'))

def main():
    garuda=read('rekap_publikasi_wordpress.json')
    sinta=read('sinta_laman_wordpress.json')
    scholar=read('publikasi_scholar.json')
    scopus=read('scopus_sinta_wordpress.json')
    extra=read('publikasi_tambahan_dosen.json')
    slugs=('siddik','dedi','rakhmat','aidil','ika','puji')
    assert {p['slug'] for p in scholar['dosen']}==set(slugs)
    assert len(scopus['publikasi'])>0
    assert isinstance(extra.get('buku'),list) and isinstance(extra.get('ipr'),list)
    output={
       'version':1,'updated':datetime.now(timezone.utc).date().isoformat(),
       'garuda_unique':garuda['rekap_prodi']['garuda_unik'],
       'garuda_years':[{'tahun':p['tahun'],'publikasi':p['publikasi']} for p in garuda['tabel_per_tahun']],
       'garuda_persons':[{'slug':p['slug'],'garuda':p['garuda']} for p in garuda['tabel_per_dosen']],
       'sinta_total':sinta['total_sinta'],'sinta_ranks':sinta['peringkat'],
       'sinta_years':[{'tahun':p['tahun'],'sinta':p['sinta'],'peringkat':p['peringkat']} for p in sinta['per_tahun']],
       'sinta_persons':[{'slug':p['slug'],'total':p['total'],'peringkat':p['peringkat']} for p in sinta['per_dosen']],
       'scholars':[{'slug':p['slug'],'metrik_scholar':p.get('metrik_scholar',{}),'sitasi_tahunan':p.get('sitasi_tahunan',{})} for p in scholar['dosen']],
       'scopus':scopus['publikasi'],
       'extra_totals':{'buku':len(extra['buku']),'ipr':len(extra['ipr'])},
       'extra_persons':[{'slug':slug,
         'buku':sum(slug in (p.get('dosen') or []) for p in extra['buku']),
         'ipr':sum(slug in (p.get('dosen') or []) for p in extra['ipr'])} for slug in slugs]
    }
    assert len(output['sinta_persons'])==6 and len(output['garuda_persons'])==6
    (BASE/'dashboard_ringkas_wordpress.json').write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Ringkasan tersedia:',output['garuda_unique'],'GARUDA,',output['sinta_total'],'SINTA,',len(output['scopus']),'Scopus')

if __name__=='__main__':
    main()
