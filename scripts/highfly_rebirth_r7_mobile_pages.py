#!/usr/bin/env python3
"""R7 REBIRTH Pages: repair public GLB/textures paths, S23 entry + Spanish creator.
No native combat, classes, Training or saved-character files are modified.
"""
from pathlib import Path
import json
import re
import sys

mode, location = sys.argv[1], Path(sys.argv[2])
ROOT = "/HIGHFLY-REBIRTH"
DIRS = ("models","textures","env","vfx","ui","audio","basis","fonts",
        "claudium","guide-stills","highfly","map_art","map_bg")
ALT = "|".join(map(re.escape, DIRS))
# Match URLs written as quoted literals or CSS URL, including built JS chunks.
QUOTED = re.compile(r"""(?P<prefix>["'\x60])/(?P<dir>""" + ALT + r""")/""")
CSSURL = re.compile(r"""(?P<prefix>url\(\s*["']?)/(?P<dir>""" + ALT + r""")/""")
def rewrite(s):
    for pattern in (QUOTED, CSSURL):
        s = pattern.sub(lambda m: m.group("prefix") + ROOT + "/" + m.group("dir") + "/", s)
    return s
def rewrite_tree(root, extensions):
    count=0
    for p in root.rglob("*"):
        if p.is_file() and p.suffix.lower() in extensions:
            try: old=p.read_text(encoding="utf-8")
            except (UnicodeError, OSError): continue
            new=rewrite(old)
            if new != old:
                p.write_text(new, encoding="utf-8"); count+=1
    return count

