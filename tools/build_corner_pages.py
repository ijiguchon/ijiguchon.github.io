#!/usr/bin/env python3
"""성수생각 글마다 고정 주소 페이지(/corner/YYYY-MM-DD/)와 공유 미리보기 이미지를 만든다.

드라이브 「목회칼럼」 공개 폴더를 읽어, 날짜(MMDDYY) 하나당
  corner/<YYYY-MM-DD>/index.html   — 제목·본문·그림 칼럼 링크, 페이스북·카톡용 og 태그
  images/corner/<YYYY-MM-DD>.jpg   — 1200×630 공유 이미지 (그림 칼럼 PDF 첫 장 또는 첫 사진)
를 만든다. 이미 있는 날짜는 건너뛴다(--force 로 다시 만듦).
"""
import io, json, os, re, sys, urllib.request, urllib.parse, html
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KEY = 'AIzaSyBL3EXN_i8b9RkcXPa4x_FD2M3sKTQpVgY'
FOLDER = '1gc6QSSoAxbvy_F7rHn1PmENkobJaxXOL'
SITE = 'https://www.ijiguchon.org'
FORCE = '--force' in sys.argv

def get(url, binary=False):
    with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'gmc-corner-pages/1.0'}), timeout=60) as r:
        return r.read() if binary else r.read().decode('utf-8')

def drive_list():
    q = f"'{FOLDER}' in parents and trashed=false"
    url = ('https://www.googleapis.com/drive/v3/files?q=' + urllib.parse.quote(q) + '&key=' + KEY
           + '&fields=' + urllib.parse.quote('files(id,name,mimeType)') + '&pageSize=300')
    return json.loads(get(url)).get('files', [])

def parse_name(name):
    m = re.match(r'^\s*(\d{2})(\d{2})(\d{2})[_\s.\-]*(.*)$', name or '')
    if not m: return None
    iso = f'20{m.group(3)}-{m.group(1)}-{m.group(2)}'
    title = re.sub(r'\.[a-z0-9]+$', '', m.group(4), flags=re.I).replace('_', ' ').strip()
    return iso, title

def doc_text(f):
    if f['mimeType'] == 'application/vnd.google-apps.document':
        return get(f'https://www.googleapis.com/drive/v3/files/{f["id"]}/export?mimeType=text/plain&key={KEY}')
    if f['name'].lower().endswith('.docx'):
        try:
            import docx  # python-docx
            b = get(f'https://www.googleapis.com/drive/v3/files/{f["id"]}?alt=media&key={KEY}', binary=True)
            return '\n'.join(p.text for p in docx.Document(io.BytesIO(b)).paragraphs)
        except Exception:
            return ''
    return get(f'https://www.googleapis.com/drive/v3/files/{f["id"]}?alt=media&key={KEY}')

def paras_of(text):
    out = []
    for ln in text.replace('﻿', '').replace('\r', '').split('\n'):
        s = re.sub(r'\s+', ' ', ln).strip()
        if not s: continue
        s = re.sub(r'^#{1,6}\s+', '', s); s = re.sub(r'\*\*(.+?)\*\*', r'\1', s); s = re.sub(r'^[-*]\s+', '', s)
        if re.match(r'^\[?\s*(?:사진|그림|이미지|photo|image)\s*[:：]?\s*\S+?\s*\]?$', s, re.I): continue
        out.append(s)
    return out

