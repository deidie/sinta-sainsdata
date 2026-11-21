#!/usr/bin/env python3
"""Bentuk dataset WordPress SINTA dari GARUDA dan peringkat jurnal.
Peringkat periode terbit yang memiliki bukti DOI/SK diprioritaskan, tetapi
total SINTA tetap mencakup jurnal yang sudah cocok katalog dan ditandai
sebagai peringkat jurnal terkini apabila bukti historis belum tersedia.
"""
from collections import Counter
from pathlib import Path
from datetime import datetime, timezone
import json
import re
import unicodedata

HERE=Path(__file__).resolve().parent
SRC=HERE/"hasil/publikasi_dosen.json"
PROOF=HERE/"data/bukti_artikel_sinta.json"
PERIOD=HERE/"data/peringkat_sinta_historis.json"
DEST=HERE/"hasil/sinta_laman_wordpress.json"

def read(path):
    return json.loads(path.read_text(encoding="utf-8"))

def norm_doi(value):
    s=str(value or "").strip().casefold()
    return re.sub(r"^https?://(?:dx\.)?doi\.org/", "", s).rstrip(".,;")

def norm_title(value):
    s=unicodedata.normalize("NFKD",str(value or "").casefold())
    return re.sub(r"[^a-z0-9]+"," ",s).strip()

def main():
    source=read(SRC)
    evidence={}
    for a in read(PROOF).get("artikel", []):
        if a.get("doi") and a.get("bukti_url") and type(a.get("peringkat")) is int:
            evidence[norm_doi(a["doi"])]=(a["peringkat"],a["bukti_url"])
    for a in read(PERIOD).get("artikel", []):
        if a.get("doi") and a.get("bukti_url") and type(a.get("peringkat_saat_terbit")) is int:
            evidence[norm_doi(a["doi"])]=(a["peringkat_saat_terbit"],a["bukti_url"])
    merged={}
    authors=[]
    for profile in source.get("dosen", []):
        slug=profile.get("slug")
        papers=profile.get("publikasi_garuda") or []
        for a in papers:
            doi=norm_doi(a.get("doi"))
            ident="doi:"+doi if doi else "title:"+norm_title(a.get("judul"))+"|"+str(a.get("tahun") or "")
            proof=evidence.get(doi)
            verified=int(proof[0]) if proof else None
            if verified is None and type(a.get("peringkat_sinta")) is int and a.get("sinta_bukti_url"):
                verified=int(a["peringkat_sinta"])
                proof=(verified,a["sinta_bukti_url"])
            current=a.get("jurnal_sinta_peringkat_terkini")
            current=current if type(current) is int and current in range(1,7) else None
            if verified is not None and verified not in range(1,7):
                raise ValueError("Peringkat historis tidak valid "+str(doi))
            row=merged.get(ident)
            if row is None:
                row={"judul":a.get("judul"),"tahun":int(a.get("tahun") or 0) or None,
                     "doi":doi or None,"jurnal":a.get("jurnal") or None,
                     "dosen":[],"sinta_jurnal_kini":current,
                     "sinta_saat_terbit":verified,"sinta_bukti_url":proof[1] if proof else None,
                     "url":a.get("url_doi") or a.get("url_garuda") or a.get("url_artikel")}
                merged[ident]=row
            if slug not in row["dosen"]:
                row["dosen"].append(slug)
            if current and not row["sinta_jurnal_kini"]:
                row["sinta_jurnal_kini"]=current
            if verified and not row["sinta_saat_terbit"]:
                row["sinta_saat_terbit"]=verified
                row["sinta_bukti_url"]=proof[1]
    works=list(merged.values())
    selected=[]
    for item in works:
        rank=item.get("sinta_saat_terbit") or item.get("sinta_jurnal_kini")
        if rank is None:
            continue
        selected.append({**item,
            "peringkat_tampilan":rank,
            "jenis_label":"tahun_terbit" if item.get("sinta_saat_terbit") else "jurnal_saat_ini"})
    # One unique publication is counted once at program level.
    ranks=Counter("S"+str(a["peringkat_tampilan"]) for a in selected)
    per_person=[]
    for profile in source.get("dosen",[]):
        slug=profile["slug"]
        matching=[a for a in selected if slug in a["dosen"]]
        count=Counter("S"+str(a["peringkat_tampilan"]) for a in matching)
        per_person.append({"slug":slug,"nama":profile.get("nama"),
            "total":len(matching),"peringkat":{f"S{k}":count[f"S{k}"] for k in range(1,7)},
            "historis_terverifikasi":sum(a["jenis_label"]=="tahun_terbit" for a in matching)})
    per_year=[]
    for year in sorted({a["tahun"] for a in works if a.get("tahun")},reverse=True):
        items=[a for a in selected if a["tahun"]==year]
        count=Counter("S"+str(a["peringkat_tampilan"]) for a in items)
        per_year.append({"tahun":year,
            "publikasi":sum(a["tahun"]==year for a in works),
            "sinta":len(items),
            "peringkat":{f"S{k}":count[f"S{k}"] for k in range(1,7)},
            "historis_terverifikasi":sum(a["jenis_label"]=="tahun_terbit" for a in items)})
    assert len(per_person)==6
    assert sum(ranks.values())==len(selected)
    assert sum(y["sinta"] for y in per_year)==len(selected)
    result={"versi":2,"dibuat_tanggal":datetime.now(timezone.utc).date().isoformat(),
        "sumber":"GARUDA + katalog jurnal SINTA + bukti periode terbit",
        "metode":"Peringkat tahun terbit diutamakan jika memiliki bukti; sumber lain memakai peringkat jurnal saat ini.",
        "total_publikasi_unik":len(works),"total_sinta":len(selected),
        "peringkat":{f"S{k}":ranks[f"S{k}"] for k in range(1,7)},
        "per_tahun":per_year,"per_dosen":per_person,"artikel":selected}
    DEST.parent.mkdir(parents=True,exist_ok=True)
    DEST.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("SINTA karya cocok:",len(selected),"unik GARUDA:",len(works),"historis terverifikasi:",sum(x["jenis_label"]=="tahun_terbit" for x in selected))

if __name__=="__main__":
    main()