INTRO_STYLE = r"""
html.hf-r7 #hf-r7-gate{
 position:fixed;inset:0;z-index:2147483600;display:flex;align-items:center;
 justify-content:center;box-sizing:border-box;padding:18px;color:#f8f1d7;
 background:radial-gradient(circle at 50% 42%,#193c4a 0%,#0c1e29 47%,#070e17 100%);
 font-family:system-ui,Arial,sans-serif;text-align:center
}
html.hf-r7 #hf-r7-gate[hidden]{display:none!important}
html.hf-r7 .hf-r7-card{border:1px solid #b28c45;border-radius:16px;padding:18px 24px;
 max-width:min(96vw,520px);box-shadow:0 14px 48px #000b;background:#101b2ecf}
html.hf-r7 .hf-r7-logo{font-size:clamp(22px,4.5vw,38px);font-weight:900;
 letter-spacing:.13em;color:#e9c474;text-shadow:0 3px 14px #000}
html.hf-r7 .hf-r7-caption{margin:7px 0 14px;font-size:clamp(11px,2vw,14px);color:#c7d8e2}
html.hf-r7 #hf-r7-enter{border:1px solid #e4c57a;border-radius:9px;padding:12px 28px;
 font-size:clamp(14px,2.5vw,18px);color:#1c1b16;font-weight:800;background:#ebcc7a;
 min-height:44px;cursor:pointer}
html.hf-r7 #start-screen .homepage-header, html.hf-r7 #start-screen .homepage-footer {
 display:none!important
}
html.hf-r7 #offline-select .char-input-group input{
 transform:none!important;direction:ltr!important;writing-mode:horizontal-tb!important;
 unicode-bidi:normal!important;letter-spacing:normal!important;text-align:left!important;
}
@media (orientation:landscape) and (max-height:540px){
 html.hf-r7 #offline-select.cs-wow{
   position:fixed!important;top:0!important;left:0!important;inset:0!important;
   display:block!important;visibility:visible!important;width:100vw!important;
   max-width:none!important;height:100dvh!important;min-height:0!important;
   margin:0!important;padding:6px 12px!important;box-sizing:border-box!important;
   overflow-y:auto!important;overflow-x:hidden!important;background:#101725fa!important;
   z-index:500!important;border:0!important;border-radius:0!important;
   transform:none!important;
 }
 html.hf-r7 #offline-select.cs-wow[hidden]{display:none!important}
 html.hf-r7 #offline-select .auth-title{
   position:static!important;transform:none!important;text-align:center!important;
   margin:0 0 4px!important;font-size:clamp(14px,3.5vh,20px)!important;line-height:1.1!important;
 }
 html.hf-r7 #offline-select .charselect-layout{
   position:relative!important;display:grid!important;
   grid-template-columns:minmax(0,1fr) minmax(0,1.02fr)!important;
   grid-template-rows:minmax(0,1fr)!important;gap:9px!important;
   width:100%!important;height:calc(100% - 27px)!important;max-height:none!important;
   margin:0!important;padding:0!important;transform:none!important;
 }
 html.hf-r7 #offline-select .charselect-col-left,
 html.hf-r7 #offline-select .charselect-col-right{
   display:flex!important;flex-direction:column!important;position:relative!important;
   width:auto!important;height:100%!important;max-width:none!important;
   min-width:0!important;min-height:0!important;margin:0!important;transform:none!important;
   overflow-y:auto!important;gap:4px!important;
 }
 html.hf-r7 #offline-select .char-create{display:flex!important;flex-direction:column!important;
   position:static!important;gap:4px!important;height:auto!important;transform:none!important;}
 html.hf-r7 #offline-select .auth-label{position:static!important;transform:none!important;
   margin:0!important;font-size:10px!important}
 html.hf-r7 #offline-select .char-input-group{position:static!important;transform:none!important;
   width:100%!important;max-width:none!important;margin:0!important}
 html.hf-r7 #offline-select #char-name{height:30px!important;min-height:30px!important;width:100%!important;
   font-size:14px!important;box-sizing:border-box!important;padding:4px 9px!important}
 html.hf-r7 #offline-select .mini-class-row{
   position:static!important;transform:none!important;display:grid!important;
   grid-template-columns:repeat(3,minmax(0,1fr))!important;gap:3px!important;
   width:100%!important;max-width:100%!important;margin:0!important}
 html.hf-r7 #offline-select .mini-class{
   display:flex!important;flex-direction:row!important;align-items:center!important;
   justify-content:center!important;width:auto!important;height:27px!important;
   min-height:27px!important;padding:1px 3px!important;gap:3px!important;
   border:1px solid #685737!important;border-radius:5px!important;background:#232638!important;
   font-size:10px!important;white-space:nowrap!important;box-shadow:none!important}
 html.hf-r7 #offline-select .mini-class .mini-class-portrait{
   display:none!important}
 html.hf-r7 #offline-select .skin-row{position:static!important;transform:none!important;
   display:flex!important;flex-direction:row!important;flex-wrap:wrap!important;
   gap:3px!important;width:100%!important;margin:0!important}
 html.hf-r7 #offline-select .auth-actions{position:sticky!important;bottom:0!important;
   display:flex!important;flex-direction:row!important;gap:5px!important;
   justify-content:flex-start!important;background:#101725ee!important;margin:2px 0!important;
   padding:3px 0!important;z-index:20!important}
 html.hf-r7 #offline-select .auth-actions .btn{
   position:static!important;transform:none!important;padding:5px 7px!important;
   min-height:29px!important;font-size:10px!important}
 html.hf-r7 #offline-select #offline-preview-container{
   position:relative!important;inset:auto!important;display:block!important;
   width:100%!important;min-height:130px!important;height:52%!important;max-height:52%!important;
   flex:1 0 130px!important;z-index:1!important;background:#0d1523!important;
   border:1px solid #5f553f!important;transform:none!important;
 }
 html.hf-r7 #offline-select #offline-class-details{
   position:relative!important;top:auto!important;right:auto!important;bottom:auto!important;
   flex:0 1 43%!important;min-height:50px!important;height:auto!important;max-height:43%!important;
   width:100%!important;box-sizing:border-box!important;overflow:auto!important;
   z-index:2!important;padding:4px 7px!important;font-size:10px!important;
   background:#101a2bdc!important;transform:none!important;
 }
}
"""
INTRO_MARKUP = r"""
<div id="hf-r7-gate" hidden role="dialog" aria-modal="true" aria-label="Entrar a HIGHFLY REBIRTH">
  <div class="hf-r7-card">
    <div class="hf-r7-logo">HIGHFLY REBIRTH</div>
    <div class="hf-r7-caption">Mundo isekai · GOLDEN 360° · 9 clases originales · HP / MP / EN</div>
    <button id="hf-r7-enter" type="button">ENTRAR AL MUNDO</button>
    <div class="hf-r7-caption">Elegí clase y apariencia. Se solicitará pantalla completa.</div>
  </div>
</div>
<script>
(function(){
  if (new URLSearchParams(location.search).get('hfRebirth')!=='1') return;
  document.documentElement.classList.add('hf-r7');
  var gate=document.getElementById('hf-r7-gate'),enter=document.getElementById('hf-r7-enter');
  gate.hidden=false;
  enter.addEventListener('click',function(){
    // Fullscreen must be initiated by the user's real tap, not a timer.
    try{
      var el=document.documentElement, fn=el.requestFullscreen||el.webkitRequestFullscreen;
      if(fn && !document.fullscreenElement){
        var result=fn.call(el);
        if(result && typeof result.then==='function')result.then(function(){
          try{screen.orientation.lock('landscape').catch(function(){})}catch(e){}
        }).catch(function(){});
      }
    }catch(e){}
    var nativeOffline=document.getElementById('btn-offline');
    if(nativeOffline)nativeOffline.click();
    gate.hidden=true;
    gate.remove();
  });
})();
</script>
"""
EARLY_HEAD = r"""
<script>
(function(){
  if(new URLSearchParams(location.search).get('hfRebirth')!=='1')return;
  // The native i18n module reads URL lang at import time. No origin-wide storage mutation.
  var u=new URL(location.href);
  if(!u.searchParams.has('lang')){u.searchParams.set('lang','es');history.replaceState(history.state,'',u)}
  document.documentElement.classList.add('hf-r7');
  // Repair dynamically assembled 3D-model requests (Three FileLoader uses fetch).
  var path=/^\/(models|textures|env|vfx|ui|audio|basis|fonts|claudium|guide-stills|highfly|map_art|map_bg)\//;
  function correct(v){
    if(v instanceof URL)v=v.href;
    if(typeof v!=='string')return v;
    if(path.test(v))return '/HIGHFLY-REBIRTH'+v;
    try{var u=new URL(v,location.href);
      if(u.origin===location.origin&&path.test(u.pathname)){
        u.pathname='/HIGHFLY-REBIRTH'+u.pathname;return u.href
      }
    }catch(e){}
    return v
  }
  var nativeFetch=window.fetch;
  if(nativeFetch)window.fetch=function(input,opts){
    if(typeof input==='string'||input instanceof URL)return nativeFetch.call(window,correct(input),opts);
    if(input instanceof Request){
      var url=correct(input.url);
      if(url!==input.url)return nativeFetch.call(window,new Request(url,input),opts)
    }
    return nativeFetch.call(window,input,opts)
  };
  if(window.XMLHttpRequest){
    var open=XMLHttpRequest.prototype.open;
    XMLHttpRequest.prototype.open=function(method,url){
      var args=Array.prototype.slice.call(arguments);
      args[1]=correct(url);
      return open.apply(this,args)
    }
  }
})();
</script>
"""
if mode=="source":
    # Explicitly correct known absolute public roots before Vite minifies the JS.
    scanned=rewrite_tree(location/"src",{".ts",".tsx",".js",".mjs",".css"})
    html=location/"index.html"
    s=html.read_text()
    assert "<body" in s and "</head>" in s and "</body>" in s, "R7_UNEXPECTED_ENTRY_DOM"
    assert 'id="offline-select"' in s and 'id="char-name"' in s, "R7_NATIVE_CREATOR_MISSING"
    assert s.count("</head>")==1 and s.count("</body>")==1
    s=s.replace("</head>",EARLY_HEAD+"<style>"+INTRO_STYLE+"</style></head>")
    s=s.replace("</body>",INTRO_MARKUP+"</body>")
    html.write_text(s)
    print("REBIRTH_R7_SOURCE_REWRITES",scanned)
