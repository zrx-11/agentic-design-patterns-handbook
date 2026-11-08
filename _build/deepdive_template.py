#!/usr/bin/env python3
"""从零推导页的模板引擎：把章节内容装进单文件 HTML。
要求（来自 skill）：
- 每 section 自带 .breadcrumb 与 .chapter-nav，用 section.querySelector 填充
- 章节 id / data-target / 顺序数组三处一致
- KaTeX CSS+JS+auto-render 内联，字体 base64 内联
- 移动端 375px 优先，顶栏常驻
"""
import base64, json, os, re

KATEX_DIR = '/tmp/katex'


def inline_katex():
    css = open(os.path.join(KATEX_DIR, 'katex.min.css'), encoding='utf-8').read()
    # 只保留 woff2，其它格式来源删掉；url 替换成 base64
    def repl(m):
        q, name = m.group(1), m.group(2)
        if not name.endswith('.woff2'):
            return 'url()'
        p = os.path.join(KATEX_DIR, 'fonts', name)
        b = base64.b64encode(open(p, 'rb').read()).decode()
        return f'url(data:font/woff2;base64,{b}) format("woff2")'
    css = re.sub(r'url\((["\']?)fonts/([^)"\']+)\1\)( format\("woff2"\))?', repl, css)
    # 清掉空 url() 与其后的 format
    css = re.sub(r'url\(\) format\("[^"]*"\)', 'url()', css)
    css = css.replace('url(),', 'url(),')
    js = open(os.path.join(KATEX_DIR, 'katex.min.js'), encoding='utf-8').read()
    ar = open(os.path.join(KATEX_DIR, 'auto-render.min.js'), encoding='utf-8').read()
    return css, js, ar


