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
  <p class="foot">시애틀지구촌교회 · www.ijiguchon.org</p>
</div>
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
