#!/usr/bin/env python3
"""
build_pages.py — render deep-research REPORT.md files into a clean, mobile-first
static site for GitHub Pages.

  <report>/report/REPORT.md  ->  <out>/<slug>.html   (+ index.html)

Each page: readable column, sticky collapsible Contents (parts + leaves),
in-page filter, light/dark, offline (all CSS/JS inline, no external deps).
"""
from __future__ import annotations
import os, re, html, json, datetime
import markdown

RESEARCH = "/Users/gieunkwak/Data_Analytics/SlowAI/automations/research"
OUT = os.path.join(RESEARCH, "deep-research-site")

PROJECTS = [
    ("stock-investing", "How to invest in stocks"),
    ("bioprocess-e2e", "End-to-end bioprocess manufacturing"),
    ("second-brain", "Second-brain systems"),
]

TOC_BLOCK_RE = re.compile(r"\n## Table of contents\n.*?\n---\n", re.DOTALL)
EXT_LINK_RE = re.compile(r'<a href="(https?://[^"]+)"')


def meta_of(text: str) -> dict:
    def grab(pat):
        m = re.search(pat, text, re.MULTILINE)
        return m.group(1).strip() if m else ""
    title = grab(r"^#\s+(.+?)\s*$")
    title = re.sub(r"\s*—\s*Deep Research Report\s*$", "", title)
    return {
        "title": title,
        "purpose": grab(r"\*\*Purpose:\*\*\s*(.+?)\s*(?:\n|$)"),
        "leaves": grab(r"\*\*Leaves:\*\*\s*(\d+)"),
        "asof": grab(r"\*\*As of:\*\*\s*([0-9-]+)"),
        "evidence": grab(r"\*\*Evidence:\*\*\s*(.+?)\s*(?:\n|$)"),
    }


def render_toc(tokens) -> str:
    """Nested <ul> for levels 2 (parts) and 3 (leaves) only."""
    def walk(nodes, depth):
        if not nodes:
            return ""
        lis = []
        for n in nodes:
            if n["level"] > 3:
                continue
            kids = walk(n.get("children", []), depth + 1)
            cls = "part" if n["level"] == 2 else "leaf"
            # n["name"] is already HTML-escaped by markdown; don't re-escape the label.
            label = n["name"]
            filt = html.escape(html.unescape(n["name"]).lower(), quote=True)
            lis.append(
                f'<li class="{cls}"><a href="#{n["id"]}" '
                f'data-t="{filt}">{label}</a>{kids}</li>'
            )
        return f"<ul>{''.join(lis)}</ul>" if lis else ""
    return walk(tokens, 0)


PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{title}</title>
<style>{css}</style>
</head>
<body>
<header class="topbar">
  <a class="home" href="index.html" title="All reports">&#8592;</a>
  <span class="crumb">{title}</span>
  <button id="toc-btn" aria-label="Contents">Contents</button>
  <button id="theme-btn" aria-label="Toggle theme">&#9681;</button>
</header>
<div class="layout">
  <nav id="toc" class="toc" aria-label="Table of contents">
    <input id="toc-filter" type="search" placeholder="Filter sections…" autocomplete="off">
    <div class="toc-scroll">{toc}</div>
  </nav>
  <main class="content">
    <article>{body}</article>
    <footer class="pagefoot">Generated {gen} · <a href="index.html">All reports</a></footer>
  </main>
</div>
<div id="scrim"></div>
<script>{js}</script>
</body>
</html>
"""

CSS = r"""
:root{
  --bg:#fbfbfa; --fg:#1b1b18; --muted:#6b6b63; --line:#e7e6e1;
  --accent:#3b5bdb; --card:#fff; --warn:#b5820a; --sidebar:#f4f3ef;
  --maxw:44rem;
}
:root[data-theme=dark]{
  --bg:#141414; --fg:#e6e6e1; --muted:#9a9a90; --line:#2b2b28;
  --accent:#8aa0ff; --card:#1c1c1a; --warn:#e0a83a; --sidebar:#1a1a18;
}
@media (prefers-color-scheme:dark){
  :root:not([data-theme=light]){
    --bg:#141414; --fg:#e6e6e1; --muted:#9a9a90; --line:#2b2b28;
    --accent:#8aa0ff; --card:#1c1c1a; --warn:#e0a83a; --sidebar:#1a1a18;
  }
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--fg);
  font:17px/1.7 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;}