CSS = """
:root{--bg:#fbfbf9;--fg:#1c1c1a;--muted:#6b6b66;--line:#e2e0da;--card:#fff;--accent:#0f6b5c;--accent2:#b45309;--code:#f2f1ec;--intuition:#eef7f1;--warn:#fdf3e3;}
@media (prefers-color-scheme: dark){:root{--bg:#16171a;--fg:#e9e8e4;--muted:#a0a09a;--line:#2b2d31;--card:#1d1f23;--accent:#5fd3b6;--accent2:#f0a86a;--code:#24262b;--intuition:#1b2a24;--warn:#2a2318;}}
*{box-sizing:border-box;}
html{-webkit-text-size-adjust:100%;}
body{margin:0;background:var(--bg);color:var(--fg);font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Noto Sans SC","Segoe UI",sans-serif;font-size:15px;line-height:1.75;overflow-wrap:break-word;}
a{color:var(--accent);}
code{background:var(--code);padding:1px 5px;border-radius:4px;font-family:ui-monospace,Menlo,Consolas,monospace;font-size:13px;}
pre{background:var(--code);padding:12px;border-radius:8px;overflow-x:auto;font-size:13px;line-height:1.55;}
pre code{background:none;padding:0;}
.topbar{position:fixed;top:0;left:0;right:0;height:52px;background:var(--card);border-bottom:1px solid var(--line);display:flex;align-items:center;gap:8px;padding:0 10px;z-index:50;}
.topbar button{background:none;border:1px solid var(--line);border-radius:8px;min-width:44px;min-height:38px;color:var(--fg);font-size:15px;}
.topbar .title{flex:1;font-size:14px;color:var(--muted);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
main{padding:64px 14px 40px;max-width:820px;margin:0 auto;width:100%;min-width:0;overflow-x:hidden;}
.wrap{display:block;}
.sidebar{display:none;}
section{display:none;}
section.active{display:block;}
h1{font-size:20px;line-height:1.4;margin:6px 0 10px;}
h2{font-size:17px;margin:22px 0 8px;border-left:3px solid var(--accent);padding-left:9px;}
h3{font-size:15px;margin:16px 0 6px;color:var(--accent2);}
p{margin:8px 0;}
.breadcrumb{font-size:12px;color:var(--muted);margin:2px 0 12px;}
.breadcrumb span{color:var(--accent);}
.kv{display:flex;flex-wrap:wrap;gap:6px;font-size:12px;color:var(--muted);margin:6px 0 14px;}
.kv b{color:var(--fg);font-weight:600;}
.box{border:1px solid var(--line);background:var(--card);border-radius:10px;padding:12px 14px;margin:12px 0;}
.intuition{background:var(--intuition);border-left:3px solid var(--accent);border-radius:8px;padding:10px 13px;margin:12px 0;}
.intuition .tag{font-size:12px;color:var(--accent);font-weight:600;display:block;margin-bottom:4px;}
.warn{background:var(--warn);border-left:3px solid var(--accent2);border-radius:8px;padding:10px 13px;margin:12px 0;}
.warn .tag{font-size:12px;color:var(--accent2);font-weight:600;display:block;margin-bottom:4px;}
.def{border:1px dashed var(--line);border-radius:8px;padding:10px 13px;margin:12px 0;}
.def .tag{font-size:12px;color:var(--muted);letter-spacing:.04em;display:block;margin-bottom:4px;}
table{width:100%;border-collapse:collapse;margin:12px 0;font-size:13px;display:block;overflow-x:auto;}
table th,table td{border:1px solid var(--line);padding:6px 8px;text-align:left;vertical-align:top;}
table th{background:var(--code);font-weight:600;white-space:nowrap;}
details{border:1px solid var(--line);border-radius:8px;padding:8px 12px;margin:10px 0;background:var(--card);}
details summary{cursor:pointer;font-size:14px;color:var(--accent);min-height:32px;display:flex;align-items:center;}
details[open] summary{margin-bottom:8px;border-bottom:1px solid var(--line);padding-bottom:6px;}
details details{margin:8px 0;}
.chapter-nav{display:flex;justify-content:space-between;gap:10px;margin-top:26px;padding-top:14px;border-top:1px solid var(--line);}
.chapter-nav button{flex:1;min-height:44px;border:1px solid var(--line);background:var(--card);color:var(--fg);border-radius:9px;font-size:13px;padding:8px;}
.chapter-nav button:disabled{opacity:.4;}
.tree{display:flex;flex-direction:column;gap:8px;}
.tree .node{border:1px solid var(--line);border-radius:8px;padding:9px 12px;background:var(--card);cursor:pointer;font-size:13.5px;}
.tree .node b{color:var(--accent);}
.tree .lvl1{margin-left:0;}
.tree .lvl2{margin-left:18px;}
.tree .lvl3{margin-left:36px;font-size:12.5px;color:var(--muted);}
.tree .node:hover{border-color:var(--accent);}
.katex-display{overflow-x:auto;overflow-y:hidden;padding:4px 0;}
.q{border-left:3px solid var(--accent2);padding-left:10px;margin:14px 0;}
.q .ans{font-size:13px;color:var(--muted);}
#toTop{position:fixed;right:14px;bottom:16px;width:44px;height:44px;border-radius:50%;border:1px solid var(--line);background:var(--card);color:var(--fg);font-size:16px;display:none;z-index:40;}
.drawer{position:fixed;inset:0;background:rgba(0,0,0,.35);display:none;z-index:60;}
.drawer.open{display:block;}
.drawer .panel{background:var(--card);width:78%;max-width:340px;height:100%;overflow-y:auto;padding:14px 12px;}
.drawer .panel h4{font-size:12px;color:var(--muted);margin:10px 0 6px;letter-spacing:.06em;}
.drawer .panel a{display:block;padding:9px 8px;border-radius:7px;text-decoration:none;color:var(--fg);font-size:14px;min-height:40px;}
.drawer .panel a.on{background:var(--code);color:var(--accent);font-weight:600;}
@media (min-width:768px){
 body{font-size:15.5px;}
 .wrap{display:flex;gap:24px;align-items:flex-start;}
 .topbar{display:none;}
 .sidebar{display:block;position:sticky;top:0;height:100vh;overflow-y:auto;width:240px;flex:0 0 240px;padding:22px 14px;border-right:1px solid var(--line);}
 .sidebar h1{font-size:15px;}
 .sidebar a{display:block;padding:8px;font-size:13.5px;text-decoration:none;color:var(--fg);border-radius:6px;}
 .sidebar a.on{background:var(--code);color:var(--accent);font-weight:600;}
 main{padding:26px 26px 60px;margin:0;max-width:820px;}
 h1{font-size:26px;}
 h2{font-size:20px;}
}
"""