def og_image(iso, pdf_id, img_id):
    dst = os.path.join(ROOT, 'images', 'corner', f'{iso}.jpg')
    if os.path.exists(dst) and not FORCE: return f'/images/corner/{iso}.jpg'
    src = None
    for fid in [pdf_id, img_id]:
        if not fid: continue
        try:
            src = Image.open(io.BytesIO(get(f'https://lh3.googleusercontent.com/d/{fid}=w1600', binary=True))).convert('RGB'); break
        except Exception:
            src = None
    if src is None: return '/images/og-genesis1314.jpg'
    W, H = 1200, 630
    r = max(W / src.width, H / src.height)
    im = src.resize((round(src.width * r), round(src.height * r)), Image.LANCZOS)
    # 세로형(그림 칼럼 첫 장)은 위쪽(제목·그림)을 살린다
    canvas = im.crop((max(0, (im.width - W) // 2), 0, max(0, (im.width - W) // 2) + W, H))
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    canvas.save(dst, quality=88, optimize=True)
    return f'/images/corner/{iso}.jpg'

def fmt(iso):
    y, m, d = iso.split('-'); return f'{int(m)}.{int(d)}.{y}'

PAGE = '''<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} · 성수생각 · 시애틀지구촌교회</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{site}/corner/{iso}/">
<meta property="og:type" content="article"/>
<meta property="og:site_name" content="시애틀지구촌교회"/>
<meta property="og:title" content="{title} · 성수생각"/>
<meta property="og:description" content="{desc}"/>
<meta property="og:url" content="{site}/corner/{iso}/"/>
<meta property="og:image" content="{site}{img}"/>
<meta property="og:image:width" content="1200"/>
<meta property="og:image:height" content="630"/>
<meta property="article:published_time" content="{iso}"/>
<meta name="twitter:card" content="summary_large_image"/>
<meta name="twitter:title" content="{title} · 성수생각"/>
<meta name="twitter:description" content="{desc}"/>
<meta name="twitter:image" content="{site}{img}"/>
<link rel="icon" type="image/png" sizes="192x192" href="/images/icon-192-r.png">
<link rel="stylesheet" crossorigin href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.css">
<style>
:root{{--cream:#F6F1E7;--ink:#14213d;--ink2:#48505e;--muted:#5F6573;--line:#e3dccd;--gold:#B8924A;--gold2:#826028}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--cream);color:var(--ink);font-family:'Pretendard Variable',Pretendard,-apple-system,'Segoe UI',sans-serif;line-height:1.75;-webkit-font-smoothing:antialiased}}
.wrap{{max-width:680px;margin:0 auto;padding:0 20px 56px}}
.top{{display:flex;justify-content:space-between;align-items:center;padding:14px 0;border-bottom:1px solid var(--line);font-size:14px;font-weight:800}}
.top a{{color:inherit;text-decoration:none}}.top .pill{{font-weight:600;border:1px solid var(--line);border-radius:999px;padding:6px 12px;color:var(--ink2)}}
.eye{{margin:28px 0 6px;font-size:12px;letter-spacing:.14em;font-weight:800;color:var(--gold2)}}
h1{{font-size:28px;line-height:1.3;margin:0 0 6px;font-weight:800;word-break:keep-all}}
.date{{color:var(--muted);font-size:14px;margin-bottom:18px}}
.fig{{display:block;margin:0 0 22px;border-radius:14px;overflow:hidden;box-shadow:0 10px 24px rgba(20,33,61,.18);background:#0b1428}}
.fig img{{display:block;width:100%;height:auto}}
.fig-cap{{display:block;text-align:center;font-size:14px;font-weight:800;color:var(--gold2);padding:10px;background:#fff}}
.body p{{margin:0 0 16px;font-size:17px;word-break:keep-all}}
.sig{{color:var(--muted);font-size:14px;margin-top:8px}}
.acts{{display:flex;gap:10px;flex-wrap:wrap;margin-top:26px}}
.btn{{display:inline-flex;align-items:center;justify-content:center;min-height:48px;padding:12px 18px;border-radius:12px;font-weight:800;text-decoration:none;font-size:15px}}
.btn.g{{background:linear-gradient(135deg,#F3DA9B,#E2BB63);color:var(--ink);border:1px solid rgba(130,96,40,.35)}}
.btn.o{{border:1.5px solid var(--ink);color:var(--ink)}}
.foot{{text-align:center;color:var(--muted);font-size:12.5px;margin-top:36px}}
.share{{margin-top:18px;background:var(--card,#fff);border:1px solid var(--line);border-radius:14px;padding:14px 16px}}
.share h3{{margin:0 0 10px;font-size:13px;font-weight:800;color:var(--muted);letter-spacing:.04em}}
.share .sb{{display:grid;grid-template-columns:repeat(4,1fr);gap:8px}}
@media (max-width:420px){{.share .sb{{grid-template-columns:repeat(2,1fr)}}}}
.share button,.share a{{display:inline-flex;align-items:center;justify-content:center;gap:6px;min-height:44px;border-radius:10px;border:1px solid var(--line);background:var(--tint,#fbf7ef);color:var(--ink);font:700 13.5px inherit;font-family:inherit;text-decoration:none;cursor:pointer;padding:8px 10px}}
.share button:hover,.share a:hover{{background:#f3ecdc}}
.share .pri{{background:var(--ink);color:#fff;border-color:var(--ink)}}
.share svg{{width:18px;height:18px;flex:none}}
.share .msg{{font-size:12.5px;color:var(--muted);margin:8px 0 0;min-height:1.2em}}
</style>
</head>
<body>
<div class="wrap">
  <div class="top"><a href="/corner/">← 성수생각</a><a class="pill" href="/">교회 홈페이지</a></div>
  <div class="eye">성수생각 · 목회자 코너</div>
  <h1>{title}</h1>
  <div class="date">{date} · 김성수 목사</div>
  {figure}
  <div class="body">{body}</div>
  <div class="sig">김성수 목사 드림</div>
  <div class="acts">{pdfbtn}<a class="btn o" href="/corner/?c={iso}">성수생각에서 보기</a></div>
  <div class="share" id="share"><h3>이 페이지 보내기</h3><div class="sb">
<button type="button" class="pri" id="sh-native"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 12v7a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-7"/><path d="M12 15V3"/><path d="m7 8 5-5 5 5"/></svg>공유 · 카톡</button>
<a id="sh-fb" href="#" target="_blank" rel="noopener"><svg viewBox="0 0 24 24" fill="currentColor"><path d="M13.5 22v-8h2.7l.4-3.2h-3.1V8.8c0-.9.3-1.6 1.6-1.6h1.7V4.4c-.3 0-1.3-.1-2.5-.1-2.5 0-4.1 1.5-4.1 4.2v2.3H7.4V14h2.8v8h3.3z"/></svg>페이스북</a>
<a id="sh-th" href="#" target="_blank" rel="noopener"><svg viewBox="0 0 24 24" fill="currentColor"><path d="M12.2 2C6.9 2 3.6 5.5 3.6 11.9S6.9 22 12.2 22c3.8 0 6.3-1.8 7.4-4.3l-2.3-1.1c-.8 1.9-2.6 3-5.1 3-3.9 0-6-2.6-6-7.6s2.1-7.6 6-7.6c3.1 0 4.9 1.4 5.5 4.1-1-.5-2.2-.8-3.4-.8-2.7 0-4.6 1.5-4.6 3.7 0 2.1 1.7 3.5 4.1 3.5 2.9 0 4.6-1.8 4.8-5v-.3c1.4.9 2.1 2.2 2.1 3.9h2.4c0-3.1-1.5-5.3-4.2-6.5C18.4 4.1 15.9 2 12.2 2zm2.1 11.2c-.1 1.9-.9 2.9-2.5 2.9-1.1 0-1.8-.5-1.8-1.3 0-.9.9-1.5 2.3-1.5.7 0 1.4.1 2 .3v-.4z"/></svg>스레드</a>
<button type="button" id="sh-copy"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="11" height="11" rx="2"/><path d="M5 15V5a2 2 0 0 1 2-2h10"/></svg>링크 복사 · 인스타</button>
</div><p class="msg" id="sh-msg"></p></div>
  <p class="foot">시애틀지구촌교회 · www.ijiguchon.org</p>
</div>
<script>(function(){{
  var url=location.origin+location.pathname, title=document.title, msg=document.getElementById('sh-msg');
  function say(t){{ msg.textContent=t; }}
  document.getElementById('sh-fb').href='https://www.facebook.com/sharer/sharer.php?u='+encodeURIComponent(url);
  document.getElementById('sh-th').href='https://www.threads.net/intent/post?text='+encodeURIComponent(title+' '+url);
  document.getElementById('sh-native').addEventListener('click',async function(){{
    if(navigator.share){{ try{{ await navigator.share({{title:title,url:url}}); return; }}catch(e){{ if(e&&e.name==='AbortError') return; }} }}
    copy('이 기기에는 공유창이 없어 주소를 복사했습니다. 카톡에 붙여넣어 보내 주세요.');
  }});
  document.getElementById('sh-copy').addEventListener('click',function(){{ copy('주소를 복사했습니다. 인스타그램·카톡에 붙여넣어 보내 주세요.'); }});
  async function copy(ok){{ try{{ await navigator.clipboard.writeText(url); say(ok); }}catch(e){{ window.prompt('아래 주소를 복사해 주세요', url); }} }}
}})();</script>
</body>
</html>
'''

def main():
    files = drive_list()
    bydate = {}
    for f in files:
        if f['mimeType'] == 'application/vnd.google-apps.folder': continue
        p = parse_name(f['name']);
        if not p: continue
        iso, title = p
        d = bydate.setdefault(iso, {'title': None, 'pdf': None, 'text': None, 'imgs': []})
        n, mt = f['name'], f['mimeType']
        if re.search(r'(슬라이드|slides?|ppt)', n, re.I): continue
        if mt == 'application/vnd.google-apps.document' or re.search(r'\.(txt|md|docx)$', n, re.I) or mt in ('text/plain', 'text/markdown'):
            d['text'] = f; d['title'] = d['title'] or title
        elif mt == 'application/pdf' or n.lower().endswith('.pdf'):
            d['pdf'] = d['pdf'] or f['id']; d['title'] = d['title'] or title
        elif mt.startswith('image/'):
            d['imgs'].append(f)
    made = []
    for iso in sorted(bydate):
        d = bydate[iso]
        if not d['title']: continue
        out = os.path.join(ROOT, 'corner', iso, 'index.html')
        if os.path.exists(out) and not FORCE: continue
        paras = []
        if d['text']:
            try: paras = paras_of(doc_text(d['text']))
            except Exception as e: print('text fail', iso, e)
        if paras and (d['title'] in paras[0] or re.match(r'^\s*\d{6}', paras[0])): paras = paras[1:]   # 첫 줄이 제목이면 뺀다
        d['imgs'].sort(key=lambda f: f['name'])
        img = og_image(iso, d['pdf'], d['imgs'][0]['id'] if d['imgs'] else None)
        desc = ' '.join(paras)[:150].rstrip() + ('…' if len(' '.join(paras)) > 150 else '') if paras else f'{d["title"]} — 김성수 목사가 매주 전하는 시애틀지구촌교회 성수생각'
        figure = ''
        if d['pdf']:
            figure = f'<a class="fig" href="https://drive.google.com/file/d/{d["pdf"]}/view" target="_blank" rel="noopener"><img src="https://lh3.googleusercontent.com/d/{d["pdf"]}=w1200" alt="{html.escape(d["title"])} — 그림으로 읽는 칼럼" referrerpolicy="no-referrer"><span class="fig-cap">그림으로 읽는 칼럼 · 누르면 크게 보기</span></a>'
        elif d['imgs']:
            figure = f'<span class="fig"><img src="https://lh3.googleusercontent.com/d/{d["imgs"][0]["id"]}=w1200" alt="" referrerpolicy="no-referrer"></span>'
        body = ''.join(f'<p>{html.escape(p)}</p>' for p in paras) or '<p>본문은 성수생각 페이지에서 읽으실 수 있습니다.</p>'
        pdfbtn = f'<a class="btn g" href="https://drive.google.com/file/d/{d["pdf"]}/view" target="_blank" rel="noopener">그림으로 읽는 칼럼 →</a>' if d['pdf'] else ''
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, 'w', encoding='utf-8') as fh:
            fh.write(PAGE.format(title=html.escape(d['title']), desc=html.escape(desc), site=SITE, iso=iso, img=img, date=fmt(iso), figure=figure, body=body, pdfbtn=pdfbtn))
        made.append(iso)
    # sitemap
    sm = os.path.join(ROOT, 'sitemap.xml')
    if made and os.path.exists(sm):
        s = open(sm, encoding='utf-8').read()
        add = ''.join(f'  <url><loc>{SITE}/corner/{iso}/</loc><lastmod>{iso}</lastmod><priority>0.6</priority></url>\n' for iso in made if f'/corner/{iso}/' not in s)
        if add: open(sm, 'w', encoding='utf-8').write(s.replace('</urlset>', add + '</urlset>'))
    print('made', len(made), made[-5:])

if __name__ == '__main__':
    main()