a{color:var(--accent);text-decoration:none}
a:hover{text-decoration:underline}

.topbar{position:sticky;top:0;z-index:30;display:flex;align-items:center;gap:.6rem;
  padding:.55rem .9rem;background:color-mix(in srgb,var(--bg) 88%,transparent);
  backdrop-filter:saturate(1.2) blur(8px);border-bottom:1px solid var(--line);
  padding-top:calc(.55rem + env(safe-area-inset-top));}
.topbar .home{font-size:1.25rem;line-height:1;color:var(--fg);padding:.1rem .3rem}
.topbar .crumb{font-weight:600;font-size:.95rem;flex:1;overflow:hidden;
  text-overflow:ellipsis;white-space:nowrap}
.topbar button{background:none;border:1px solid var(--line);color:var(--fg);
  border-radius:8px;padding:.28rem .6rem;font-size:.85rem;cursor:pointer}
#toc-btn{display:none}

.layout{display:grid;grid-template-columns:19rem 1fr;gap:0;align-items:start}
.toc{position:sticky;top:3.1rem;align-self:start;height:calc(100vh - 3.1rem);
  background:var(--sidebar);border-right:1px solid var(--line);
  padding:.8rem .5rem .8rem .9rem;display:flex;flex-direction:column}
#toc-filter{width:100%;padding:.45rem .6rem;margin-bottom:.6rem;border:1px solid var(--line);
  border-radius:8px;background:var(--bg);color:var(--fg);font-size:.85rem}
.toc-scroll{overflow-y:auto;padding-right:.3rem}
.toc ul{list-style:none;margin:0;padding:0}
.toc li.part>a{display:block;font-weight:650;font-size:.86rem;margin-top:.7rem;color:var(--fg)}
.toc li.leaf>a{display:block;font-size:.82rem;color:var(--muted);padding:.12rem 0 .12rem .7rem;
  border-left:2px solid transparent}
.toc li.leaf>a:hover{color:var(--fg)}
.toc a.active{color:var(--accent)!important;border-left-color:var(--accent)!important}
.toc li.hide{display:none}

.content{min-width:0;padding:1.2rem 1.4rem 4rem}
article{max-width:var(--maxw);margin:0 auto}
article h1{font-size:1.9rem;line-height:1.25;margin:.4rem 0 1rem}
article h2{font-size:1.4rem;margin:2.4rem 0 .6rem;padding-top:.5rem;border-top:1px solid var(--line)}
article h3{font-size:1.15rem;margin:1.8rem 0 .5rem}
article h4{font-size:1rem;margin:1.3rem 0 .4rem;color:var(--muted);
  text-transform:uppercase;letter-spacing:.04em}
article p{margin:.7rem 0}
article blockquote{margin:1rem 0;padding:.6rem 1rem;background:var(--card);
  border:1px solid var(--line);border-left:3px solid var(--accent);border-radius:8px;
  font-size:.94rem;color:var(--muted)}
article blockquote strong{color:var(--fg)}
article table{border-collapse:collapse;width:100%;display:block;overflow-x:auto;font-size:.9rem}
article th,article td{border:1px solid var(--line);padding:.4rem .6rem;text-align:left}
article code{background:var(--card);border:1px solid var(--line);border-radius:5px;
  padding:.05rem .35rem;font-size:.88em}
article pre{background:var(--card);border:1px solid var(--line);border-radius:10px;
  padding:.9rem 1rem;overflow-x:auto}
