#!/usr/bin/env python3
"""HIGHFLY R16 stage 1: native S23 layout + creator visibility, NO NEW SIM.
Applied AFTER the frozen R15 overlay. Strict single anchors fail closed.
No gameplay or save schema is touched by this stage.
"""
from pathlib import Path
import json
import sys

if len(sys.argv) != 2:
    raise SystemExit("usage: highfly_rebirth_r16_visual.py <candidate>")
root = Path(sys.argv[1]).resolve()
main = root / "src/main.ts"
source = main.read_text(encoding="utf-8")
anchor = "import './highfly/rebirth/r15_style.css';"
assert source.count(anchor) == 1, "R16_DRIFT_R15_CSS_IMPORT"
source = source.replace(anchor, anchor + """
import './highfly/rebirth/r16_layout.css';
import './highfly/rebirth/r16_layout';""", 1)

# R15 only reattached the existing canvas. Keep a ResizeObserver on its live
# parent: fullscreen / first WebGL frame on Android often changes actual size
# without generating a window resize event. No new renderer/context.
anchor = """    requestAnimationFrame(()=>characterPreview?.syncSize());
  };
  if(hfOffline){"""
assert source.count(anchor) == 1, "R16_DRIFT_R15_PREVIEW_SYNC"
source = source.replace(anchor, """    requestAnimationFrame(()=>characterPreview?.syncSize());
  };
  if(hfOffline){""", 1)
anchor = """    window.addEventListener('resize',hfReseat,{passive:true});"""
assert source.count(anchor) == 1, "R16_DRIFT_R15_RESIZE"
source = source.replace(anchor, """    const hfR16PreviewHost=document.getElementById('offline-preview-container');
    if(hfR16PreviewHost && typeof ResizeObserver!=='undefined'){
      const hfR16SizeWatch=new ResizeObserver(()=>{
        if(!hfOffline.hasAttribute('hidden') &&
           getComputedStyle(hfOffline).display!=='none'){
          requestAnimationFrame(()=>characterPreview?.syncSize());
        }
      });
      hfR16SizeWatch.observe(hfR16PreviewHost);
    }
    window.addEventListener('resize',hfReseat,{passive:true});""", 1)
main.write_text(source, encoding="utf-8")

out = root / "src/highfly/rebirth"
out.mkdir(parents=True, exist_ok=True)
(out / "r16_layout.ts").write_text(r"""/**
 * R16: move EXISTING native elements, never duplicate HP/skill/menu.
 * The native #mobile-more retains its MobileControls listener and opens
 * #mobile-extra-controls exactly as before.
 */
type Rect = { x:number; y:number; width:number; height:number };
function rectOf(id:string):Rect|null {
  const el=document.getElementById(id);
  if(!el)return null;
  const r=el.getBoundingClientRect();
  return {x:r.x,y:r.y,width:r.width,height:r.height};
}
function syncR16():void {
  if(!document.body.classList.contains('hf-rebirth-r2'))return;
  const more=document.getElementById('mobile-more');
  if(more && more.parentElement!==document.body){
    document.body.appendChild(more);
    more.textContent='⋯';
    more.removeAttribute('data-icon');
    more.removeAttribute('data-i18n-aria');
    more.setAttribute('aria-label','Abrir MÁS');
    more.setAttribute('title','MÁS');
    more.tabIndex=0;
    more.dataset.hfR16NativeMore='1';
  }
  const player=document.getElementById('player-frame');
  if(player && player.parentElement!==document.body){
    document.body.appendChild(player);
    player.dataset.hfR16SinglePlayerFrame='1';
  }
}
function boot():void {
  syncR16();
  new MutationObserver(syncR16).observe(document.body,{
    attributes:true,attributeFilter:['class']
  });
  (window as Window & {__hfR16VisualDiagnostics?:()=>object})
    .__hfR16VisualDiagnostics=()=>({
      active:document.body.classList.contains('hf-rebirth-r2'),
      playerFrameCount:document.querySelectorAll('#player-frame').length,
      playerFrame:rectOf('player-frame'),
      nativeMoreCount:document.querySelectorAll('#mobile-more').length,
      nativeMore:rectOf('mobile-more'),
      originalMoreDialog:!!document.getElementById('mobile-extra-controls'),
      moreOpen:document.body.classList.contains('mobile-more-open'),
      previewParent:document.getElementById('char-preview-canvas')?.parentElement?.id??null,
      preview:rectOf('offline-preview-container'),
      canvas:rectOf('char-preview-canvas')
    });
}
if(document.readyState==='loading')
  document.addEventListener('DOMContentLoaded',boot,{once:true});
else boot();
""", encoding="utf-8")

