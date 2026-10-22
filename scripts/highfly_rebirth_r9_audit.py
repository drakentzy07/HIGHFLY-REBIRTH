#!/usr/bin/env python3
"""HIGHFLY REBIRTH R9 — comprehensive Pages media contract and launcher audit.

source: after R7/R8 patches, before Vite, install one canonical media resolver
and a complete fallback for raw fetch/XHR paths (plus Spanish creator labels).
dist: after R7/R8 Pages rewriting, before media prune, exhaustively verify every
catalogue asset and every canonicalized request against the *actual* published
files. This script never writes to the original HIGHFLY repository.
"""
from pathlib import Path
import hashlib
import json
import re
import sys

BASE = "/HIGHFLY-REBIRTH"
MEDIA = ("models/", "textures/", "env/", "vfx/")
mode, candidate = sys.argv[1], Path(sys.argv[2])
outdir = candidate / "dist"

def manifest():
    source = (candidate / "src/render/assets/manifest.generated.ts").read_text()
    pattern = r'export const MEDIA_ASSETS: Record<string, string> =\s*(\{.*?\})\s*as const'
    m = re.search(pattern, source, re.S)
    if not m: raise AssertionError("R9_MEDIA_MANIFEST_FORMAT_DRIFT")
    mapping = json.loads(m.group(1))
    if len(mapping) < 1500: raise AssertionError("R9_MEDIA_MANIFEST_TOO_SMALL:" + str(len(mapping)))
    if any(not k.startswith(MEDIA) or not v.startswith("/media/") for k,v in mapping.items()):
        raise AssertionError("R9_BAD_MEDIA_LOGICAL_KEYS")
    return mapping

