# -*- coding: utf-8 -*-
"""교회 사이트 RSS(새 글 목록) feed.xml 만들기 (2026-11-08 목사님 「좋아. 올리자.」, 웹 노출 정본 3절 네이버).
목회자 코너의 날짜 쪽(/corner/YYYY-MM-DD/)에서 제목 · 설명 · 주소를 읽어 최근순으로 적는다. 글을 지어 넣지 않는다.

사용: python rss_build.py <배포 저장소를 클론한 폴더>   → 그 폴더의 feed.xml을 새로 쓴다
      칼럼을 올릴 때마다 커밋 직전에 돌린다 (CLAUDE.md 5. 빌드 · 배포)
"""
import datetime, html, io, os, re, sys
from xml.sax.saxutils import escape

SITE = "https://www.ijiguchon.org"
ROOT = sys.argv[1]
TAIL = " · 성수생각 · 시애틀지구촌교회"
LIMIT = 30


def meta(s, pat):
    m = re.search(pat, s, re.S)
    return html.unescape(m.group(1)).strip() if m else ""


items = []
base = os.path.join(ROOT, "corner")
for d in sorted(os.listdir(base), reverse=True):
    f = os.path.join(base, d, "index.html")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", d) or not os.path.exists(f):
        continue
    s = io.open(f, encoding="utf-8").read()
    title = meta(s, r"<title>(.*?)</title>")
    title = title[:-len(TAIL)] if title.endswith(TAIL) else title
    desc = meta(s, r'name="description" content="([^"]*)"')
    if not title:
        sys.exit(f"제목을 읽지 못함: {f}")
    y, m, dd = map(int, d.split("-"))
    when = datetime.datetime(y, m, dd, 9, 0, tzinfo=datetime.timezone(datetime.timedelta(hours=-8)))
    url = f"{SITE}/corner/{d}/"
    items.append(f"""    <item>
      <title>{escape(title)}</title>
      <link>{url}</link>
      <guid isPermaLink="true">{url}</guid>
      <pubDate>{when.strftime('%a, %d %b %Y %H:%M:%S %z')}</pubDate>
      <dc:creator>김성수 목사</dc:creator>
      <description>{escape(desc)}</description>
    </item>""")
if not items:
    sys.exit("칼럼을 찾지 못함")
items = items[:LIMIT]
now = datetime.datetime.now(datetime.timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")
xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom" xmlns:dc="http://purl.org/dc/elements/1.1/">
  <channel>
    <title>시애틀지구촌교회 · 목회자 코너</title>
    <link>{SITE}/corner/</link>
    <atom:link href="{SITE}/feed.xml" rel="self" type="application/rss+xml"/>
    <description>시애틀지구촌교회 김성수 목사의 목회 칼럼 「성수생각」</description>
    <language>ko</language>
    <lastBuildDate>{now}</lastBuildDate>
{chr(10).join(items)}
  </channel>
</rss>
"""
io.open(os.path.join(ROOT, "feed.xml"), "w", encoding="utf-8", newline="\n").write(xml)
print(f"feed.xml {len(items)}편")