elif mode=="dist":
    dist=location/"dist"
    assert (dist/"index.html").is_file(), "R7_NO_INDEX"
    assert (dist/"models/props/column.glb").is_file(), "R7_MISSING_CRITICAL_COLUMN_GLB"
    assert (dist/"models/props/column_broken.glb").is_file(), "R7_MISSING_CRITICAL_COLUMN_BROKEN_GLB"
    assert (dist/"models/chars/players/knight.glb").is_file(), "R7_MISSING_KNIGHT_PREVIEW_GLB"
    rewritten=rewrite_tree(dist,{".html",".js",".css",".json",".webmanifest"})
    html=(dist/"index.html").read_text()
    assert "HIGHFLY REBIRTH" in html and "hf-r7-enter" in html, "R7_SPLASH_LOST"
    assert "hf-r7" in html and "requestFullscreen" in html,"R7_FULLSCREEN_MISSING"
    assert "offline-preview-container" in html and "body" in html,"R7_CREATOR_MISSING"
    assert "/HIGHFLY-REBIRTH/assets/" in html, "R7_BUNDLE_PREFIX_MISSING"
    suspect=[]
    for p in (dist/"assets").glob("*.js"):
        s=p.read_text(errors="replace")
        if re.search(r"""["'\x60]/(?:models|textures|env|vfx)/""",s):
            suspect.append(p.name)
    assert not suspect, "R7_UNREWRITTEN_ROOT_STATIC_ASSETS "+repr(suspect[:8])
    info={"entry":"HIGHFLY REBIRTH R7","locale":"es via URL","s23Fullscreen":"requires user tap",
          "nineNativeClasses":True,"nativeCharacterCreator":True,"rebirthSave":"R6 isolated",
          "staticFilesChecked":["models/props/column.glb","models/props/column_broken.glb",
                                "models/chars/players/knight.glb"],
          "rewrittenOutputFiles":rewritten,"physicalS23":"PENDING"}
    (dist/"rebirth-r7-qa.json").write_text(json.dumps(info,indent=2)+"\n")
    print("REBIRTH_R7_QA",json.dumps(info))
else:
    raise SystemExit("usage: script source|dist candidate")