(out / "r16_layout.css").write_text(r"""/* HIGHFLY R16 single owner HUD / S23 landscape.
   Supersedes R12's 2 rows and R15's bottom positioning via ONE last import.
   No fake resource bars, no duplicate controls, no new game engine. */
@media (orientation:landscape) and (max-height:650px) {
  html body.mobile-touch.hf-rebirth-r2 #player-frame {
    position:fixed!important;
    top:clamp(7px,1.6vh,12px)!important;
    left:clamp(8px,1.2vw,16px)!important;
    right:auto!important;bottom:auto!important;
    margin:0!important;transform:none!important;
    opacity:1!important;visibility:visible!important;
    z-index:180!important;pointer-events:auto!important;
    max-width:min(31vw,275px)!important;
  }
  html body.mobile-touch.hf-rebirth-r2 #mobile-more {
    position:fixed!important;
    top:clamp(70px,17vh,82px)!important;left:clamp(11px,1.7vw,23px)!important;
    right:auto!important;bottom:auto!important;
    display:flex!important;align-items:center!important;justify-content:center!important;
    width:49px!important;height:49px!important;min-width:49px!important;
    border:1.5px solid #d6bb7e!important;border-radius:50%!important;
    color:#f6d89b!important;background:#222936ed!important;
    font:bold 30px/1 system-ui,sans-serif!important;
    z-index:190!important;opacity:1!important;visibility:visible!important;
    transform:none!important;touch-action:manipulation!important;
    pointer-events:auto!important;padding:0 0 8px!important;
  }
  html body.mobile-touch.hf-rebirth-r2 #mobile-menu-anchor {
    display:none!important;
  }
  html body.mobile-touch.hf-rebirth-r2.mobile-more-open #mobile-extra-controls {
    z-index:1600!important;
  }
  /* Original four equipped slots and native ATK remain single instances. */
  html body.mobile-touch.hf-rebirth-r2 #mobile-action-ring {
    z-index:150!important;
    right:0!important;bottom:0!important;
    width:min(59vw,560px)!important;height:min(52vh,224px)!important;
  }
  html body.mobile-touch.hf-rebirth-r2 #mobile-action-ring #mobile-action-attack {
    right:15px!important;bottom:76px!important;
    width:74px!important;height:74px!important;
  }
  html body.mobile-touch.hf-rebirth-r2 #mobile-action-ring #mobile-interact {
    right:20px!important;bottom:12px!important;
  }
  html body.mobile-touch.hf-rebirth-r2 #mobile-action-ring #mobile-jump {
    right:270px!important;bottom:22px!important;
  }
  html body.mobile-touch.hf-rebirth-r2 #mobile-action-ring #mobile-evade {
    right:325px!important;bottom:22px!important;
  }
  html body.mobile-touch.hf-rebirth-r2 #mobile-action-ring .mobile-action-slot[data-mobile-index="0"]{
    right:94px!important;bottom:15px!important
  }
  html body.mobile-touch.hf-rebirth-r2 #mobile-action-ring .mobile-action-slot[data-mobile-index="1"]{
    right:153px!important;bottom:52px!important
  }
  html body.mobile-touch.hf-rebirth-r2 #mobile-action-ring .mobile-action-slot[data-mobile-index="2"]{
    right:158px!important;bottom:115px!important
  }
  html body.mobile-touch.hf-rebirth-r2 #mobile-action-ring .mobile-action-slot[data-mobile-index="3"]{
    right:98px!important;bottom:164px!important
  }
  /* World-facing HUD cannot overlap creator; character model gets a real
     non-zero right-column viewport for GPU presentation. */
  html.hf-r7 #offline-select.cs-wow .charselect-col-right{
    min-height:0!important;overflow:hidden!important;align-items:stretch!important
  }
  html.hf-r7 #offline-select.cs-wow #offline-preview-container{
    position:relative!important;display:block!important;
    box-sizing:border-box!important;
    width:100%!important;
    height:clamp(190px,58dvh,315px)!important;
    flex:1 1 auto!important;min-height:190px!important;
    max-height:calc(100dvh - 64px)!important;
    overflow:hidden!important;visibility:visible!important;opacity:1!important;
    background:radial-gradient(ellipse at center,#31485a66,#111725bb)!important;
  }
  html.hf-r7 #offline-select.cs-wow #offline-preview-container #char-preview-canvas{
    position:absolute!important;inset:0!important;
    display:block!important;width:100%!important;height:100%!important;
    min-width:100%!important;min-height:100%!important;
    transform:none!important;opacity:1!important;visibility:visible!important;
  }
  html.hf-r7 #offline-select.cs-wow #offline-class-details{
    flex:0 1 auto!important;max-height:23dvh!important;overflow:auto!important
  }
}
""", encoding="utf-8")
(root/"public/highfly-r16-status.json").write_text(json.dumps({
  "version":"R16_S23_VISUAL_STAGE1",
  "base":"R15 existing Sim / ClaudeCraft v0.44.7",
  "cap":20,"originalClasses":9,
  "menu":"move native #mobile-more; opens native #mobile-extra-controls",
  "playerFrame":"one native #player-frame moved top-left",
  "creator":"one native WebGL canvas + live ResizeObserver; visual browser QA required",
  "hpMpEnDualAuthoritativeSim":False,
  "nativeResourceConversionDone":False,
  "fourPhysicalComboVerified":False,
  "allSkillAimingVerified":False,
  "physicalS23Verified":False,
  "r11ProductionChanged":False,
  "safeToPublish":False
},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("R16_VISUAL_STAGE1_PATCHED=PASS; GAMEPLAY_UNMODIFIED; PHYSICAL_QA_PENDING")
