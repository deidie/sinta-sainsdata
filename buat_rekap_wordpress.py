#!/usr/bin/env python3
"""Buat JSON ringkas untuk dua tabel rekap WordPress dari hasil GitHub.

Tabel 1 = rekap publikasi GARUDA dan peringkat jurnal teramati per dosen.
Tabel 2 = rekap tahunan artikel unik prodi.
Jangan samakan peringkat jurnal kini dengan akreditasi artikel historis.
"""
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RESULT = ROOT / "hasil"
RECAP = RESULT / "rekap_jurnal_sinta_terkini.json"
ARTICLES = RESULT / "rekap_sinta.json"
MONTHLY = RESULT / "status_pemeriksaan_sinta.json"
GARUDA = RESULT / "publikasi_dosen.json"
DEST = RESULT / "rekap_publikasi_wordpress.json"

RANKS = ["S" + str(n) for n in range(1, 7)] + ["belum_tercocokkan"]


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def counts(m):
    return {name: int(m.get(name) or 0) for name in RANKS}


def main():
    recap, verified, garuda = read(RECAP), read(ARTICLES), read(GARUDA)
    audit = read(MONTHLY) if MONTHLY.is_file() else None
    if (recap.get("artikel_unik_prodi") is None or
        recap.get("rekaman_per_dosen_dengan_duplikasi_kolaborasi") != verified.get("total_rekaman")):
        raise ValueError("Rekap sumber tidak konsisten; tidak memperbarui data WordPress")
    teachers = [
        {"slug": p["slug"], "nama": p["nama"], "garuda": int(p["rekaman"]),
         **counts(p["peringkat_jurnal"])}
        for p in recap.get("rekap_per_dosen") or []
    ]
    if len(teachers) != 6 or sum(p["garuda"] for p in teachers) != verified["total_rekaman"]:
        raise ValueError("Profil dosen tidak sesuai jumlah GARUDA")
    years = [
        {"tahun": int(year), "publikasi": sum(int(n or 0) for n in c.values()), **counts(c)}
        for year, c in recap.get("rekap_tahunan_unik_prodi",{}).items()
    ]
    years.sort(key=lambda x:x["tahun"], reverse=True)
    result = {
        "versi": 1,
        "dibuat_utc": datetime.now(timezone.utc).isoformat(),
        "sumber": "GARUDA + katalog profil jurnal SINTA",
        "garuda_diperbarui_utc": garuda.get("diperbarui_utc"),
        "peringkat_jurnal_diperbarui_utc": recap.get("diperbarui_utc"),
        "pemeriksaan_sinta_utc": audit.get("diperiksa_utc") if audit else None,
        "pemeriksaan_sinta_terbatas": bool(audit.get("akses_dibatasi")) if audit else None,
        "tabel_per_dosen": teachers,
        "tabel_per_tahun": years,
        "rekap_prodi": {
            "garuda_unik": int(recap["artikel_unik_prodi"]),
            "garuda_rekaman_per_dosen": int(recap["rekaman_per_dosen_dengan_duplikasi_kolaborasi"]),
            "peringkat_jurnal": counts(recap["rekap_unik_prodi"]),
            "peringkat_artikel_doi_terverifikasi": int(verified["artikel_sinta_terverifikasi"]),
        },
        "keterangan": "S1-S6 dalam tabel berarti peringkat jurnal yang teramati. Ini bukan bukti peringkat akreditasi tiap artikel pada tahun terbit. Jumlah tahunan unik menghapus karya bersama. Belum cocok bukan berarti tidak terindeks SINTA.",
    }
    DEST.parent.mkdir(exist_ok=True)
    DEST.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("JSON WordPress dibuat: ",len(teachers),"dosen,",len(years),
          "tahun,",result["rekap_prodi"]["garuda_unik"],"artikel unik")


if __name__=="__main__":
    main()
