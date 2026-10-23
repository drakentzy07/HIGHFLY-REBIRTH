#!/usr/bin/env python3
"""R15 Chromium browser assertions on the ACTUAL native app, not mock divs."""
from pathlib import Path
import sys
p=Path(sys.argv[1]);s=p.read_text(encoding='utf8')
def once(label,anchor,update):
 global s
 if s.count(anchor)!=1:raise AssertionError("R15_TEST_ANCHOR_"+label+"="+str(s.count(anchor)))
 s=s.replace(anchor,update,1)
once('spatialHUD',
 """  for(let k=1;k<mobileHud.length;k++){
    const previous=mobileHud[k-1],current=mobileHud[k];
    if(current.cx<previous.cx+(previous.width+current.width)/2+3)
      throw Error('R12_HUD_TOUCH_OVERLAP_OR_BAD_ORDER '+JSON.stringify(mobileHud));
  }""",
 """  // R15 uses an arc, not the obsolete R12 straight row. Check ACTUAL
  // two-dimensional hit regions, including the same zero-size guard above.
  for(let i=0;i<mobileHud.length;i++)for(let j=i+1;j<mobileHud.length;j++){
    const a=mobileHud[i],b=mobileHud[j];
    const dx=Math.abs(a.cx-b.cx),dy=Math.abs(a.cy-b.cy);
    const intersectionX=dx<(a.width+b.width)/2-3;
    const intersectionY=dy<(a.height+b.height)/2-3;
    if(intersectionX&&intersectionY)
      throw Error('R15_HUD_REAL_TOUCH_RECT_OVERLAP '+JSON.stringify({a,b}));
  }
  console.log('R15_ARC_LAYOUT_SPATIAL_TOUCH_SEPARATION=PASS');""")
once('preview',
 " if(!glbs.length)throw Error('R9_PREVIEW_CANVAS_WITHOUT_LOADED_GLB');",
 """  if(!glbs.length)throw Error('R9_PREVIEW_CANVAS_WITHOUT_LOADED_GLB');
  const r15Preview=await page.evaluate(()=>
    window.__hfR15PreviewDiagnostics?.()??null);
  console.log('R15_CREATOR_WEBGL_OWNER '+JSON.stringify(r15Preview));
  if(!r15Preview?.mounted||!r15Preview?.attached||
     r15Preview.width<80||r15Preview.height<80||
     r15Preview.canvasWidth<80||r15Preview.canvasHeight<80||
     r15Preview.webglLost){
    throw Error('R15_CREATOR_EMPTY_OR_WRONG_CANVAS_OWNER '+JSON.stringify(r15Preview));
  }""")
once('hud',
 " console.log('R14_FREEDOM_RUNTIME_PROFILE '+JSON.stringify(r14));",
 """ console.log('R14_FREEDOM_RUNTIME_PROFILE '+JSON.stringify(r14));
 const r15HUD=await page.evaluate(()=>{
  const el=id=>document.querySelector(id);
  const rect=id=>{const e=el(id);if(!e)return null;
    const r=e.getBoundingClientRect(),css=getComputedStyle(e);
    return {x:r.x,y:r.y,w:r.width,h:r.height,display:css.display};};
  const skills=[0,1,2,3].map(i=>rect('#mobile-action-ring .mobile-action-slot[data-mobile-index="'+i+'"]'));
  const nativeResource=el('#pf-resource');
  const p=window.__game.sim.player;
  const castMaskSource=!!window.__game?.renderer;
  return {skills,atk:rect('#mobile-action-attack'),
    jump:rect('#mobile-jump'),dash:rect('#mobile-evade'),
    interact:rect('#mobile-interact'),passive:rect('#hf-r12-passive'),
    page:rect('#mobile-action-page-toggle'),
    resourceType:p.resourceType,resource:p.resource,max:p.maxResource,
    shownType:nativeResource?.dataset.highflyR15Resource??null,
    shownValue:nativeResource?.dataset.highflyR15Available??null,
    castMaskSource};
 });
 console.log('R15_REAL_HUD_AND_NATIVE_RESOURCE '+JSON.stringify(r15HUD));
 if(!r15HUD.atk||r15HUD.atk.w<65||
    !r15HUD.skills.every(x=>x&&x.w>=36&&x.h>=36)||
    !r15HUD.passive||!r15HUD.interact||
    !r15HUD.shownType||r15HUD.shownValue===null){
   throw Error('R15_HUD_RESOURCE_NOT_READY '+JSON.stringify(r15HUD));
 }""")
p.write_text(s,encoding='utf8')
print("R15_S23_NATIVE_CREATOR_HUD_RESOURCE_BROWSER_ASSERTIONS_APPLIED")