JS_TMPL = """
var ORDER=__ORDER__;
var TITLES=__TITLES__;
var cur=ORDER[0];
function $(s,r){return (r||document).querySelector(s);}
function $$(s,r){return Array.prototype.slice.call((r||document).querySelectorAll(s));}
function show(id){
  if(ORDER.indexOf(id)<0) id=ORDER[0];
  cur=id;
  $$('section').forEach(function(s){s.classList.toggle('active',s.id===id);});
  $$('.drawer .panel a').forEach(function(a){a.classList.toggle('on',a.getAttribute('data-target')===id);});
  $$('.sidebar a').forEach(function(a){a.classList.toggle('on',a.getAttribute('data-target')===id);});
  var t=$('#topTitle'); if(t) t.textContent=TITLES[id]||'';
  var el=document.getElementById(id);
  if(el){ fillNav(el); renderIn(el); }
  window.scrollTo(0,0);
  if(location.hash!=='#'+id) history.replaceState(null,'','#'+id);
}
function fillNav(sec){
  var i=ORDER.indexOf(sec.id);
  var bc=sec.querySelector('.breadcrumb');
  if(bc && !bc.dataset.filled){
    bc.innerHTML='<span>'+ (TITLES[ORDER[0]]) +'</span> / '+(i+1)+' / '+ORDER.length+' · '+(TITLES[sec.id]||'');
    bc.dataset.filled='1';
  }
  var nav=sec.querySelector('.chapter-nav');
  if(nav && !nav.dataset.filled){
    var prev=ORDER[i-1], next=ORDER[i+1];
    var b1=document.createElement('button');
    b1.textContent=prev?('← '+TITLES[prev]):'已是第一章';
    b1.disabled=!prev; b1.onclick=function(){ if(prev) show(prev); };
    var b2=document.createElement('button');
    b2.textContent=next?('下一章 '+TITLES[next]+' →'):'已是最后一章';
    b2.disabled=!next; b2.onclick=function(){ if(next) show(next); };
    nav.appendChild(b1); nav.appendChild(b2);
    nav.dataset.filled='1';
  }
}
function renderIn(sec){
  if(typeof renderMathInElement!=='function'){ setTimeout(function(){renderIn(sec);},150); return; }
  try{ renderMathInElement(sec,{delimiters:[{left:'$$',right:'$$',display:true},{left:'$',right:'$',display:false}],throwOnError:false,ignoredTags:['script','noscript','style','textarea','pre','code']}); }catch(e){ console.warn('katex',e); }
}
document.addEventListener('click',function(e){
  var a=e.target.closest('[data-target]');
  if(a){ e.preventDefault(); closeDrawer(); show(a.getAttribute('data-target')); }
});
function openDrawer(){ document.getElementById('drawer').classList.add('open'); }
function closeDrawer(){ document.getElementById('drawer').classList.remove('open'); }
document.addEventListener('scroll',function(){
  var b=document.getElementById('toTop');
  if(b) b.style.display=(window.scrollY>600)?'block':'none';
});
"""


def build(title, subtitle, sections, out_path, home_html):
    order = [x['id'] for x in sections]
    titles = {x['id']: x['nav'] for x in sections}
    css, kjs, arjs = inline_katex()
    js = JS_TMPL.replace('__ORDER__', json.dumps(order, ensure_ascii=False)).replace('__TITLES__', json.dumps(titles, ensure_ascii=False))
    nav_links = "\n".join('<a href="#%s" data-target="%s">%s</a>' % (x['id'], x['id'], x['nav']) for x in sections)
    sec_html = []
    for i, x in enumerate(sections):
        cls = ' active' if i == 0 else ''
        sec_html.append('<section id="%s" class="%s"><div class="breadcrumb"></div>%s<div class="chapter-nav"></div></section>'
                        % (x['id'], cls.strip(), x['html']))

    head = (
        '<!DOCTYPE html>\n<html lang="zh-CN">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        '<title>' + title + '</title>\n<style>' + css + '</style>\n<style>' + CSS + '</style>\n</head>\n<body>\n'
        '<div class="topbar"><button onclick="openDrawer()" aria-label="目录">☰</button>'
        '<div class="title" id="topTitle">' + sections[0]['nav'] + '</div></div>\n'
        '<div class="drawer" id="drawer" onclick="if(event.target===this)closeDrawer()"><div class="panel">'
        '<h4>' + subtitle + '</h4><a href="' + home_html + '" style="color:var(--accent)">← 回到学习手册</a>'
        + nav_links + '</div></div>\n'
        '<div class="wrap"><nav class="sidebar"><h1>' + subtitle + '</h1>'
        '<div style="font-size:12px;color:var(--muted);margin-bottom:10px">' + title + '</div>'
        '<a href="' + home_html + '" style="color:var(--accent)">← 回到学习手册</a>' + nav_links + '</nav>\n'
        '<main>' + ''.join(sec_html) + '</main></div>\n'
        '<button id="toTop" onclick="toTop()" aria-label="回到顶部">↑</button>\n'
    )
    tail = ('<script>' + kjs + '</script>\n<script>' + arjs + '</script>\n<script>' + js + '</script>\n'
            '<script>function toTop(){window.scrollTo(0,0);}\n'
            "window.addEventListener('load',function(){"
            "var h=location.hash.slice(1);var id=ORDER.indexOf(h)>=0?h:ORDER[0];"
            "ORDER.forEach(function(x){var s=document.getElementById(x);fillNav(s);renderIn(s);});"
            "show(id);});"
            '</script>\n</body>\n</html>')
    html = head + tail
    open(out_path, 'w', encoding='utf-8').write(html)
    return len(html)
