#!/usr/bin/env python3
"""Build lightweight WordPress Scopus SOURCE checks, never convert source match into EID."""
import json
from datetime import datetime, timezone
from pathlib import Path

BASE=Path(__file__).resolve().parent
IN=BASE/"hasil/pemeriksaan_scopus_tanpa_api.json"
OUT=BASE/"hasil/scopus_ringkas_wordpress.json"
def main():
    d=json.loads(IN.read_text(encoding="utf-8"))
    results=[]
    for p in d.get("publikasi",[]):
        status=p.get("status_pemeriksaan_scopus","")
        if not (status.startswith("sumber_") or status=="dokumen_scopus_ber_eid"):
            continue
        src=(p.get("hasil_jurnal_seri") or {}).get("data_sumber") or {}
        bk=(p.get("hasil_buku") or {}).get("data_buku") or {}
        results.append({
            "judul":p.get("judul"),"tahun":p.get("tahun"),"doi":p.get("doi"),"isbn":p.get("isbn",[]),
            "dosen":p.get("dosen",[]),"status":status,"scopus_eid":p.get("scopus_eid"),
            "jenis":"buku_atau_bab" if bk else "jurnal",
            "sumber_scopus":src.get("nama_sumber") or bk.get("judul_buku"),
            "source_id":src.get("id_sumber_scopus") or bk.get("id_buku_scopus"),
            "bukti_url":src.get("sumber_bukti") or bk.get("sumber_bukti"),
            "cakupan_tahun":(p.get("hasil_jurnal_seri") or {}).get("cakupan_pada_tahun")
        })
    books=json.loads((BASE/"hasil/kandidat_buku_scopus_crossref.json").read_text(encoding="utf-8")) if (BASE/"hasil/kandidat_buku_scopus_crossref.json").exists() else {}
    book_candidates=[{
        "judul":p.get("judul"),"tahun":p.get("tahun"),"doi":p.get("doi"),"isbn":p.get("isbn",[]),
        "dosen":p.get("dosen",[]),"jenis":"bab_buku","bukti_crossref":p.get("bukti_crossref"),
        "status":"kandidat_crossref_belum_scopus" if not any(x.get("doi")==p.get("doi") for x in results) else "sumber_buku_scopus_cocok_belum_bukti_dokumen"
    } for p in books.get("publikasi",[])]
    payload={"versi":1,"diperbarui_utc":datetime.now(timezone.utc).isoformat(),
       "judul_data":"Kecocokan SUMBER Scopus (bukan bukti dokumen individual)",
       "jumlah_kecocokan_sumber":len(results),
       "daftar_kecocokan_sumber":results,
       "kandidat_buku_lain":book_candidates,
       "peringatan":"ISSN/ISBN cocok pada daftar sumber/buku Scopus resmi. Jangan tampilkan ini sebagai jumlah artikel Scopus terindeks atau Q1-Q4."}
    OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"Scopus WordPress: {len(results)} sumber cocok, {len(book_candidates)} kandidat bab buku.")
if __name__=="__main__":main()
