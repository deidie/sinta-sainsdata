#!/usr/bin/env python3
"""Diagnostik publik Scholar, GARUDA, SINTA, Scopus.
Tidak mengubah publikasi_scholar.json atau publikasi_dosen.json.
Tidak melewati CAPTCHA, HTTP 403, atau login. Tidak menampilkan API key.
"""
import json,os,re,time,html
from datetime import datetime,timezone
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError,URLError
from urllib.parse import urlencode
BASE=Path(__file__).resolve().parent
OUT=BASE/"hasil"/"diagnostik_live.json"
SLUGS=["siddik","dedi","rakhmat","aidil","ika","puji"]
GARUDA_IDS=["2406700","1197451","1733344","621444","7443043","10712505"]
SCHOLAR_IDS=["btqJcxwAAAAJ","16zyvPAAAAAJ","-KDoZuAAAAAJ","ZMlFoEgAAAAJ","8znduJIAAAAJ","QcicRmEAAAAJ"]
def http(url, headers=None):
    try:
        h={"User-Agent":"SainsData-Public-Academic-Status-Check/1.0","Accept":"text/html"}
        if headers: h.update(headers)
        with urlopen(Request(url,headers=h),timeout=17) as res:
            data=res.read(450000)
            return {"http":res.status,"body":data.decode("utf-8","replace")}
    except HTTPError as e: return {"http":e.code,"error":"HTTP "+str(e.code)}
    except (URLError,TimeoutError,ValueError) as e: return {"http":None,"error":type(e).__name__}
def sample(url):
    r=http(url)
    body=r.pop("body","")
    if r["http"]==200:
        if "recaptcha" in body.lower() or "unusual traffic" in body.lower() or "captcha" in body.lower():
            r["status"]="captcha_or_block"
        else:r["status"]="received"
    else:r["status"]="denied_or_unreachable"
    return r,body
def main():
    current_scholar=json.loads((BASE/"hasil"/"publikasi_scholar.json").read_text(encoding="utf8"))
    current_garuda=json.loads((BASE/"hasil"/"publikasi_dosen.json").read_text(encoding="utf8"))
    result={"diperiksa_utc":datetime.now(timezone.utc).isoformat(),"metode":"GET publik dengan batas waktu; tidak melewati proteksi","scholar":{},"garuda":{},"sinta":{},"scopus":{}}
    result["scholar"]["snapshot"]=[{"slug":p["slug"],"artikel_tersimpan":len(p.get("artikel_scholar") or []),"cakupan_lengkap":bool(p.get("scholar_lengkap"))} for p in current_scholar.get("dosen",[])]
    # Test direct public Google Scholar, only 1 URL to avoid rate limits.
    uri="https://scholar.google.com/citations?"+urlencode({"user":SCHOLAR_IDS[0],"hl":"en","pagesize":100,"cstart":0})
    status,body=sample(uri)
    status["jumlah_baris_artikel_halaman"]=len(re.findall(r'class=["\x27][^"\x27]*\bgsc_a_tr\b',body)) if status["status"]=="received" else None
    if status["status"]=="received" and ("gsc_a_tr" not in body and "gsc_prf_in" not in body):
        status["status"]="html_tidak_sesuai"
    result["scholar"]["akses_langsung_sampel"]=status
    # Test all public GARUDA profile pages, fast status and shown count, no pages crawl.
    for slug,author_id in zip(SLUGS,GARUDA_IDS):
        status,body=sample("https://garuda.kemdiktisaintek.go.id/author/view/"+author_id)
        plain=re.sub(r"\s+"," ",html.unescape(re.sub(r"<[^>]+>"," ",body)))
        m=re.search(r"(?:Published\s*:\s*|Found\s+)([\d,.]+)\s+Documents",plain,re.I)
        status["jumlah_ditampilkan"]=int(re.sub(r"\D","",m.group(1))) if m else None
        status["panjang_html"]=len(body)
        status["ada_published"]="Published" in plain
        status["ada_documents"]="Documents" in plain
        if m is None: status["cuplikan_teks"]=plain[:160]
        status["nama_terdeteksi"]=slug if slug in SLUGS and status["status"]=="received" else None
        result["garuda"][slug]=status
        time.sleep(0.6)
    # Public SINTA author profile and journal profile
    status,body=sample("https://sinta.kemdiktisaintek.go.id/authors/profile/6054939")
    result["sinta"]["profil_penulis_sampel"]=status
    status,body=sample("https://sinta.kemdiktisaintek.go.id/journals/profile/207")
    rank=re.search(r"Sinta\s*([1-6])",body,re.I)
    status["peringkat_jurnal_tampilan"]=int(rank.group(1)) if rank else None
    result["sinta"]["jurnal_cess_sampel"]=status
    # Scopus: only request Elsevier when key is present, never echo key.
    key=os.getenv("SCOPUS_API_KEY","").strip()
    result["scopus"]["api_key_tersedia"]=bool(key)
    if key:
        hdr={"X-ELS-APIKey":key,"Accept":"application/json"}
        uri="https://api.elsevier.com/content/search/scopus?"+urlencode({"query":"DOI(10.33558/piksel.v8i2.2291)","count":1})
        status,body=sample(uri) if False else (None,None)
        res=http(uri,headers=hdr)
        status={"http":res["http"],"status":"success" if res["http"]==200 else "denied_or_error"}
        if res["http"]==200:
            try:
                data=json.loads(res.get("body","{}"))
                status["hasil_pencarian"]=((data.get("search-results") or {}).get("opensearch:totalResults"))
            except (ValueError,TypeError): status["status"]="invalid_json"
        result["scopus"]["uji_doi"]=status
    else:result["scopus"]["uji_doi"]={"status":"tidak_diuji_tanpa_api_key"}
    result["garuda"]["snapshot_total_terambil"]=sum(len(p.get("publikasi_garuda") or []) for p in current_garuda.get("dosen",[]))
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
