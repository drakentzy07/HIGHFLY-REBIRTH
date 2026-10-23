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
 """ for(let k=1;k<mobileHud.length;k++){
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
  // A live 3D CANVAS is not a visible CHARACTER. Audit actual raster pixels
  // of the creator (excluding UI border) to detect the long-standing dark
  // empty panel that passed all older GLB/DOM smoke tests.
  await page.waitForTimeout(650);
  const png=await page.locator('#offline-preview-container').screenshot({type:'png'});
  const r15Raster=await page.evaluate(async(base64)=>{
    const img=new Image();
    img.src='data:image/png;base64,'+base64;
    await img.decode();
    const canvas=document.createElement('canvas');
    canvas.width=img.width;canvas.height=img.height;
    const ctx=canvas.getContext('2d',{willReadFrequently:true});
    if(!ctx)throw Error('R15_SCREENSHOT_DECODE_CONTEXT');
    ctx.drawImage(img,0,0);
    const data=ctx.getImageData(0,0,img.width,img.height).data;
    const buckets=new Set();
    let maxL=0,minL=255;
    for(let y=Math.floor(img.height*.08);y<img.height*.94;y+=3)
    for(let x=Math.floor(img.width*.15);x<img.width*.85;x+=3){
      const i=(y*img.width+x)*4;
      const r=data[i],g=data[i+1],b=data[i+2];
      buckets.add((r>>4)*256+(g>>4)*16+(b>>4));
      const v=(r*3+g*6+b)/10;
      maxL=Math.max(maxL,v);minL=Math.min(minL,v);
    }
    return {width:img.width,height:img.height,
      colorBuckets:buckets.size,luminanceRange:maxL-minL};
  },png.toString('base64'));
  console.log('R15_CREATOR_ACTUAL_3D_RASTER '+JSON.stringify(r15Raster));
  if(r15Raster.colorBuckets<16||r15Raster.luminanceRange<30)
    throw Error('R15_CREATOR_STILL_VISUALLY_BLANK '+JSON.stringify(r15Raster));
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