article pre code{border:0;padding:0}
article img{max-width:100%;height:auto;border-radius:8px}
article ul,article ol{padding-left:1.3rem}
article hr{border:0;border-top:1px solid var(--line);margin:2rem 0}
:target{scroll-margin-top:4rem}
.pagefoot{margin:3rem auto 0;max-width:var(--maxw);color:var(--muted);
  font-size:.82rem;border-top:1px solid var(--line);padding-top:1rem}

#scrim{display:none;position:fixed;inset:0;background:rgba(0,0,0,.4);z-index:20}

@media (max-width:820px){
  .layout{display:block}
  #toc-btn{display:inline-block}
  .toc{position:fixed;top:0;left:0;z-index:25;width:80%;max-width:20rem;height:100vh;
    transform:translateX(-100%);transition:transform .22s ease;
    padding-top:calc(.8rem + env(safe-area-inset-top));box-shadow:2px 0 18px rgba(0,0,0,.15)}
  .toc.open{transform:none}
  #scrim.open{display:block}
  .content{padding:1rem 1.05rem 4rem}
  article h1{font-size:1.6rem}
  body{font-size:16px}
}
"""

JS = r"""
(function(){
  var root=document.documentElement;
  var tbtn=document.getElementById('theme-btn');
  var stored=null; try{stored=localStorage.getItem('theme')}catch(e){}
  if(stored)root.setAttribute('data-theme',stored);
  tbtn.addEventListener('click',function(){
    var cur=root.getAttribute('data-theme');
    var next = cur==='dark' ? 'light' : (cur==='light' ? 'dark' :
      (matchMedia('(prefers-color-scheme:dark)').matches?'light':'dark'));
    root.setAttribute('data-theme',next);
    try{localStorage.setItem('theme',next)}catch(e){}
  });

  var toc=document.getElementById('toc'), scrim=document.getElementById('scrim'),
      obtn=document.getElementById('toc-btn');
  function close(){toc.classList.remove('open');scrim.classList.remove('open')}
  if(obtn)obtn.addEventListener('click',function(){toc.classList.toggle('open');scrim.classList.toggle('open')});
  scrim.addEventListener('click',close);
  toc.addEventListener('click',function(e){if(e.target.tagName==='A')close()});

  var flt=document.getElementById('toc-filter');
  flt.addEventListener('input',function(){
    var q=flt.value.trim().toLowerCase();
    toc.querySelectorAll('a[data-t]').forEach(function(a){
      var li=a.closest('li');
      var hit=!q||a.getAttribute('data-t').indexOf(q)>-1;
      if(li.classList.contains('part')){
        var anyKid=[].some.call(li.querySelectorAll('li.leaf a'),function(k){
          return !q||k.getAttribute('data-t').indexOf(q)>-1;});
        li.classList.toggle('hide',!(hit||anyKid));
      }else{li.classList.toggle('hide',!hit);}
    });
  });

  // scroll-spy
  var links={}, ids=[];
  toc.querySelectorAll('a[href^="#"]').forEach(function(a){
    var id=a.getAttribute('href').slice(1);links[id]=a;ids.push(id);});
  var spy=new IntersectionObserver(function(es){
    es.forEach(function(en){
      if(en.isIntersecting){
        for(var k in links)links[k].classList.remove('active');
        var a=links[en.target.id];
        if(a){a.classList.add('active');
          a.scrollIntoView({block:'nearest'});}
      }
    });
  },{rootMargin:'-10% 0px -80% 0px'});
  ids.forEach(function(id){var el=document.getElementById(id);if(el)spy.observe(el);});
})();
"""

INDEX_CSS = r"""
:root{--bg:#fbfbfa;--fg:#1b1b18;--muted:#6b6b63;--line:#e7e6e1;--accent:#3b5bdb;--card:#fff}
@media(prefers-color-scheme:dark){:root{--bg:#141414;--fg:#e6e6e1;--muted:#9a9a90;--line:#2b2b28;--accent:#8aa0ff;--card:#1c1c1a}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);
  font:17px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  padding:calc(2.4rem + env(safe-area-inset-top)) 1.2rem 4rem}
.wrap{max-width:42rem;margin:0 auto}
h1{font-size:1.7rem;margin:0 0 .2rem}
.sub{color:var(--muted);margin:0 0 2rem}
a.card{display:block;text-decoration:none;color:inherit;background:var(--card);
  border:1px solid var(--line);border-radius:14px;padding:1.1rem 1.2rem;margin:.9rem 0;
  transition:border-color .15s,transform .05s}
a.card:hover{border-color:var(--accent)}
a.card:active{transform:scale(.995)}
.card h2{font-size:1.2rem;margin:0 0 .35rem;color:var(--accent)}
.card .p{color:var(--fg);font-size:.95rem;margin:0 0 .7rem}
.card .m{color:var(--muted);font-size:.8rem;display:flex;flex-wrap:wrap;gap:.3rem 1rem}
footer{color:var(--muted);font-size:.8rem;margin-top:2rem;text-align:center}
"""


def build():
    os.makedirs(OUT, exist_ok=True)
    gen = datetime.datetime.fromtimestamp(os.path.getmtime(__file__)).strftime("%Y-%m-%d")
    cards = []
    for slug, short in PROJECTS:
        src = os.path.join(RESEARCH, slug, "report", "REPORT.md")
        if not os.path.exists(src):
            print("  skip (missing):", slug); continue
        with open(src, encoding="utf-8") as f:
            text = f.read()
        meta = meta_of(text)
        text = TOC_BLOCK_RE.sub("\n", text, count=1)  # drop inline TOC; sidebar replaces it
        md = markdown.Markdown(extensions=[
            "extra", "toc", "sane_lists", "attr_list", "smarty"],
            extension_configs={"toc": {"toc_depth": "2-4"}})
        body = md.convert(text)
        body = EXT_LINK_RE.sub(r'<a target="_blank" rel="noopener" href="\1"', body)
        toc = render_toc(md.toc_tokens)
        page = PAGE.format(title=html.escape(meta["title"]), css=CSS, js=JS,
                           toc=toc, body=body, gen=gen)
        with open(os.path.join(OUT, slug + ".html"), "w", encoding="utf-8") as f:
            f.write(page)
        m = []
        if meta["leaves"]: m.append(f'{meta["leaves"]} sections')
        if meta["evidence"]:
            ev = re.search(r"([\d,]+)\s+claims", meta["evidence"])
            src_ = re.search(r"([\d,]+)\s+unique sources", meta["evidence"])
            if ev: m.append(f'{ev.group(1)} claims')
            if src_: m.append(f'{src_.group(1)} sources')
        if meta["asof"]: m.append(f'as of {meta["asof"]}')
        cards.append(
            f'<a class="card" href="{slug}.html"><h2>{html.escape(meta["title"])}</h2>'
            f'<p class="p">{html.escape(meta["purpose"])}</p>'
            f'<div class="m">{"".join(f"<span>{x}</span>" for x in m)}</div></a>')
        print("  built:", slug + ".html", f'({len(body)//1024} KB)')

    index = (f'<!doctype html><html lang="en"><head><meta charset="utf-8">'
             f'<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
             f'<title>Deep Research</title><style>{INDEX_CSS}</style></head><body><div class="wrap">'
             f'<h1>Deep Research</h1><p class="sub">Comprehensive methodology maps · read anywhere</p>'
             f'{"".join(cards)}'
             f'<footer>Generated {gen}</footer></div></body></html>')
    with open(os.path.join(OUT, "index.html"), "w", encoding="utf-8") as f:
        f.write(index)
    print("  built: index.html")
    print("OUT:", OUT)


if __name__ == "__main__":
    build()
