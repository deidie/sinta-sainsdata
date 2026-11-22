(function(){const mount=document.getElementById('sdpub26-mount');if(!mount)return;mount.innerHTML="<div id=\"sdpub26\" aria-label=\"Publikasi Dosen Program Studi Sains Data\">\n  <div class=\"sdp-shell\">\n    <header class=\"sdp-hero\">\n      <div class=\"sdp-hero-top\"><span class=\"sdp-identity\"><span class=\"sdp-ident-mark\">DS</span>  SAINS DATA</span><span id=\"sdp-status\" class=\"sdp-live\">6 profil dosen</span></div>\n      <div class=\"sdp-hero-main\"><div><p class=\"sdp-hero-eyebrow\">DATA AKADEMIK &amp; REKAM RISET</p><h1>Publikasi <span>Dosen.</span></h1><p class=\"sdp-intro\">Rekapitulasi karya ilmiah, indeksasi, dan sitasi dosen Program Studi Sains Data, Fakultas Sains dan Teknologi UIN Sumatera Utara.</p></div><div class=\"sdp-update\"><span>PEMBARUAN DATA</span><strong id=\"sdp-date\">22 November 2026</strong><small>Google Scholar · GARUDA · SINTA · Scopus</small></div></div>\n    </header>\n\n    <section class=\"sdp-stats\" aria-label=\"Rekapitulasi utama\">\n      <article class=\"sdp-stat\"><div class=\"sdp-stat-head\"><span>GARUDA</span><span class=\"sdp-stat-symbol\">G</span></div><strong id=\"sdp-total-garuda\">499</strong><p>Publikasi</p><small>Artikel dari profil GARUDA</small></article>\n      <article class=\"sdp-stat\"><div class=\"sdp-stat-head\"><span>SINTA</span><span class=\"sdp-stat-symbol sdp-symbol-sinta\">S</span></div><strong id=\"sdp-total-sinta\">312</strong><p>Publikasi SINTA</p><small id=\"sdp-sinta-caption\">Peringkat jurnal SINTA</small></article>\n      <article class=\"sdp-stat sdp-stat-feature\"><div class=\"sdp-stat-head\"><span>SCOPUS</span><span class=\"sdp-stat-symbol sdp-symbol-scopus\">Sc</span></div><strong id=\"sdp-total-scopus\">13</strong><p>Publikasi</p><small>Jurnal · prosiding · bab buku</small></article>\n      <article class=\"sdp-stat\"><div class=\"sdp-stat-head\"><span>GOOGLE SCHOLAR</span><span class=\"sdp-stat-symbol sdp-symbol-gs\">GS</span></div><strong id=\"sdp-total-cites\">4.020</strong><p>Total sitasi profil</p><small>Jumlah profil, bukan sitasi unik</small></article>\n    </section>\n\n    <div class=\"sdp-headingrow\"><div><span class=\"sdp-kicker\">GAMBARAN PROGRAM STUDI</span><h2>Produktivitas dan indeksasi</h2></div><div class=\"sdp-actions\"><label for=\"sdp-from\">Periode</label><select id=\"sdp-from\" aria-label=\"Dari tahun\"></select><span>–</span><select id=\"sdp-to\" aria-label=\"Sampai tahun\"></select></div></div>\n    <div class=\"sdp-analytics\"><div class=\"sdp-chart-grid\">\n      <section class=\"sdp-panel sdp-panel-wide\"><div class=\"sdp-panel-header\"><div><h3>Publikasi per tahun</h3><p>Tren publikasi GARUDA dan Scopus.</p></div><span class=\"sdp-legend\"><i></i> GARUDA <i class=\"sdp-legend-orange\"></i> Scopus</span></div><div id=\"sdp-bars\" class=\"sdp-bars\" role=\"img\" aria-label=\"Grafik publikasi tahunan\"></div><p class=\"sdp-smallnote\">Grafik menggunakan data publikasi yang tersedia pada sumber masing-masing.</p></section>\n      <section class=\"sdp-panel\"><div class=\"sdp-panel-header\"><div><h3>Klasifikasi SINTA</h3><p>Distribusi publikasi pada jurnal SINTA.</p></div></div><div id=\"sdp-ranks\" class=\"sdp-ranks\"></div><div class=\"sdp-rank-note\">Klasifikasi mengikuti tahun terbit jika bukti tersedia; selebihnya menggunakan peringkat jurnal dalam katalog SINTA.</div></section>\n    </div>\n\n    <section class=\"sdp-panel sdp-overview-panel\"><div class=\"sdp-panel-header\"><div><span class=\"sdp-kicker\">REKAP TAHUNAN</span><h3>Publikasi dan indeks per tahun</h3><p>Rekap publikasi unik tingkat program studi.</p></div></div><div class=\"sdp-tablewrap\"><table class=\"sdp-table\"><thead><tr><th>Tahun</th><th>GARUDA</th><th>SCOPUS</th><th>S1</th><th>S2</th><th>S3</th><th>S4</th><th>S5</th><th>S6</th></tr></thead><tbody id=\"sdp-yearbody\"></tbody></table></div><div class=\"sdp-footline\">Karya bersama dihitung satu kali pada rekap prodi. Klasifikasi SINTA didasarkan pada periode penerbitan jika telah diperiksa.</div></section>\n\n    <section class=\"sdp-panel sdp-overview-panel\"><div class=\"sdp-panel-header\"><div><span class=\"sdp-kicker\">REKAP DOSEN</span><h3>Rekapitulasi seluruh dosen</h3><p>Publikasi bersama dapat muncul di masing-masing profil dosen tetapi dihitung satu kali pada total prodi.</p></div><button class=\"sdp-soft-button\" id=\"sdp-download-recap\" type=\"button\">↓ Ekspor rekap CSV</button></div><div class=\"sdp-tablewrap\"><table class=\"sdp-table\"><thead><tr><th class=\"sdp-th-name\"><button type=\"button\" class=\"sdp-sort-btn\" data-sdp-sort=\"name\">Dosen</button></th><th><button type=\"button\" class=\"sdp-sort-btn\" data-sdp-sort=\"garuda\">GARUDA <span class=\"sdp-sort-arrow\">↓</span></button></th><th><button type=\"button\" class=\"sdp-sort-btn\" data-sdp-sort=\"sinta\">SINTA</button></th><th><button type=\"button\" class=\"sdp-sort-btn\" data-sdp-sort=\"scopus\">SCOPUS</button></th><th><button type=\"button\" class=\"sdp-sort-btn\" data-sdp-sort=\"sitasi\">Sitasi GS</button></th><th><button type=\"button\" class=\"sdp-sort-btn\" data-sdp-sort=\"hindex\">h-index GS</button></th></tr></thead><tbody id=\"sdp-staffbody\"></tbody></table></div><div class=\"sdp-footline\">Rekap per dosen mencakup artikel bersama pada setiap profil penulis.</div></section>\n      <section class=\"sdp-panel sdp-overview-panel sdp-citations\" aria-label=\"Sitasi Google Scholar per tahun\">\n        <div class=\"sdp-panel-header\"><div><span class=\"sdp-kicker\">SITASI TAHUNAN</span><h3>Jumlah sitasi per tahun</h3><p>Rincian sitasi Google Scholar setiap dosen, mengikuti periode tahun yang dipilih di atas.</p></div><small id=\"sdp-cite-status\" class=\"sdp-cite-status\">Sitasi tahunan</small></div>\n        <div class=\"sdp-tablewrap\"><table class=\"sdp-table sdp-cite-table\"><thead id=\"sdp-cite-head\"><tr><th>Dosen</th><th>2022</th><th>2023</th><th>2024</th><th>2025</th><th>2026</th></tr></thead><tbody id=\"sdp-cite-body\"><tr><td>Muhammad Siddik Hasibuan</td><td>27</td><td>55</td><td>87</td><td>152</td><td>142</td></tr><tr><td>Muhammad Dedi Irawan</td><td>228</td><td>274</td><td>272</td><td>355</td><td>244</td></tr><tr><td>Rakhmat Kurniawan R</td><td>21</td><td>24</td><td>74</td><td>160</td><td>130</td></tr><tr><td>Aidil Halim Lubis</td><td>11</td><td>35</td><td>61</td><td>107</td><td>80</td></tr><tr><td>Ika Yusnita Sari</td><td>40</td><td>33</td><td>41</td><td>44</td><td>19</td></tr><tr><td>Puji Sari Ramadhan</td><td>130</td><td>160</td><td>155</td><td>120</td><td>90</td></tr></tbody><tfoot id=\"sdp-cite-foot\"><tr><td>Total sitasi profil</td><td>457</td><td>581</td><td>690</td><td>938</td><td>705</td></tr></tfoot></table></div>\n        <div class=\"sdp-footline\">Sitasi dihitung berdasarkan tahun diterimanya sitasi. Total adalah penjumlahan sitasi profil dosen, bukan sitasi unik tingkat program studi.</div>\n      </section>\n    </div>\n\n    <section class=\"sdp-person-section\" id=\"sdp-people-section\"><div class=\"sdp-headingrow\"><div><span class=\"sdp-kicker\">DOSEN &amp; PROFIL AKADEMIK</span><h2>Profil publikasi dosen</h2></div><label class=\"sdp-search\"><span class=\"sdp-search-symbol\">⌕</span><input id=\"sdp-people-search\" type=\"search\" placeholder=\"Cari dosen...\" aria-label=\"Cari dosen\"></label></div><div id=\"sdp-people\" class=\"sdp-people\"></div></section>\n\n    <section class=\"sdp-panel sdp-library\" id=\"sdp-library\"><div class=\"sdp-panel-header\"><div><span class=\"sdp-kicker\">DIREKTORI KARYA</span><h3>Riwayat publikasi</h3><p>Telusuri artikel, prosiding, bab buku, buku terbit, dan hak cipta melalui kategori masing-masing.</p></div><div class=\"sdp-header-tools\"><button type=\"button\" class=\"sdp-soft-button\" id=\"sdp-export-works\">↓ Ekspor publikasi</button><button type=\"button\" class=\"sdp-soft-button\" id=\"sdp-print\">⎙ Cetak</button></div></div>\n      <div class=\"sdp-tabs\" role=\"group\" aria-label=\"Kategori publikasi\"><button class=\"sdp-tab active\" data-tab=\"scopus\" type=\"button\">Scopus</button><button class=\"sdp-tab\" data-tab=\"sinta\" type=\"button\">SINTA</button><button class=\"sdp-tab\" data-tab=\"all\" type=\"button\">Semua publikasi</button><button class=\"sdp-tab\" data-tab=\"book\" type=\"button\">Buku</button><button class=\"sdp-tab\" data-tab=\"ipr\" type=\"button\">HKI / IPR</button></div>\n      <div class=\"sdp-filters\"><label>Dosen<select id=\"sdp-select-person\"><option value=\"all\">Semua dosen</option></select></label><label>Tahun<select id=\"sdp-select-year\"><option value=\"all\">Semua tahun</option></select></label><label class=\"sdp-filter-query\">Cari judul / sumber<input type=\"search\" id=\"sdp-select-query\" placeholder=\"Judul, sumber, ISBN, atau nomor HKI...\"></label></div>\n      <div class=\"sdp-list-head\"><span id=\"sdp-work-count\">13 publikasi Scopus</span><small id=\"sdp-load-note\">Sumber: daftar publikasi dan profil akademik</small></div><div id=\"sdp-works\" class=\"sdp-works\" aria-live=\"polite\"></div><button id=\"sdp-more\" class=\"sdp-more\" type=\"button\" hidden=\"\">Tampilkan karya lainnya ↓</button>\n    </section>\n    <footer class=\"sdp-footer\"><div><strong>Publikasi Dosen</strong><p>Program Studi Sains Data · Fakultas Sains dan Teknologi UIN Sumatera Utara</p></div><p>Sumber data: Google Scholar, GARUDA, SINTA, Scopus, dan penerbit. Pembaruan berkala melalui repositori publikasi program studi.</p></footer>\n  </div>\n</div>";})();
(function(){'use strict';
 const root=document.getElementById('sdpub26');if(!root||root.dataset.ready)return;root.dataset.ready='1';document.body.classList.add('sdpub26-page');
 // Khusus halaman publikasi: buka pembungkus kolom WordPress, bukan hanya lebar panel internal.
 // Sidebar tema dapat berupa DIV kolom (.col-md-4) tanpa id #secondary.
 function expandPublicationLayout(){
   const sidebarSelector='#secondary,#sidebar,#right-sidebar,.sidebar,.sidebar-area,.sidebar-wrapper,.widget-area,.right-sidebar,.right_sidebar,.right-sidebar-wrapper,[role="complementary"],.widget_categories,.widget_calendar,.wp-calendar-table';
   const isSidebar=(el)=>{
     if(!el||el.nodeType!==1||el.contains(root))return false;
     const identity=(String(el.id||'')+' '+String(el.className||'')).toLowerCase();
     if(/(^|[\s_-])(sidebar|secondary|widget-area|right-widget)([\s_-]|$)/.test(identity))return true;
     if(el.matches(sidebarSelector)||el.querySelector(sidebarSelector))return true;
     if(el.matches('aside')&&el.querySelector('.widget,.widget-title,.wp-block-categories,.wp-block-calendar'))return true;
     const widgetHeadings=[...el.querySelectorAll('h2,h3,h4')].map(h=>(h.textContent||'').trim().toLowerCase());
     return widgetHeadings.some(x=>x==='categories'||x==='kategori')&&widgetHeadings.some(x=>x==='kalender'||x==='calendar');
   };
   let node=root.parentElement,depth=0;
   while(node&&node!==document.body&&depth++<24){
     // Pastikan setiap kolom dari blok HTML sampai pembungkus halaman berukuran penuh.
     if(node.id!=='sdpub26'){
       for(const [key,val] of Object.entries({width:'100%',maxWidth:'100%',minWidth:'0',flexBasis:'100%',flexGrow:'1',float:'none',gridColumn:'1 / -1'})){
         node.style.setProperty(key.replace(/[A-Z]/g,c=>'-'+c.toLowerCase()),val,'important');
       }
     }
     const parent=node.parentElement;
     if(parent&&parent!==document.body){
       let removed=false;
       for(const sibling of parent.children){
         if(sibling!==node&&isSidebar(sibling)){
           sibling.style.setProperty('display','none','important');
           sibling.setAttribute('data-sdpub-sidebar-hidden','true');
           removed=true;
         }
       }
       if(removed){
         parent.style.setProperty('grid-template-columns','minmax(0,1fr)','important');
         parent.style.setProperty('flex-wrap','wrap','important');
       }
     }
     if(node.matches('#content,.site-content,#main-content,.site-content-wrapper'))break;
     node=parent;
   }
 }
 expandPublicationLayout();
 // Custom HTML dapat dieksekusi sebelum sidebar tema dirender. Ulangi saat DOM selesai.
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',expandPublicationLayout,{once:true});
 else requestAnimationFrame(expandPublicationLayout);
 const BASE='https://raw.githubusercontent.com/deidie/sinta-sainsdata/main/hasil/';
 const E=id=>root.querySelector('#'+id),N=x=>Number.isFinite(Number(x))?Number(x):0,F=x=>new Intl.NumberFormat('id-ID').format(N(x));
 const esc=x=>String(x==null?'':x).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const key=x=>String(x||'').toLowerCase().normalize('NFKD').replace(/[\u0300-\u036f]/g,'').replace(/[^a-z0-9]+/g,' ').trim();
 const doi=x=>String(x||'').toLowerCase().trim().replace(/^https?:\/\/(dx\.)?doi\.org\//,'');
 const href=x=>typeof x==='string'&&/^https:\/\//i.test(x)?x:null;
 const staff=[
  {slug:'siddik',name:'Muhammad Siddik Hasibuan',photo:'https://sainsdata.uinsu.ac.id/wp-content/uploads/2026/04/Siddik.jpeg',sinta:'5983919',garuda:'2406700',scholar:'btqJcxwAAAAJ',scopus:null},
  {slug:'dedi',name:'Muhammad Dedi Irawan',photo:'https://sainsdata.uinsu.ac.id/wp-content/uploads/2026/09/Dedi.png',sinta:'6054939',garuda:'1197451',scholar:'16zyvPAAAAAJ',scopus:'58996427700'},
  {slug:'rakhmat',name:'Rakhmat Kurniawan R',photo:'https://sainsdata.uinsu.ac.id/wp-content/uploads/2026/09/RKR.png',sinta:'6160028',garuda:'1733344',scholar:'-KDoZuAAAAAJ',scopus:'58190434200'},
  {slug:'aidil',name:'Aidil Halim Lubis',photo:'https://sainsdata.uinsu.ac.id/wp-content/uploads/2026/09/Aidilbatik.png',sinta:'6795618',garuda:'621444',scholar:'ZMlFoEgAAAAJ',scopus:null},
  {slug:'ika',name:'Ika Yusnita Sari',photo:'https://sainsdata.uinsu.ac.id/wp-content/uploads/2026/09/Ika.png',sinta:'6745259',garuda:'7443043',scholar:'8znduJIAAAAJ',scopus:null},
  {slug:'puji',name:'Puji Sari Ramadhan',photo:'https://sainsdata.uinsu.ac.id/wp-content/uploads/2026/09/Puji.png',sinta:'6089755',garuda:'2469503',scholar:'QcicRmEAAAAJ',scopus:'57222343067'}
 ];
 const fallbackScopus=[
  ['Evaluating browser-based immersive technology for cultural heritage',2026,'jurnal','dedi','International Journal of Informatics and Communication Technology','10.11591/ijict.v15i4.pp1664-1672'],
  ['Genetic algorithm-optimized BERTopic with SHAP explainability for institutional research trend analysis',2026,'jurnal','dedi','IAES International Journal of Artificial Intelligence','10.11591/ijai.v15.i4.pp3818-3826'],
  ['Future Trends in Intelligent Construction Monitoring Technologies',2026,'bab_buku','dedi','Intelligent Construction Monitoring Systems: Real-Time Safety, Environmental Prediction, and Risk Management','10.4018/979-8-3373-9245-5.ch010'],
  ['Mapping of crime prone areas in Batubara districts using the k-means method',2024,'prosiding','dedi','AIP Conference Proceedings',null],
  ['Latent Semantic Indexing for Indonesian text similarity',2018,'jurnal','dedi','International Journal of Engineering and Technology (UAE)',null],
  ['AI for Inclusion: Sign Language Recognition to Support Hajj Pilgrims',2026,'bab_buku','siddik,aidil','From Smart Cities to the Metaverse: Games, Immersive Experiences, and the Future of Digital Interaction','10.1201/9781003662433-18'],
  ['Higher Education and Health Breakthroughs: Residual Network for Pneumonia Detection from Chest X-ray Images',2025,'jurnal','siddik','International Journal on Advanced Science, Engineering and Information Technology',null],
  ['NEURO NETWORK TECHNIQUES OF TELEMETRY MULTIVARIATE TIME SERIES PROCESSING AND THEIR APPLICATIONS IN INDUSTRY',2022,'jurnal','siddik','Journal of Theoretical and Applied Information Technology',null],
  ['Intelligent LPG Gas Leak Detection Tool with SMS Notification',2019,'prosiding','siddik','Journal of Physics: Conference Series',null],
  ['Checking the Answer Sheet with Image Recognition',2018,'jurnal','siddik','Journal of Information Technology Education: Research',null],
  ['A Micromechanical Data-Driven Machine-Learning Approach for Microstructural Characterization of Solder Balls in Electronic Packages Subjected to Thermomechanical Fatigue',2023,'jurnal','rakhmat','Journal of Electronic Materials',null],
  ['Smart Machine Learning Approaches for Detection of Malicious Unified Resource Locator: Towards Sustainable Cybersecurity Systems',2026,'bab_buku','rakhmat','Smart, Secure, and Sustainable Digital Futures: AI, Cybersecurity, and Governance in Emerging Digital Systems','10.1201/9781042013098-10'],
  ['Comparison of Knowledge-Based Reasoning Methods to Measure the Effectiveness of Diagnostic Results',2021,'prosiding','puji','Journal of Physics: Conference Series',null]
 ].map((x,i)=>({judul:x[0],tahun:x[1],jenis:x[2],dosen:x[3].split(','),jurnal:x[4],doi:x[5],url_scopus:({5:'https://www.scopus.com/pages/publications/105035278259?origin=resultslist',10:'https://www.scopus.com/pages/publications/85153088849?origin=resultslist',11:'https://www.scopus.com/pages/publications/105051027879?origin=resultslist',12:'https://www.scopus.com/pages/publications/85102337587?origin=resultslist'})[i]||null,tautan_penerbit:i===2?'https://www.igi-global.com/chapter/future-trends-in-intelligent-construction-monitoring-technologies/401484':null}));
 const yearlyDefaults=[{tahun:2026,publikasi:43,S1:0,S2:1,S3:1,S4:6,S5:1,S6:0},{tahun:2025,publikasi:89,S1:0,S2:1,S3:0,S4:0,S5:0,S6:0},{tahun:2024,publikasi:127,S1:0,S2:0,S3:0,S4:0,S5:0,S6:0},{tahun:2023,publikasi:68,S1:0,S2:1,S3:0,S4:0,S5:0,S6:0},{tahun:2022,publikasi:37,S1:0,S2:0,S3:0,S4:0,S5:0,S6:0}];
 const personDefaults=[{slug:'siddik',garuda:90},{slug:'dedi',garuda:180},{slug:'rakhmat',garuda:149},{slug:'aidil',garuda:46},{slug:'ika',garuda:16},{slug:'puji',garuda:87}];
 const gsDefaults=[{slug:'siddik',metrik_scholar:{sitasi:529,h_index:12}},{slug:'dedi',metrik_scholar:{sitasi:1629,h_index:18}},{slug:'rakhmat',metrik_scholar:{sitasi:442,h_index:10}},{slug:'aidil',metrik_scholar:{sitasi:326,h_index:8}},{slug:'ika',metrik_scholar:{sitasi:200,h_index:4}},{slug:'puji',metrik_scholar:{sitasi:894,h_index:14}}];
 const historicalDoi=[['10.20895/infotel.v15i1.848',2],['10.24002/ijis.v7i2.10213',2],['10.12928/spekta.v7i1.15674',2]];
  const fallbackExtra={buku:[],ipr:[]};
  const data={extra:fallbackExtra,scopus:{publikasi:fallbackScopus},sinta:{total_sinta:312,peringkat:{S1:0,S2:7,S3:49,S4:153,S5:49,S6:4},per_dosen:[{slug:'siddik',total:48,peringkat:{S1:0,S2:3,S3:11,S4:26,S5:4,S6:4}},{slug:'dedi',total:88,peringkat:{S1:0,S2:3,S3:16,S4:51,S5:18,S6:0}},{slug:'rakhmat',total:101,peringkat:{S1:0,S2:1,S3:20,S4:52,S5:28,S6:0}},{slug:'aidil',total:25,peringkat:{S1:0,S2:0,S3:2,S4:20,S5:3,S6:0}},{slug:'ika',total:7,peringkat:{S1:0,S2:0,S3:1,S4:5,S5:1,S6:0}},{slug:'puji',total:1,peringkat:{S1:0,S2:0,S3:0,S4:1,S5:0,S6:0}}],per_tahun:[{tahun:2026,publikasi:43,sinta:23,peringkat:{S1:0,S2:1,S3:5,S4:15,S5:2,S6:0}},{tahun:2025,publikasi:89,sinta:51,peringkat:{S1:0,S2:2,S3:11,S4:36,S5:2,S6:0}},{tahun:2024,publikasi:127,sinta:84,peringkat:{S1:0,S2:0,S3:18,S4:54,S5:12,S6:0}},{tahun:2023,publikasi:68,sinta:41,peringkat:{S1:0,S2:3,S3:7,S4:25,S5:6,S6:0}},{tahun:2022,publikasi:37,sinta:21,peringkat:{S1:0,S2:0,S3:2,S4:11,S5:8,S6:0}}],artikel:[]},history:{rekap_prodi:{publikasi_sinta_saat_terbit_terverifikasi:11,jurnal_dipadan_peringkat_terkini:260,peringkat:{S1:0,S2:3,S3:1,S4:6,S5:1,S6:0}},tabel_per_tahun:yearlyDefaults,tabel_per_dosen:staff.map(p=>({slug:p.slug,terverifikasi_terbit:p.slug==='dedi'?3:p.slug==='rakhmat'?8:0,S1:0,S2:p.slug==='dedi'?3:0,S3:p.slug==='rakhmat'?1:0,S4:p.slug==='rakhmat'?6:0,S5:p.slug==='rakhmat'?1:0,S6:0})),artikel_peringkat_terverifikasi:historicalDoi.map(([d,r])=>({doi:d,peringkat_sinta_saat_terbit:r}))},recap:{rekap_prodi:{garuda_unik:499},tabel_per_tahun:yearlyDefaults,tabel_per_dosen:personDefaults},scholar:{dosen:gsDefaults},garuda:null,garudaAttempted:false,tab:'scopus',library:[],visible:18,loaded:{}};

  // Snapshot dasar 22 November 2026; jika GitHub dapat diakses, dataset terbaru menggantikannya.
  data.recap.rekap_prodi.garuda_unik=499;
  data.recap.tabel_per_tahun=[[2026,53],[2025,98],[2024,136],[2023,81],[2022,54],[2021,18],[2020,18],[2019,19],[2018,11],[2017,8],[2016,2],[2013,1]].map(([tahun,publikasi])=>({tahun,publikasi}));
  data.recap.tabel_per_dosen=[['siddik',90],['dedi',180],['rakhmat',149],['aidil',46],['ika',16],['puji',87]].map(([slug,garuda])=>({slug,garuda}));
  data.sinta.total_sinta=312;
  data.sinta.peringkat={S1:0,S2:9,S3:49,S4:188,S5:62,S6:4};
  data.sinta.per_tahun=[[2026,53,1,5,17,4,0],[2025,98,2,11,40,4,0],[2024,136,0,18,59,13,0],[2023,81,4,7,30,8,0],[2022,54,0,2,21,10,0],[2021,18,0,1,5,6,0],[2020,18,2,3,5,5,0],[2019,19,0,0,6,5,0],[2018,11,0,1,2,4,1],[2017,8,0,1,2,3,1],[2016,2,0,0,0,0,2],[2013,1,0,0,1,0,0]].map(([tahun,publikasi,S2,S3,S4,S5,S6])=>({tahun,publikasi,peringkat:{S1:0,S2,S3,S4,S5,S6}}));
  data.sinta.per_dosen=[['siddik',48,3,11,26,4,4],['dedi',88,3,16,51,18,0],['rakhmat',101,1,20,53,27,0],['aidil',25,0,2,20,3,0],['ika',7,0,1,5,1,0],['puji',51,2,0,36,13,0]].map(([slug,total,S2,S3,S4,S5,S6])=>({slug,total,peringkat:{S1:0,S2,S3,S4,S5,S6}}));
 const findP=slug=>staff.find(p=>p.slug===slug)||{name:slug},recP=slug=>(data.recap.tabel_per_dosen||[]).find(x=>x.slug===slug)||{},histP=slug=>(data.history.tabel_per_dosen||[]).find(x=>x.slug===slug)||{},gsP=slug=>(data.scholar.dosen||[]).find(x=>x.slug===slug)?.metrik_scholar||{};
 const sintaP=slug=>(data.sinta.per_dosen||[]).find(x=>x.slug===slug)||{};
 const scRows=()=>data.scopus?.publikasi||[];
 const scCount=slug=>{let cnt=scRows().filter(x=>(x.dosen||[]).includes(slug)).length;return cnt?cnt:null;};
 const scYear=year=>new Set(scRows().filter(x=>N(x.tahun)===N(year)).map(x=>x.scopus_eid||doi(x.doi)||key(x.judul)+'|'+x.tahun)).size;
 async function loadJson(file,timeout=17000){const c=new AbortController(),t=setTimeout(()=>c.abort(),timeout);try{const r=await fetch(BASE+file+'?v='+Date.now(),{mode:'cors',cache:'no-store',signal:c.signal});if(!r.ok)throw Error('HTTP '+r.status);return await r.json();}finally{clearTimeout(t)}}
 function years(){const yy=(data.recap.tabel_per_tahun||[]).map(y=>N(y.tahun));return [...new Set(yy)].filter(v=>v>=2013).sort((a,b)=>a-b);}
 function selectors(){const a=E('sdp-from'),b=E('sdp-to'),old1=a.value,old2=b.value,ys=years(),options=ys.map(y=>'<option value="'+y+'">'+y+'</option>').join('');a.innerHTML=b.innerHTML=options;if(ys.length){a.value=ys.includes(N(old1))?old1:String(Math.max(ys[0],ys[ys.length-1]-4));b.value=ys.includes(N(old2))?old2:String(ys[ys.length-1]);}}
 function currentYears(){let a=N(E('sdp-from').value),b=N(E('sdp-to').value);if(a>b)[a,b]=[b,a];return (data.recap.tabel_per_tahun||[]).filter(r=>N(r.tahun)>=a&&N(r.tahun)<=b).sort((a,b)=>N(b.tahun)-N(a.tahun));}
 function updateTop(){
   E('sdp-total-garuda').textContent=F(data.recap.rekap_prodi?.garuda_unik??499);
   E('sdp-total-sinta').textContent=F(data.sinta?.total_sinta??0);
   E('sdp-total-scopus').textContent=F(scRows().length);
   E('sdp-total-cites').textContent=F((data.scholar.dosen||[]).reduce((n,x)=>n+N(x.metrik_scholar?.sitasi),0));
   E('sdp-sinta-caption').textContent='Publikasi pada jurnal SINTA';
 }

 function renderBars(){const rr=currentYears(),max=Math.max(1,...rr.map(x=>N(x.publikasi)));E('sdp-bars').innerHTML=rr.map(x=>'<div class="sdp-barline"><strong>'+esc(x.tahun)+'</strong><div class="sdp-bargrid"><div class="sdp-track"><span style="width:'+Math.max(1,Math.round(N(x.publikasi)/max*100))+'%"></span></div><div class="sdp-track sdp-track-secondary" title="Scopus: '+scYear(x.tahun)+'"><span style="width:'+Math.max(1,Math.round(scYear(x.tahun)/max*100))+'%"></span></div></div><b>'+F(x.publikasi)+'</b></div>').join('')||'<p class="sdp-empty">Data periode belum tersedia.</p>';
 E('sdp-yearbody').innerHTML=rr.map(r=>{const h=(data.sinta.per_tahun||[]).find(x=>N(x.tahun)===N(r.tahun))?.peringkat||{};return '<tr><td>'+esc(r.tahun)+'</td><td class="sdp-high">'+F(r.publikasi)+'</td><td>'+F(scYear(r.tahun))+'</td>'+[1,2,3,4,5,6].map(k=>'<td>'+F(h['S'+k])+'</td>').join('')+'</tr>'}).join('')||'<tr><td colspan="9">Belum ada data pada periode ini.</td></tr>';}
 function renderRanks(){const r=data.sinta.peringkat||{},arr=[1,2,3,4,5,6].map(k=>({label:'SINTA '+k,count:N(r['S'+k])})),max=Math.max(1,...arr.map(v=>v.count));E('sdp-ranks').innerHTML=arr.map(x=>'<div class="sdp-rank"><span class="sdp-rank-label">'+x.label+'</span><div class="sdp-rank-track"><span style="width:'+(x.count?Math.round(x.count/max*100):0)+'%"></span></div><b>'+F(x.count)+'</b></div>').join('');}
 // Tabel sitasi selalu memiliki data awal yang tervalidasi dari pembaruan 21 November 2026.
 // Hasil Google Scholar terbaru dapat memperbarui nilai per tahun, tanpa mengosongkan nilai lama.
 const scholarAnnualSnapshot={"siddik":{"2017":2,"2018":8,"2019":5,"2020":15,"2021":22,"2022":27,"2023":55,"2024":87,"2025":152,"2026":142},"dedi":{"2018":18,"2019":15,"2020":51,"2021":104,"2022":228,"2023":274,"2024":272,"2025":355,"2026":244},"rakhmat":{"2019":3,"2020":5,"2021":15,"2022":21,"2023":24,"2024":74,"2025":160,"2026":130},"aidil":{"2019":3,"2020":5,"2021":10,"2022":11,"2023":35,"2024":61,"2025":107,"2026":80},"ika":{"2020":2,"2021":12,"2022":40,"2023":33,"2024":41,"2025":44,"2026":19},"puji":{"2018":31,"2019":49,"2020":41,"2021":95,"2022":130,"2023":160,"2024":155,"2025":120,"2026":90}};
 const scholarAnnualLive={};
 const scholarWebApp='https://script.google.com/macros/s/AKfycbyZzldxXqRzIW0SKqDcIZLiz3GpIiY2uzAj8IPVRJau-6nM_cK7-OI1xoKA_HFWfm7Q/exec';
 const annualNumber=(o,y)=>o&&Object.prototype.hasOwnProperty.call(o,String(y))&&Number.isFinite(Number(o[String(y)]))?Math.max(0,Number(o[String(y)])):null;
 function scholarYear(slug,year){
   const fresh=annualNumber(scholarAnnualLive[slug],year);
   if(fresh!==null)return fresh;
   const published=(data.scholar.dosen||[]).find(p=>p.slug===slug)?.sitasi_tahunan;
   const existing=annualNumber(published,year);
   if(existing!==null)return existing;
   return annualNumber(scholarAnnualSnapshot[slug],year);
 }
 function renderCitations(){
   let from=N(E('sdp-from').value),to=N(E('sdp-to').value);
   if(from>to)[from,to]=[to,from];
   const yy=Array.from({length:Math.max(0,Math.min(to-from+1,70))},(_,i)=>from+i);
   E('sdp-cite-head').innerHTML='<tr><th>Dosen</th>'+yy.map(y=>'<th>'+y+'</th>').join('')+'</tr>';
   E('sdp-cite-body').innerHTML=staff.map(p=>'<tr><td>'+esc(p.name)+'</td>'+yy.map(y=>{const v=scholarYear(p.slug,y);return '<td>'+(v===null?'—':F(v))+'</td>'}).join('')+'</tr>').join('');
   E('sdp-cite-foot').innerHTML='<tr><td>Total sitasi profil</td>'+yy.map(y=>{const vals=staff.map(p=>scholarYear(p.slug,y)).filter(x=>x!==null);return '<td class="sdp-high">'+(vals.length?F(vals.reduce((a,b)=>a+b,0)):'—')+'</td>'}).join('')+'</tr>';
 }
 function updateScholarAnnualFromWebApp(p){
   const callback='sdAnnualCitation_'+p.slug+'_'+Date.now();
   const node=document.createElement('script');let finished=false;let timer;
   const finish=result=>{
     if(finished)return;finished=true;clearTimeout(timer);try{delete window[callback]}catch(e){window[callback]=undefined;}node.remove();
     if(!result||result.error||!Array.isArray(result.graph))return;
     const values={};
     for(const point of result.graph){const year=Number(point.year),n=Number(point.citations);if(Number.isInteger(year)&&year>=1900&&year<=2100&&Number.isFinite(n)&&n>=0)values[year]=n;}
     if(Object.keys(values).length){scholarAnnualLive[p.slug]=values;renderCitations();}
   };
   window[callback]=finish;
   node.onerror=()=>finish(null);
   node.src=scholarWebApp+'?slug='+encodeURIComponent(p.slug)+'&callback='+encodeURIComponent(callback);
   timer=setTimeout(()=>finish(null),13000);
   document.head.appendChild(node);
 }
  const xCount=(slug,ty)=>data.extraLoaded?(data.extra?.[ty]||[]).filter(x=>(x.dosen||[]).includes(slug)).length:N(data.extra_counts?.[slug]?.[ty]);
  const sortState={field:'garuda',descending:true};
 function renderStaff(){
  const rows=staff.map(p=>{const g=gsP(p.slug),s=sintaP(p.slug),r=recP(p.slug),sc=scCount(p.slug);return {name:p.name,garuda:N(r.garuda),sinta:N(s.total),scopus:sc??0,scopusMissing:sc===null,sitasi:N(g.sitasi),hindex:N(g.h_index)};});
  rows.sort((a,b)=>{const f=sortState.field,v=f==='name'?String(a.name).localeCompare(String(b.name),'id'):N(a[f])-N(b[f]);return (sortState.descending?-1:1)*v||String(a.name).localeCompare(String(b.name),'id');});
  E('sdp-staffbody').innerHTML=rows.map(x=>'<tr><td>'+esc(x.name)+'</td><td>'+F(x.garuda)+'</td><td class="sdp-high">'+F(x.sinta)+'</td><td class="sdp-high">'+(x.scopusMissing?'—':F(x.scopus))+'</td><td>'+F(x.sitasi)+'</td><td>'+F(x.hindex)+'</td></tr>').join('');
  root.querySelectorAll('[data-sdp-sort]').forEach(btn=>{
   const active=btn.dataset.sdpSort===sortState.field;
   btn.setAttribute('aria-pressed',String(active));btn.parentElement.setAttribute('aria-sort',active?(sortState.descending?'descending':'ascending'):'none');
   const label={name:'Dosen',garuda:'GARUDA',sinta:'SINTA',scopus:'SCOPUS',sitasi:'Sitasi GS',hindex:'h-index GS'}[btn.dataset.sdpSort];
   btn.innerHTML=esc(label)+(active?' <span class="sdp-sort-arrow">'+(sortState.descending?'↓':'↑')+'</span>':'');
  });
 }
 root.querySelectorAll('[data-sdp-sort]').forEach(btn=>btn.addEventListener('click',()=>{
  const field=btn.dataset.sdpSort;
  if(sortState.field===field)sortState.descending=!sortState.descending;
  else{sortState.field=field;sortState.descending=field!=='name';}
  renderStaff();
 }));
 function renderPeople(){const q=key(E('sdp-people-search').value);let list=staff.filter(p=>key(p.name).includes(q));E('sdp-people').innerHTML=list.map(p=>{const h=sintaP(p.slug),g=gsP(p.slug),r=recP(p.slug),sc=scCount(p.slug),s=[1,2,3,4,5,6].filter(k=>N(h.peringkat?.['S'+k])).map(k=>'<span class="sdp-chip">SINTA '+k+' · '+F(h.peringkat?.['S'+k])+'</span>').join('');const chipExtra=(xCount(p.slug,'buku')?'<span class="sdp-chip">Buku · '+F(xCount(p.slug,'buku'))+'</span>':'')+(xCount(p.slug,'ipr')?'<span class="sdp-chip">HKI · '+F(xCount(p.slug,'ipr'))+'</span>':'');const links=[['Scholar','https://scholar.google.com/citations?user='+p.scholar,'scholar'],['GARUDA','https://garuda.kemdiktisaintek.go.id/author/view/'+p.garuda,'garuda'],['SINTA','https://sinta.kemdiktisaintek.go.id/authors/profile/'+p.sinta,'sinta'],['Scopus',p.scopus?'https://www.scopus.com/authid/detail.uri?authorId='+p.scopus:'https://sinta.kemdiktisaintek.go.id/authors/profile/'+p.sinta+'/?view=scopus','scopus']];return '<article class="sdp-person-card"><div class="sdp-person-head"><a class="sdp-photo" href="'+esc(p.photo)+'" target="_blank" rel="noopener noreferrer" title="Lihat foto '+esc(p.name)+'" aria-label="Lihat foto asli '+esc(p.name)+'">'+esc(p.name.split(' ').slice(0,2).map(t=>t[0]).join(''))+'<img src="'+esc(p.photo)+'" alt="Foto '+esc(p.name)+'" loading="lazy" decoding="async" onerror="this.remove()"></a><div><div class="sdp-person-name">'+esc(p.name)+'</div><small>Dosen Program Studi Sains Data</small></div></div><div class="sdp-person-stats"><div><span>GARUDA</span><b>'+F(r.garuda)+'</b></div><div><span>SCOPUS</span><b>'+(sc===null?'—':F(sc))+'</b></div><div><span>Sitasi GS</span><b>'+F(g.sitasi)+'</b></div></div><div class="sdp-chiprow">'+s+chipExtra+'</div><div class="sdp-social">'+links.map(([name,url,kind])=>'<a href="'+esc(url)+'" data-kind="'+kind+'" target="_blank" rel="noopener noreferrer" aria-label="Profil '+name+' '+esc(p.name)+'">'+name+'</a>').join('')+'</div><button type="button" class="sdp-person-action" data-open="'+esc(p.slug)+'">Lihat karya &amp; indeksasi ↗</button></article>'}).join('')||'<p class="sdp-empty">Dosen tidak ditemukan.</p>';root.querySelectorAll('[data-open]').forEach(b=>b.addEventListener('click',()=>{E('sdp-select-person').value=b.dataset.open;setTab('all');E('sdp-library').scrollIntoView({behavior:'smooth',block:'start'});}));}
 // Gabungkan sumber dengan DOI, judul, dan tahun agar publikasi bersama tidak dihitung ganda.
  function mergeRows(){
    const map=new Map(),byTitle=new Map();
    function add(a,slug,source){
      const title=key(a.judul)+'|'+a.tahun, id=doi(a.doi)?'doi:'+doi(a.doi):a.scopus_eid?'eid:'+a.scopus_eid:'title:'+title;
      let v=map.get(id)||byTitle.get(title);
      if(!v){v={judul:a.judul||'',tahun:a.tahun||null,jurnal:a.jurnal||'',doi:a.doi||null,jenis:a.jenis||'jurnal',scopus:false,garuda:false,scholar:false,book:false,dosen:[],scopusURL:null,publisherURL:null,sourceURL:null,sintaHistory:null,sintaCurrent:null,extra:false};map.set(id,v);byTitle.set(title,v);}
      if(slug&&!v.dosen.includes(slug))v.dosen.push(slug);
      for(const k of Array.isArray(a.dosen)?a.dosen:[])if(!v.dosen.includes(k))v.dosen.push(k);
      if(source==='scopus'){v.scopus=true;v.jenis=a.jenis||v.jenis;v.jurnal=a.jurnal||v.jurnal;v.scopusURL=href(a.url_scopus)||v.scopusURL;v.publisherURL=href(a.tautan_penerbit)||v.publisherURL;v.doi=a.doi||v.doi;v.quartile_scopus=a.quartile_scopus||v.quartile_scopus;}
      if(source==='garuda'){v.garuda=true;v.sourceURL=href(a.url_doi)||href(a.url_garuda)||href(a.url_artikel)||v.sourceURL;v.jurnal=v.jurnal||a.jurnal;v.sintaCurrent=a.jurnal_sinta_peringkat_terkini||v.sintaCurrent;}
      if(source==='google'){v.scholar=true;v.jurnal=v.jurnal||a.jurnal;}
      v.book=v.book||['bab_buku','buku'].includes(v.jenis);
      return v;
    }
    for(const a of data.scopus?.publikasi||[])add(a,null,'scopus');
    for(const d of data.garuda?.dosen||[])for(const a of d.publikasi_garuda||[])add(a,d.slug,'garuda');
    const evidence=new Map((data.history.artikel_peringkat_terverifikasi||[]).filter(x=>x.doi).map(x=>[doi(x.doi),x.peringkat_sinta_saat_terbit]));
    const sintaArticles=new Map((data.sinta.artikel||[]).filter(x=>x.doi).map(x=>[doi(x.doi),x]));
    for(const x of new Set(map.values())){const id=doi(x.doi);if(!id)continue;const hit=sintaArticles.get(id);if(hit){x.sintaCurrent=hit.sinta_jurnal_kini||x.sintaCurrent;if(hit.sinta_saat_terbit)x.sintaHistory=hit.sinta_saat_terbit;}if(evidence.has(id))x.sintaHistory=evidence.get(id);}
    data.library=[...new Set(map.values())].sort((a,b)=>N(b.tahun)-N(a.tahun)||Number(b.scopus)-Number(a.scopus)||String(a.judul).localeCompare(String(b.judul),'id'));
    const ysel=E('sdp-select-year'),old=ysel.value,ys=[...new Set([...data.library,...(data.extra?.buku||[]),...(data.extra?.ipr||[])].map(x=>N(x.tahun)).filter(v=>v>=1900))].sort((a,b)=>b-a);
    ysel.innerHTML='<option value="all">Semua tahun</option>'+ys.map(y=>'<option value="'+y+'">'+y+'</option>').join('');if(ys.map(String).includes(old))ysel.value=old;
  }
  function filtered(){
    const p=E('sdp-select-person').value,y=E('sdp-select-year').value,q=key(E('sdp-select-query').value);
    const isExtra=data.tab==='book'||data.tab==='ipr';
    const rows=isExtra?(data.extra?.[data.tab==='book'?'buku':'ipr']||[]):data.library;
    return rows.filter(x=>
       (p==='all'||(x.dosen||[]).includes(p)) &&
       (y==='all'||String(x.tahun)===y) &&
       (!q||key([x.judul,x.jurnal,x.penulis,x.penerbit,x.pemegang_hak,x.isbn,x.nomor_permohonan,x.nomor_pencatatan].filter(Boolean).join(' ')).includes(q)) &&
       (isExtra||data.tab==='all'||(data.tab==='scopus'&&x.scopus)||(data.tab==='sinta'&&(x.sintaHistory||x.sintaCurrent)))
    ).sort((a,b)=>data.tab==='book'||data.tab==='ipr'?N(b.tahun)-N(a.tahun)||String(a.judul).localeCompare(String(b.judul),'id'):0);
  }
  function renderWorks(){
    const rows=filtered(),isBooks=data.tab==='book',isIpr=data.tab==='ipr',extra=isBooks||isIpr;
    E('sdp-work-count').textContent=F(rows.length)+(isBooks?' buku sesuai filter':isIpr?' HKI sesuai filter':' publikasi sesuai filter');
    E('sdp-load-note').textContent=extra?'Sumber: riwayat buku dan HKI profil SINTA':data.garuda?'Riwayat publikasi GARUDA dan Scopus':data.garudaAttempted?'Daftar Scopus ditampilkan':'Daftar publikasi berdasarkan kategori';
    E('sdp-works').innerHTML=rows.slice(0,data.visible).map(x=>{
      if(extra){
        const names=(x.dosen||[]).map(sl=>findP(sl).name).join(', ');
        const proof=href(x.sumber_profil_sinta);
        const title=proof?'<a href="'+esc(proof)+'" target="_blank" rel="noopener noreferrer">'+esc(x.judul)+'</a>':esc(x.judul);
        const tags=isBooks?'<span class="sdp-tag book">Buku</span>'+(x.jenis_buku?'<span class="sdp-tag">'+esc(x.jenis_buku)+'</span>':'')+(x.isbn?'<span class="sdp-tag">ISBN '+esc(x.isbn)+'</span>':''):'<span class="sdp-tag sinta">Hak Cipta</span>'+(x.nomor_permohonan?'<span class="sdp-tag">'+esc(x.nomor_permohonan)+'</span>':'')+(x.nomor_pencatatan?'<span class="sdp-tag">Pencatatan '+esc(x.nomor_pencatatan)+'</span>':'');
        const source=isBooks?[x.penerbit,x.tempat_terbit,x.tahun].filter(Boolean).join(' · '):[x.tahun,x.pemegang_hak?'Pemegang hak: '+x.pemegang_hak:null].filter(Boolean).join(' · ');
        const authors=x.penulis?'<div class="sdp-work-meta sdp-extra-authors">'+esc(isBooks?'Penulis: ':'Pencipta: ')+esc(x.penulis)+'</div>':'';
        return '<article class="sdp-work"><div><h4>'+title+'</h4><div class="sdp-work-meta">'+esc(source)+'</div>'+authors+'<div class="sdp-work-meta">Dosen: '+esc(names)+'</div><div class="sdp-work-tags">'+tags+'</div></div>'+(proof?'<a class="sdp-work-link" target="_blank" rel="noopener noreferrer" href="'+esc(proof)+'">Lihat SINTA ↗</a>':'')+'</article>';
      }
      const tags=[];
      if(x.scopus)tags.push('<span class="sdp-tag scopus">Scopus'+(x.quartile_scopus?' · '+esc(x.quartile_scopus):'')+'</span>');
      if(x.sintaHistory)tags.push('<span class="sdp-tag sinta">SINTA '+esc(x.sintaHistory)+'</span>');else if(x.sintaCurrent)tags.push('<span class="sdp-tag sinta">SINTA '+esc(x.sintaCurrent)+'</span>');
      if(x.jenis==='bab_buku')tags.push('<span class="sdp-tag book">Bab buku</span>');else if(x.jenis==='prosiding')tags.push('<span class="sdp-tag">Prosiding</span>');
      if(x.garuda)tags.push('<span class="sdp-tag">GARUDA</span>');
      const url=x.scopusURL||x.publisherURL||(x.doi?'https://doi.org/'+doi(x.doi):null)||x.sourceURL,proof=href(url),persons=x.dosen.map(sl=>findP(sl).name).join(', ');
      return '<article class="sdp-work"><div><h4>'+(proof?'<a href="'+esc(proof)+'" target="_blank" rel="noopener noreferrer">'+esc(x.judul)+'</a>':esc(x.judul))+'</h4><div class="sdp-work-meta">'+esc(x.jurnal||'Sumber belum dicatat')+' · '+esc(x.tahun||'')+(persons?' · '+esc(persons):'')+'</div><div class="sdp-work-tags">'+tags.join('')+'</div></div>'+(proof?'<a class="sdp-work-link" target="_blank" rel="noopener noreferrer" href="'+esc(proof)+'">Lihat sumber ↗</a>':'')+'</article>';
    }).join('')||'<p class="sdp-empty">Belum ada '+(isBooks?'buku':isIpr?'HKI':'publikasi')+' pada filter ini.</p>';
    E('sdp-more').hidden=rows.length<=data.visible;
  }
 async function fetchGaruda(){if(data.garuda||data.garudaAttempted)return;data.garudaAttempted=true;try{const j=await loadJson('publikasi_dosen.json',22000);if(!Array.isArray(j.dosen))throw Error('format');data.garuda=j;}catch(e){}mergeRows();renderWorks();}
 let extraRequest=null;
 async function fetchExtra(){
  if(data.extraLoaded||extraRequest)return extraRequest;
  extraRequest=loadJson('publikasi_tambahan_dosen.json',16000).then(x=>{
   if(!Array.isArray(x.buku)||!Array.isArray(x.ipr))throw Error('format');
   data.extra=x;data.extraLoaded=true;renderPeople();mergeRows();renderWorks();
  }).catch(()=>{E('sdp-works').innerHTML='<p class="sdp-empty">Daftar belum dapat dimuat. Silakan buka tab kembali.</p>';}).finally(()=>{extraRequest=null});
  return extraRequest;
 }
 function setTab(tab){data.tab=tab;data.visible=18;root.querySelectorAll('.sdp-tab').forEach(b=>{b.classList.toggle('active',b.dataset.tab===tab);b.setAttribute('aria-pressed',String(b.dataset.tab===tab));});E('sdp-select-query').placeholder=tab==='book'?'Judul, penulis, penerbit, atau ISBN...':tab==='ipr'?'Judul, pencipta, atau nomor permohonan HKI...':'Cari judul atau sumber...';if(['all','sinta'].includes(tab))fetchGaruda();mergeRows();renderWorks();if(['book','ipr'].includes(tab)&&!data.extraLoaded){E('sdp-work-count').textContent='Memuat daftar...';E('sdp-works').innerHTML='<p class="sdp-empty">Memuat data dari GitHub...</p>';fetchExtra();}}
 function exportCSV(name,head,rows){const csv='\ufeff'+[head,...rows].map(row=>row.map(x=>'"'+String(x??'').replace(/"/g,'""')+'"').join(';')).join('\r\n');const url=URL.createObjectURL(new Blob([csv],{type:'text/csv;charset=utf-8'})),a=document.createElement('a');a.href=url;a.download=name;document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);}
 function exportRecap(){exportCSV('Rekap_Publikasi_Dosen_Sains_Data.csv',['Dosen','GARUDA','SINTA','Scopus','Sitasi Google Scholar','h-index Scholar'],staff.map(p=>[p.name,N(recP(p.slug).garuda),N(sintaP(p.slug).total),scCount(p.slug)??'BELUM ADA DATA',N(gsP(p.slug).sitasi),N(gsP(p.slug).h_index)]));}
  function exportWorks(){
    const rows=filtered();
    if(data.tab==='book'){
      exportCSV('Riwayat_Buku_Sains_Data.csv',['Judul','Tahun','ISBN','Kategori','Penerbit','Penulis','Dosen','Profil SINTA'],rows.map(x=>[x.judul,x.tahun,x.isbn||'',x.jenis_buku||'',x.penerbit||'',x.penulis||'',(x.dosen||[]).map(sl=>findP(sl).name).join('; '),x.sumber_profil_sinta||'']));return;
    }
    if(data.tab==='ipr'){
      exportCSV('Riwayat_HKI_Sains_Data.csv',['Judul','Tahun','Nomor Permohonan','Nomor Pencatatan','Pencipta','Pemegang Hak','Dosen','Profil SINTA'],rows.map(x=>[x.judul,x.tahun,x.nomor_permohonan||'',x.nomor_pencatatan||'',x.penulis||'',x.pemegang_hak||'',(x.dosen||[]).map(sl=>findP(sl).name).join('; '),x.sumber_profil_sinta||'']));return;
    }
    exportCSV('Riwayat_Publikasi_Dosen_Sains_Data.csv',['Judul','Tahun','Jenis','Jurnal / Sumber','Dosen','Scopus','SINTA saat terbit','Peringkat jurnal kini','DOI','Tautan'],rows.map(x=>[x.judul,x.tahun,x.jenis,x.jurnal,x.dosen.map(sl=>findP(sl).name).join('; '),x.scopus?'Ya':'',x.sintaHistory||'',x.sintaCurrent||'',x.doi||'',x.scopusURL||x.publisherURL||(x.doi?'https://doi.org/'+doi(x.doi):'')||x.sourceURL||'']));
  }

 function render(){selectors();updateTop();renderBars();renderRanks();renderStaff();renderCitations();renderPeople();mergeRows();renderWorks();}
 for(const p of staff)E('sdp-select-person').insertAdjacentHTML('beforeend','<option value="'+esc(p.slug)+'">'+esc(p.name)+'</option>');
 E('sdp-from').addEventListener('change',()=>{renderBars();renderCitations()});E('sdp-to').addEventListener('change',()=>{renderBars();renderCitations()});E('sdp-people-search').addEventListener('input',renderPeople);
 root.querySelectorAll('.sdp-tab').forEach(b=>b.addEventListener('click',()=>setTab(b.dataset.tab)));
 E('sdp-select-person').addEventListener('change',()=>{data.visible=18;renderWorks()});E('sdp-select-year').addEventListener('change',()=>{data.visible=18;renderWorks()});E('sdp-select-query').addEventListener('input',()=>{data.visible=18;renderWorks()});
 E('sdp-more').addEventListener('click',()=>{data.visible+=18;renderWorks()});E('sdp-download-recap').addEventListener('click',exportRecap);E('sdp-export-works').addEventListener('click',exportWorks);E('sdp-print').addEventListener('click',()=>window.print());
 render();
 /* Sitasi tahunan dibaca dari satu rekap GitHub, bukan enam permintaan Apps Script. */
 // Memuat satu rekap ringkas; data dasar langsung tersedia jika jaringan lambat.
 loadJson('dashboard_ringkas_wordpress.json',12000).then(x=>{
  if(!x||!Array.isArray(x.garuda_years)||!Array.isArray(x.scholars)||!Array.isArray(x.scopus))throw Error('format');
  data.recap={rekap_prodi:{garuda_unik:x.garuda_unique},tabel_per_tahun:x.garuda_years,tabel_per_dosen:x.garuda_persons};
  data.sinta={total_sinta:x.sinta_total,peringkat:x.sinta_ranks,per_tahun:x.sinta_years,per_dosen:x.sinta_persons,artikel:[]};
  data.scopus={publikasi:x.scopus};data.scholar={dosen:x.scholars};
  data.extra_counts=Object.fromEntries((x.extra_persons||[]).map(p=>[p.slug,{buku:p.buku,ipr:p.ipr}]));
  if(/^\d{4}-\d\d-\d\d$/.test(x.updated||'')){
    const [year,month,day]=x.updated.split('-').map(Number);
    E('sdp-date').textContent=day+' '+(['','Januari','Februari','Maret','April','Mei','Juni','Juli','Agustus','September','Oktober','November','Desember'][month])+' '+year;
  }
  render();
 }).catch(()=>{ /* Data awal tetap tampil. */ });
})();