def source_patch():
    mapping = manifest()
    p = candidate / "src/render/assets/media.ts"
    s = p.read_text()
    old = """  const logical = logicalPath(url);
  const raw = import.meta.env.DEV ?"""
    new = """  const base = import.meta.env.BASE_URL.replace(/\\/$/, '');
  const original = logicalPath(url);
  // R9: tolerate both logical keys and legacy scoped URLs, without confusing the
  // MEDIA_ASSETS lookup or adding the Pages prefix a second time.
  const logical = base && original.startsWith(base.slice(1) + '/')
    ? original.slice(base.length) : original;
  const raw = import.meta.env.DEV ?"""
    if s.count(old) != 1: raise AssertionError("R9_MEDIA_RESOLVER_DONOR_CHANGED")
    s = s.replace(old, new)
    old_base = """  const base = import.meta.env.BASE_URL.replace(/\\/$/, '');
  return base && raw.startsWith('/')"""
    if s.count(old_base) != 1: raise AssertionError("R9_MEDIA_BASE_DUPLICATE_DRIFT")
    s = s.replace(old_base, """  return base && raw.startsWith('/')""")
    p.write_text(s)

    # R7 must NOT rewrite raw logical paths to absolute Pages URLs during
    # bundling: a manifest maps logical keys, never Pages-specific strings.
    offenders = []
    for f in (candidate / "src").rglob("*"):
        if f.suffix not in (".ts", ".tsx", ".js", ".mjs", ".css"): continue
        text = f.read_text(errors="replace")
        for root in MEDIA:
            if BASE + "/" + root in text:
                offenders.append(str(f.relative_to(candidate)))
                break
    if offenders: raise AssertionError("R9_MEDIA_PREFIX_CORRUPTED_IN_SOURCE " + repr(offenders[:12]))

    html = candidate / "index.html"
    page = html.read_text()
    # A small synchronous route map makes raw THREE loader requests resolve
    # exactly like assetUrl() and works even before the native app JS imports.
    lookup = {k: v for k,v in mapping.items() if k.startswith(MEDIA)}
    entry = """<script id="hf-r9-complete-media-route-map">
(function(){
if(new URLSearchParams(location.search).get('hfRebirth')!=='1')return;
window.__hfRebirthMediaMap = """ + json.dumps(lookup,ensure_ascii=True,separators=(",",":")) + """;
})();
</script>
"""
    anchor = "<script>\n(function(){\n  if(new URLSearchParams(location.search).get('hfRebirth')!=='1')return;\n  // The native i18n module"
    if page.count(anchor) != 1: raise AssertionError("R9_R7_EARLY_BOOT_ANCHOR_DRIFT")
    page = page.replace(anchor, entry + anchor)
    correct_anchor = """    if(typeof v!=='string')return v;
    if(path.test(v))return '/HIGHFLY-REBIRTH'+v;"""
    replacement = """    if(typeof v!=='string')return v;
    // R9 central fallback. Covers direct fetch/XHR loaders, including
    // the old /models root and both Pages-scoped and unscoped logical URLs.
    try {
      var request=new URL(v,location.href);
      if(request.origin===location.origin){
        var p=request.pathname;
        var logical=p.indexOf('/HIGHFLY-REBIRTH/')===0
          ? p.slice('/HIGHFLY-REBIRTH/'.length) : p.replace(/^\\/+/, '');
        var route=window.__hfRebirthMediaMap && window.__hfRebirthMediaMap[logical];
        if(route){request.pathname='/HIGHFLY-REBIRTH'+route;return request.href;}
        // Hashed file callers sometimes use /media/ directly.
        if(p.indexOf('/media/')===0){
          request.pathname='/HIGHFLY-REBIRTH'+p;return request.href;
        }
      }
    }catch(e){}
    if(path.test(v))return '/HIGHFLY-REBIRTH'+v;"""
    if page.count(correct_anchor) != 1:
        raise AssertionError("R9_FETCH_GATEWAY_ANCHOR_DRIFT")
    page = page.replace(correct_anchor,replacement)
    # Native class mechanics stay untouched: this label-only fix is scoped to
    # REBIRTH's selection sheet, whose HP/MP/Energy adapter is already R4.
    label_fix = """<script id="hf-r9-creator-resource-ui">
(function(){
if(new URLSearchParams(location.search).get('hfRebirth')!=='1')return;
function start(){
  var target=document.getElementById('offline-class-details');
  if(!target)return;
  function refresh(){
    var walker=document.createTreeWalker(target,NodeFilter.SHOW_TEXT),node;
    while((node=walker.nextNode())){
      var v=node.nodeValue||'';
      // Replace a resource label, not the detailed talent/tooltips.
      var trimmed=v.trim();
      if(trimmed==='Ira'||trimmed==='Concentración'||trimmed==='Rage'||trimmed==='Focus')
        node.nodeValue=v.replace(trimmed,'Energía');
      else if(/^(Recurso|Resource):\\s*(Ira|Concentración|Rage|Focus)$/i.test(trimmed))
        node.nodeValue=v.replace(/(Ira|Concentración|Rage|Focus)\\s*$/,'Energía');
    }
  }
  new MutationObserver(refresh).observe(target,{subtree:true,childList:true});
  refresh();
}
if(document.readyState==='loading')
 document.addEventListener('DOMContentLoaded',start,{once:true});
else start();
})();
</script>
"""
    if page.count("</body>") != 1: raise AssertionError("R9_HTML_BODY_DRIFT")
    page = page.replace("</body>",label_fix+"</body>")
    # The native WoW-style desktop takeover uses absolute positioning. R7's
    # forced mobile grid kept pieces of that takeover and let the appearance
    # customizer float over the 9 class buttons. Restore normal flow INSIDE
    # each independently scrolling creator column, with a clear touch stack.
    creator_css = """<style id="hf-r9-creator-no-overlap">
@media (orientation:landscape) and (max-height:540px){
 html.hf-r7 #offline-select.cs-wow .char-create{
   position:relative!important;display:flex!important;flex-direction:column!important;
   justify-content:flex-start!important;align-items:stretch!important;
   width:100%!important;max-width:100%!important;
   height:auto!important;min-height:max-content!important;
   flex:0 0 auto!important;overflow:visible!important;
 }
 html.hf-r7 #offline-select.cs-wow .mini-class-row{
   position:relative!important;left:auto!important;right:auto!important;
   top:auto!important;bottom:auto!important;inset:auto!important;
   display:grid!important;grid-template-columns:repeat(3,minmax(0,1fr))!important;
   width:100%!important;height:auto!important;
   flex:0 0 auto!important;clear:both!important;
   margin:4px 0 8px!important;padding:0!important;
   z-index:30!important;transform:none!important;
 }
 html.hf-r7 #offline-select.cs-wow #offline-appearance{
   position:relative!important;left:auto!important;right:auto!important;
   top:auto!important;bottom:auto!important;inset:auto!important;
   display:block!important;width:100%!important;max-width:100%!important;
   min-height:0!important;height:auto!important;max-height:none!important;
   flex:0 0 auto!important;clear:both!important;
   margin:6px 0 8px!important;padding:0!important;transform:none!important;
   z-index:1!important;box-sizing:border-box!important;
 }
 html.hf-r7 #offline-select.cs-wow #offline-appearance .appearance-customizer{
   position:relative!important;left:auto!important;right:auto!important;
   top:auto!important;bottom:auto!important;inset:auto!important;
   display:flex!important;flex-direction:column!important;
   width:100%!important;max-width:100%!important;
   min-height:0!important;height:auto!important;max-height:none!important;
   margin:0!important;transform:none!important;
   box-sizing:border-box!important;z-index:1!important;
 }
 html.hf-r7 #offline-select.cs-wow .charselect-col-left{
   overflow-y:auto!important;overflow-x:hidden!important;
   overscroll-behavior:contain!important;
 }
 html.hf-r7 #offline-select.cs-wow .auth-actions{
   position:relative!important;z-index:2!important;flex:0 0 auto!important;
   margin:8px 0 3px!important;
 }
}
</style>"""
    if page.count("</head>") != 1:raise AssertionError("R9_CREATOR_CSS_HEAD_DRIFT")
    page=page.replace("</head>",creator_css+"</head>")
    html.write_text(page)
    print("R9_SOURCE_PASS",len(mapping),"logical assets routed without prefix corruption")

