#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rekap SINTA yang benar-benar sesuai periode terbit. S1-S6 jurnal terkini tidak
dipaksakan menjadi peringkat artikel terdahulu. Dijalankan setelah pembaruan GARUDA.
"""
import json
import re
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parent
def read(p):
    return json.loads((ROOT/p).read_text(encoding="utf-8"))
def write(p,o):
    target=ROOT/p;target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(o,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
def doi_key(x):
    s=str(x or "").strip().lower()
    return re.sub(r"^https?://(?:dx\.)?doi\.org/","",s).rstrip(".,;")
def title_key(x):
    s=unicodedata.normalize("NFKD",str(x or "").casefold())
    return re.sub(r"[^a-z0-9]+"," ",s).strip()
def main():
    papers=read("hasil/publikasi_dosen.json")
    proof=read("data/bukti_artikel_sinta.json")
    period=read("data/peringkat_sinta_historis.json")
    proof_by={}
    for a in proof["artikel"]:
        assert a.get("bukti_url") and type(a.get("peringkat")) is int and 1 <= a["peringkat"] <= 6
        proof_by[doi_key(a["doi"])]=(a["peringkat"],a["bukti_url"],"doi_sinta")
    for a in period["artikel"]:
        assert a.get("bukti_url") and type(a.get("peringkat_saat_terbit")) is int and 1 <= a["peringkat_saat_terbit"] <= 6
        proof_by[doi_key(a["doi"])]=(a["peringkat_saat_terbit"],a["bukti_url"],"periode_akreditasi")
    unique={}
    people=[]
    for person in papers["dosen"]:
        counter=Counter()
        for a in person["publikasi_garuda"]:
            d=doi_key(a.get("doi"))
            proof_rec=proof_by.get(d)
            if not proof_rec and type(a.get("peringkat_sinta")) is int and a.get("sinta_bukti_url"):
                proof_rec=(a["peringkat_sinta"],a["sinta_bukti_url"],"doi_data")
            ident="doi:"+d if d else "title:"+title_key(a.get("judul"))+"|"+str(a.get("tahun") or "")
            if ident not in unique:
                unique[ident]={"judul":a.get("judul"),"tahun":a.get("tahun"),"doi":d or None,
                     "dosen":[],"peringkat_sinta_saat_terbit":None,"bukti_url":None,"sumber_peringkat":None,
                     "jurnal_sinta_peringkat_terkini":a.get("jurnal_sinta_peringkat_terkini")}
            u=unique[ident]
            if person["slug"] not in u["dosen"]:u["dosen"].append(person["slug"])
            if proof_rec:
                counter["S"+str(proof_rec[0])]+=1
                if u["peringkat_sinta_saat_terbit"] is None:
                    u["peringkat_sinta_saat_terbit"]=proof_rec[0]
                    u["bukti_url"]=proof_rec[1]
                    u["sumber_peringkat"]=proof_rec[2]
        rank_cols={f"S{k}":counter[f"S{k}"] for k in range(1,7)}
        people.append({"slug":person["slug"],"nama":person["nama"],
                       "total_publikasi_garuda":len(person["publikasi_garuda"]),
                       "terverifikasi_terbit":sum(rank_cols.values()),**rank_cols})
    docs=list(unique.values())
    ok=[x for x in docs if x["peringkat_sinta_saat_terbit"] is not None]
    byyear=[]
    for y in sorted({int(x["tahun"]) for x in docs if str(x.get("tahun") or "").isdigit()},reverse=True):
        rows=[x for x in docs if int(x.get("tahun") or 0)==y]
        cy=Counter("S"+str(x["peringkat_sinta_saat_terbit"]) for x in rows if x["peringkat_sinta_saat_terbit"])
        byyear.append({"tahun":y,"publikasi":len(rows),"terverifikasi_terbit":sum(cy.values()),
                      **{f"S{k}":cy[f"S{k}"] for k in range(1,7)}})
    # The number of journals matched to SINTA is separate from historical period verification.
    latest=read("hasil/rekap_publikasi_wordpress.json")
    journal_counts=latest.get("rekap_prodi",{}).get("peringkat_jurnal",{})
    journal_matches=sum(int(journal_counts.get(f"S{k}") or 0) for k in range(1,7))
    assert len(docs)>0 and len(papers["dosen"])==len(people)==6
    payload={"versi":1,"diperiksa_tanggal":datetime.now(timezone.utc).date().isoformat(),
      "metode":"Peringkat saat terbit berdasarkan DOI SINTA atau bukti periode jurnal; tidak mengasumsikan peringkat jurnal terkini berlaku historis.",
      "rekap_prodi":{"garuda_unik":len(docs),"jurnal_dipadan_peringkat_terkini":journal_matches,
       "publikasi_sinta_saat_terbit_terverifikasi":len(ok),"belum_divalidasi_periode":len(docs)-len(ok),
       "peringkat":{f"S{k}":sum(x["peringkat_sinta_saat_terbit"]==k for x in ok) for k in range(1,7)}},
       "tabel_per_tahun":byyear,"tabel_per_dosen":people,
       "artikel_peringkat_terverifikasi":ok,
       "catatan":"0 pada peringkat terverifikasi berarti belum ada bukti pada subset, bukan menyatakan tidak ada publikasi terindeks."}
    write("hasil/rekap_sinta_berdasar_terbit.json",payload)
    print("Total unik:",len(docs),"SINTA historis terverifikasi:",len(ok),"Jurnal cocok terkini:",journal_matches)
if __name__=="__main__": main()