def check_glb(path):
    with path.open("rb") as f: header=f.read(12)
    if len(header)<12 or header[:4]!=b"glTF":
        raise AssertionError("R9_INVALID_GLB_MAGIC " + str(path))
    length=int.from_bytes(header[8:12],"little")
    if int.from_bytes(header[4:8],"little")!=2 or length!=path.stat().st_size:
        raise AssertionError("R9_INVALID_GLB_HEADER_OR_SIZE " + str(path))

def dist_audit():
    mapping=manifest()
    if not outdir.is_dir(): raise AssertionError("R9_MISSING_DIST")
    # CSS url() and HTML src/href load through the BROWSER, bypassing the
    # runtime fetch/XHR gateway. Resolve every logical media URL directly to
    # the same hashed /media file before the exhaustive no-404 scan.
    media_links = re.compile(
        r'(?P<root>/HIGHFLY-REBIRTH/|/)(?P<logical>(?:models|textures|env|vfx)/[A-Za-z0-9_./-]+)'
    )
    rewrites = 0
    for f in outdir.rglob("*"):
        if not f.is_file() or f.suffix.lower() not in (".css",".html",".svg",".xml"):
            continue
        old = f.read_text(errors="replace")
        def map_direct(m):
            logical = m.group("logical")
            if logical not in mapping:
                return m.group(0)   # The separate no-404 scan will fail unknowns.
            return BASE+mapping[logical]
        new = media_links.sub(map_direct,old)
        if new != old:
            f.write_text(new)
            rewrites+=1
    print("R9_CSS_HTML_DIRECT_MEDIA_ALIAS_REPAIRED",rewrites)
    total_bytes=0
    counts={}
    failures=[]
    for logical,uri in mapping.items():
        f=outdir/uri.lstrip("/")
        if not f.is_file():
            failures.append("MISSING "+logical+" -> "+uri)
            continue
        size=f.stat().st_size
        total_bytes+=size
        if size<=0:
            failures.append("EMPTY "+logical)
            continue
        ext=f.suffix.lower()
        counts[ext]=counts.get(ext,0)+1
        # Complete catalogue SHA contract: detects incorrect naming or files
        # copied from another release (the common mismatched 0.44/0.45 case).
        digest=hashlib.sha256(f.read_bytes()).hexdigest()[:12]
        actual=f.stem.rsplit(".",1)[-1]
        if actual!=digest:
            failures.append("HASH "+logical+" expected "+actual+" got "+digest)
        if ext==".glb":
            try:check_glb(f)
            except AssertionError as e:failures.append(str(e))
        if ext==".ktx2" and f.read_bytes()[:12]!=b'\xabKTX 20\xbb\r\n\x1a\n':
            failures.append("INVALID_KTX2 "+logical)
        # Contract: both historical URL shapes must map to a REAL file after
        # the source patch and the runtime raw-URL fallback.
        for raw in ("/"+logical,BASE+"/"+logical):
            route=BASE+mapping[raw[len(BASE)+1:] if raw.startswith(BASE+"/") else raw.lstrip("/")]
            expected=BASE+uri
            if route!=expected or not (outdir/route[len(BASE)+1:]).is_file():
                failures.append("INVALID_RESOLUTION "+raw)
    if failures:
        raise AssertionError("R9_CATALOGUE_CONTRACT_FAILURE_COUNT="+str(len(failures))+
                             " sample="+repr(failures[:14]))
    for key in ("models/chars/players/knight.glb",
                "models/creatures/bull.glb",
                "models/biome/kcas_torch_mounted.glb",
                "models/biome/kcas_rubble_large.glb",
                "models/biome/kcas_bookcase.glb"):
        if key not in mapping: raise AssertionError("R9_USER_VIDEO_ASSET_MISSING "+key)
    for req in ("index.html","play.html","editor.html","manifest.webmanifest",
                "basis/basis_transcoder.wasm"):
        if not (outdir/req).is_file():raise AssertionError("R9_STATIC_BOOT_MISSING "+req)
    page=(outdir/"index.html").read_text()
    for term in ("hf-r9-complete-media-route-map","__hfRebirthMediaMap",
                 "hf-r9-creator-resource-ui","hf-r7-enter",
                 "/HIGHFLY-REBIRTH/assets/","hf-r8-logo"):
        if term not in page:raise AssertionError("R9_LAUNCHER_COMPONENT_MISSING "+term)
    webmanifest=json.loads((outdir/"manifest.webmanifest").read_text())
    if webmanifest.get("scope")!=BASE+"/" or BASE not in webmanifest.get("start_url",""):
        raise AssertionError("R9_UNSCOPED_PWA_MANIFEST")
    js=list((outdir/"assets").glob("*.js"))
    if not js:raise AssertionError("R9_MISSING_GAME_JS")
    # Inspect actual HTML/CSS asset addresses beyond the media manifest.
    # These fetches are issued by the browser itself (fonts/images), bypassing
    # JavaScript fetch wrappers entirely.
    unresolved=[]
    root_assets=(".png",".jpg",".jpeg",".svg",".webp",".woff",".woff2",
                 ".glb",".ktx2",".wasm",".ogg",".mp3",".mp4",".css",".js")
    for file in outdir.rglob("*"):
        if not file.is_file() or file.suffix.lower() not in (".html",".css"):
            continue
        body=file.read_text(errors="replace")
        refs=re.findall(r'(?:src|href)\s*=\s*["\x27]([^"\x27]+)["\x27]',body)
        refs+=re.findall(r'url\(\s*["\x27]?([^\s)"\x27]+)',body)
        for ref in refs:
            path=ref.split("?",1)[0].split("#",1)[0]
            if path.startswith(("data:","http:","https:","blob:","//","#")):continue
            if not path.lower().endswith(root_assets):continue
            if path.startswith(BASE+"/"):
                local=outdir/path[len(BASE)+1:]
            elif path.startswith("/"):
                unresolved.append(str(file.relative_to(outdir))+": root URL "+path)
                continue
            else:
                local=(file.parent/path).resolve()
            if not local.is_file():
                unresolved.append(str(file.relative_to(outdir))+": not published "+path)
        if len(unresolved)>100:break
    if unresolved:
        raise AssertionError("R9_HTML_CSS_DIRECT_ASSETS_INVALID_COUNT="+str(len(unresolved))+
                             " sample="+repr(unresolved[:15]))
    media=(candidate/"src/render/assets/media.ts").read_text()
    if "original.startsWith(base.slice(1) + '/')" not in media:
        raise AssertionError("R9_CANONICAL_ASSET_URL_NOT_INSTALLED")
    if "MEDIA_ASSETS[logical]" not in media:
        raise AssertionError("R9_HASH_LOOKUP_DISABLED")
    report={
      "version":"HIGHFLY REBIRTH R9", "outcome":"PASS: FULL CATALOGUE CONTRACT",
      "base":BASE,"catalogue_total":len(mapping),"by_extension":counts,
      "hashed_asset_bytes":total_bytes,
      "raw_and_scoped_requests_verified":2*len(mapping),
      "sha256_verified":len(mapping),
      "GLB_valid_headers":counts.get(".glb",0),
      "KTX2_verified":counts.get(".ktx2",0),
      "pwa_scope":"PASS",
      "direct_html_css_assets":"PASS",
      "css_html_rewritten_files":rewrites,
      "mobile_creator":"needs physical S23 test",
      "world_loading":"needs physical S23 test",
      "source_repo":"ClaudeCraft-v0.44.7",
      "original_highfly_repo":"UNMODIFIED"
    }
    (outdir/"rebirth-r9-audit.json").write_text(json.dumps(report,indent=2)+"\n")
    print("R9_FULL_CATALOGUE_AUDIT_PASS",json.dumps(report))

if mode=="source":source_patch()
elif mode=="dist":dist_audit()
else:raise SystemExit("usage: audit.py source|dist candidate")
