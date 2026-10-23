#!/usr/bin/env node
/**
 * R9 in-browser gate. Opens built GitHub Pages-shaped app with a fresh mobile
 * profile, waits for a real GLB-backed native creator and completes world boot.
 * A green static build alone is insufficient.
 */
import { createServer } from 'node:http';
import { createReadStream, existsSync, statSync, mkdirSync, writeFileSync } from 'node:fs';
import { resolve, join, extname, sep } from 'node:path';
import { chromium } from 'playwright';

const ROOT=resolve(process.cwd(),'dist');
const DIAG=resolve(process.cwd(),'.run-diagnostics');
mkdirSync(DIAG,{recursive:true});
const PREFIX='/HIGHFLY-REBIRTH';
const mime={
 '.js':'text/javascript;charset=utf-8','.html':'text/html;charset=utf-8',
 '.css':'text/css;charset=utf-8','.json':'application/json;charset=utf-8',
 '.webmanifest':'application/manifest+json','.glb':'model/gltf-binary',
 '.ktx2':'image/ktx2','.wasm':'application/wasm','.woff2':'font/woff2',
 '.png':'image/png','.jpg':'image/jpeg','.jpeg':'image/jpeg','.svg':'image/svg+xml',
 '.webp':'image/webp','.ogg':'audio/ogg','.mp3':'audio/mpeg',
};
const missing=[];
const diagnostics={bootConsole:[],failedResources:[],stages:[]};
const server=createServer((req,res)=>{
 const raw=new URL(req.url||'/', 'http://127.0.0.1:4187').pathname;
 const scoped=raw===PREFIX||raw.startsWith(PREFIX+'/');
 if(!scoped){res.writeHead(404);res.end('Outside HIGHFLY scope');missing.push(raw);return;}
 const sub=raw.slice(PREFIX.length).replace(/^\/+/, '')||'index.html';
 const resolved=resolve(ROOT,sub);
 if(resolved!==ROOT&&!resolved.startsWith(ROOT+sep)){
   res.writeHead(403);res.end('Invalid path');return;
 }
 const filename=existsSync(resolved)&&statSync(resolved).isFile()?resolved:null;
 if(!filename){missing.push(raw);res.writeHead(404);res.end('Not Found '+raw);return;}
 const total=statSync(filename).size;
 const range=req.headers.range?.match(/^bytes=(\d+)-(\d*)$/);
 if(range){
   const start=Number(range[1]),end=range[2]?Math.min(total-1,Number(range[2])):total-1;
   if(start>=total){res.writeHead(416);res.end();return;}
   res.writeHead(206,{'Content-Type':mime[extname(filename)]||'application/octet-stream',
      'Content-Length':end-start+1,'Content-Range':'bytes '+start+'-'+end+'/'+total,
      'Accept-Ranges':'bytes','Cache-Control':'no-store'});
   createReadStream(filename,{start,end}).pipe(res);return;
 }
 res.writeHead(200,{'Content-Type':mime[extname(filename)]||'application/octet-stream',
   'Content-Length':total,'Cache-Control':'no-store'});
 createReadStream(filename).pipe(res);
});
await new Promise((ok,fail)=>server.listen(4187,'127.0.0.1',e=>e?fail(e):ok()));
let browser;
try{
 browser=await chromium.launch({
  headless:true,timeout:60000,
  args:['--no-sandbox','--disable-dev-shm-usage','--enable-webgl',
        '--enable-unsafe-swiftshader','--use-gl=angle','--use-angle=swiftshader']
 });
 const context=await browser.newContext({
   viewport:{width:932,height:430},isMobile:true,hasTouch:true,
   deviceScaleFactor:1,serviceWorkers:'block'
 });
 const page=await context.newPage();
 page.setDefaultTimeout(40000);
 const failures=[],network=[],consoleIssues=[],requestFailures=[];
 page.on('pageerror',err=>{const msg='JS '+String(err).slice(0,400);failures.push(msg);consoleIssues.push(msg);});
 page.on('requestfailed',req=>requestFailures.push({url:req.url(),error:req.failure()?.errorText}));
 page.on('response',r=>{
   const path=new URL(r.url()).pathname;
   if(/\.(glb|ktx2|wasm)(\?|$)/.test(path)){
     network.push({status:r.status(),path});
     if(r.status()>=400)failures.push('ASSET HTTP '+r.status()+' '+r.url());
   }
   if(r.status()>=400 && /\.(glb|ktx2|wasm|js|css|woff2?|jpg|png|webp|hdr)(\?|$)/i.test(path)){
     failures.push('HTTP '+r.status()+' '+r.url());
   }
 });
 page.on('console',m=>{
   const str=m.text();
   if(/\[entry-guard\]|\[load-profile\]|deferred preload|asset load failed|prewarm failed|character preview assets failed/i.test(str)){
     diagnostics.bootConsole.push({type:m.type(),text:str.slice(0,700)});
     if(diagnostics.bootConsole.length>150)diagnostics.bootConsole.shift();
   }
   if(m.type()==='error'||(m.type()==='warning' && /webgl|ktx2|glb|character|preview|transcode|shader|wasm/i.test(str)))
     consoleIssues.push(m.type()+': '+str.slice(0,500));
   if(/asset load failed|missing file or bad GLB|Error: Failed to fetch/i.test(str))
     failures.push('BROWSER '+str.slice(0,300));
 });
 // Low is the official source game's graphics-tier smoke for headless
// SwiftShader; full quality on S23 is checked separately, not inferred.
const url='http://127.0.0.1:4187'+PREFIX+'/?hfRebirth=1&lang=es&gfx=low';
 await page.goto(url,{waitUntil:'load',timeout:60000});
 await page.locator('#hf-r7-enter').click();
 await page.locator('#offline-select').waitFor({state:'visible',timeout:40000});
 const classCount=await page.locator('#offline-select .mini-class').count();
 if(classCount!==9)throw Error('R9_NATIVE_NINE_CLASSES_NOT_PRESENT='+classCount);
 const placement=await page.evaluate(()=>{
  const select=(q)=>{
   const e=document.querySelector(q);
   if(!e)return null;
   const r=e.getBoundingClientRect();
   const x=r.left+r.width/2,y=r.top+r.height/2;
   const hit=document.elementFromPoint(x,y);
   return {x:Math.round(x),y:Math.round(y),width:Math.round(r.width),
     height:Math.round(r.height),hitTag:hit?.tagName,hitClass:hit?.className,
     hitId:hit?.id,position:getComputedStyle(e).position};
  };
  return {warrior:select('#offline-select .mini-class[data-class="warrior"]'),
    appearance:select('#offline-appearance'),appearanceHead:select('#offline-appearance .ac-head'),
    preview:select('#offline-preview-container'),
    action:select('#btn-start-offline')};
 });
 console.log('R9_CREATOR_LAYOUT_GEOMETRY '+JSON.stringify(placement));
 await page.locator('#offline-select .mini-class[data-class="warrior"]').click();
 try {
 await page.waitForFunction(()=>{
   const el=document.querySelector('#offline-preview-container canvas');
   return el && el.width>=80 && el.height>=80 &&
    el.getBoundingClientRect().width>=80 && el.getBoundingClientRect().height>=80;
 },null,{timeout:75000,polling:300});
 }catch(err){
   const state=await page.evaluate(()=>{
     const c=document.getElementById('char-preview-canvas');
     const o=document.getElementById('offline-preview-container');
     const n=document.getElementById('online-preview-container');
     const box=e=>{if(!e)return null;const r=e.getBoundingClientRect();return {width:r.width,height:r.height,hidden:e.hidden,display:getComputedStyle(e).display,visibility:getComputedStyle(e).visibility}};
     return {canvasParent:c?.parentElement?.id,canvasSize:c?{width:c.width,height:c.height}:null,
       canvas:box(c),offline:box(o),online:box(n),
       loadingStatus:document.getElementById('ls-status')?.textContent,
       pageText:document.body.innerText.slice(-900),loadingProgress:document.getElementById('ls-fill')?.style.width,
       loadProfile:!!window.__loadProfile};
   });
   await page.screenshot({path:join(DIAG,'preview-failure.png'),fullPage:true,timeout:10000}).catch(()=>{});
   console.error('R9_PREVIEW_FORENSICS '+JSON.stringify({
     state,glbs:network.filter(x=>x.path.endsWith('.glb')).slice(-20),
     issueCount:consoleIssues.length,consoleIssues:consoleIssues.slice(-24),
     failures:failures.slice(-12),requests:requestFailures.slice(-15),
     serverMissing:missing.slice(-18)}));
   throw err;
 }
 // The real preview is not proven by a canvas alone. There must be a successful
 // versioned GLB fetch in addition to a painted WebGL canvas.
 const glbs=network.filter(x=>x.status===200&&x.path.includes('/media/models/')&&x.path.endsWith('.glb'));
 if(!glbs.length)throw Error('R9_PREVIEW_CANVAS_WITHOUT_LOADED_GLB');
 if(failures.length)throw Error('R9_PREVIEW_ASSET_FAILURE '+failures.slice(0,8).join(' | '));
 await page.locator('#char-name').fill('RebirthTester');
 await page.locator('#btn-start-offline').click();
 // The native character validator accepts letters/spaces/apostrophes/hyphens
 // ONLY. A rejected test name must fail immediately, never masquerade as a
 // GLB/world-entry timeout or falsely accuse the real mobile build.
 await page.waitForFunction(()=>{
   const error=document.querySelector('#offline-error')?.textContent?.trim();
   return document.body.classList.contains('game-active') || Boolean(error);
 },null,{timeout:25000,polling:200});
 const nameError=(await page.locator('#offline-error').textContent())?.trim();
 if(nameError)throw Error('R9_NATIVE_CREATOR_REJECTED_NAME '+nameError);
 console.log('R9_VALID_NAME_ACCEPTED_AND_WORLD_ENTRY_STARTED=PASS');
 async function captureWorldForensics(reason){
   const state=await page.evaluate(()=>{
     const visible=(selector)=>{
       const e=document.querySelector(selector);if(!e)return null;
       const css=getComputedStyle(e);const r=e.getBoundingClientRect();
       return {visible:css.visibility,display:css.display,width:r.width,height:r.height,
         classes:e.className,text:e.textContent?.slice(0,220)};
     };
     const localStorageKeys=Object.keys(localStorage).filter(x=>/highfly|rebirth|save|character/i.test(x));
     return {location:location.href,ready:document.readyState,
       gameDefined:!!window.__game,hasSim:!!window.__game?.sim,
       playerDefined:!!window.__game?.sim?.player,
       gameScreen:visible('#game-container'),loadingScreen:visible('#loading-screen'),
       loadingStatus:visible('#ls-status'),
       authScreen:visible('#offline-select'),
       assetError:visible('#asset-error'),fatalOverlay:visible('#disconnect-overlay'),
       allCanvases:[...document.querySelectorAll('canvas')].map(x=>({
         id:x.id,parent:x.parentElement?.id,width:x.width,height:x.height})),
       storageKeys:localStorageKeys,bodyText:document.body.innerText.slice(-1100)};
   });
   const payload={reason,state,bootConsole:diagnostics.bootConsole.slice(-70),
     networkTail:network.slice(-45),errors:failures.slice(-30),
     consoleIssues:consoleIssues.slice(-35),requestFailures:requestFailures.slice(-24),
     serverMissing:missing.slice(-30)};
   console.error('R9_WORLD_FORENSICS '+JSON.stringify(payload));
   writeFileSync(join(DIAG,'world-failure.json'),JSON.stringify(payload,null,2)+'\n');
   await page.screenshot({path:join(DIAG,'world-failure.png'),fullPage:true,timeout:10000}).catch(()=>{});
   return payload;
 }
 try {
 await page.waitForFunction(()=>{
   const l=document.querySelector('#loading-screen');
   return Boolean(window.__game?.sim?.player) &&
     (!l || !l.classList.contains('visible'));
 },null,{timeout:180000,polling:500});
 }catch(err) {
   await captureWorldForensics(err?.message||'WORLD_TIMEOUT');
   throw new Error('R9_WORLD_FAILED_SEE_FORENSICS: '+String(err?.message||err));
 }
 // R12 S23 layout contract: five actual native controls, in requested order.
 // Passive opens the NATIVE spellbook; Dash is original R2 input onEvade.
 const mobileHud=await page.evaluate(()=>{
   const specs=[
     ['passive','#hf-r12-passive'],['jump','#mobile-jump'],
     ['dash','#mobile-evade'],
     ['skill1','#mobile-action-ring .mobile-action-slot[data-mobile-index="0"]'],
     ['use','#mobile-interact']];
   return specs.map(([id,selector])=>{
     const el=document.querySelector(selector);
     if(!el)return {id,missing:true};
     const r=el.getBoundingClientRect(),style=getComputedStyle(el);
     const cx=r.left+r.width/2,cy=r.top+r.height/2;
     const at=document.elementFromPoint(cx,cy);
     return {id,cx,cy,width:r.width,height:r.height,display:style.display,
       hit:at?.id||at?.closest('button')?.id||null};
   });
 });
 console.log('R12_S23_HUD_GEOMETRY '+JSON.stringify(mobileHud));
 if(mobileHud.some(x=>x.missing||x.display==='none'||x.width<32||x.height<32))
   throw Error('R12_MISSING_OR_TOO_SMALL_HUD_BUTTON '+JSON.stringify(mobileHud));
 for(let k=1;k<mobileHud.length;k++){
   const previous=mobileHud[k-1],current=mobileHud[k];
   if(current.cx<previous.cx+(previous.width+current.width)/2+3)
     throw Error('R12_HUD_TOUCH_OVERLAP_OR_BAD_ORDER '+JSON.stringify(mobileHud));
 }
 // Exercise the REAL multi-touch router through Chromium CDP. Synthetic DOM
 // dispatchEvent does not create pointer capture and can lie about joystick.
 const cdp=await context.newCDPSession(page);
 const origin=await page.evaluate(()=>{
   const el=document.getElementById('mobile-move-joystick');
   const r=el?.getBoundingClientRect();
   const zone=document.getElementById('mobile-move-zone')?.getBoundingClientRect();
   const center=r?{x:r.left+r.width/2,y:r.top+r.height/2}:null;
   return {center,zone:zone?{x:zone.x,y:zone.y,width:zone.width,height:zone.height}:null};
 });
 if(!origin.center)throw Error('R12_MOVE_WHEEL_MISSING');
 const initial=await page.evaluate(()=>{
   const g=window.__game,p=g.sim.player;
   return {x:p.pos.x,z:p.pos.z,yaw:g.input.camYaw,
     highfly:typeof g.input.highflyTouchVector==='function'?g.input.highflyTouchVector():null};
 });
 const x=origin.center.x,y=origin.center.y;
 await cdp.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{x,y,id:7}]});
 await cdp.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[{x,y:y-46,id:7}]});
 await page.waitForTimeout(1000);
 const moved=await page.evaluate(()=>{
   const g=window.__game,p=g.sim.player;
   return {x:p.pos.x,z:p.pos.z,yaw:g.input.camYaw,
     highfly:typeof g.input.highflyTouchVector==='function'?g.input.highflyTouchVector():null};
 });
 await cdp.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});
 const distance=Math.hypot(moved.x-initial.x,moved.z-initial.z);
 const cameraChange=Math.abs(moved.yaw-initial.yaw);
 console.log('R12_REAL_TOUCH_JOYSTICK_MEASURE '+JSON.stringify({
   origin,initial,moved,distance,cameraChange}));
 if(distance<0.15||cameraChange>0.18){
   await page.screenshot({path:join(DIAG,'r12-joystick-failure.png'),fullPage:true}).catch(()=>{});
   throw Error('R12_STICK_STEERS_CAMERA_NOT_PLAYER '+JSON.stringify({distance,cameraChange,origin,initial,moved}));
 }
 // Native Dash button should feed exactly one HIGHFLY evade input edge,
 // not move the player client-side or spawn a new control owner.
 const dash=mobileHud.find(x=>x.id==='dash');
 const dashBefore=await page.evaluate(()=>window.__game.input.highflyEvadeSeq);
 await cdp.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{x:dash.cx,y:dash.cy,id:8}]});
 await cdp.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});
 await page.waitForTimeout(100);
 const dashAfter=await page.evaluate(()=>window.__game.input.highflyEvadeSeq);
 console.log('R12_NATIVE_DASH_EDGE '+JSON.stringify({dashBefore,dashAfter}));
 if(typeof dashBefore!=='number'||dashAfter!==dashBefore+1)
   throw Error('R12_DASH_BUTTON_NOT_BOUND_TO_NATIVE_EVADE');
 console.log('R12_S23_NATIVE_HUD_JOYSTICK_DASH_SMOKE_PASS');
 // R6 save is isolated by class + lowercased name. Trigger the actual
 // pagehide listener and prove persistence without deleting any user data.
 const saveReceipt=await page.evaluate(()=>{
   window.dispatchEvent(new Event('pagehide'));
   const key='highfly.rebirth044.offline.r6:warrior:rebirthtester';
   const raw=localStorage.getItem(key);
   let record=null;
   try{record=raw?JSON.parse(raw):null}catch{}
   return {key,stored:Boolean(raw),name:record?.name,cls:record?.cls,
     origin:record?.origin,level:record?.character?.level,
     savedAt:record?.savedAt,position:record?.character?.pos};
 });
 if(!saveReceipt.stored||saveReceipt.origin!=='highfly.rebirth044'||
    saveReceipt.cls!=='warrior'||saveReceipt.name!=='rebirthtester'||
    !(saveReceipt.level>=1))
   throw Error('R9_NATIVE_SAVE_MISSING '+JSON.stringify(saveReceipt));
 console.log('R9_NATIVE_OFFLINE_SAVE_WRITTEN '+JSON.stringify(saveReceipt));
 if(failures.length)throw Error('R9_WORLD_ASSET_ERRORS '+failures.slice(0,12).join(' | '));
 const missingAssets=missing.filter(p=>/\.(glb|ktx2|wasm|woff2?|png|webp)(\?|$)/.test(p));
 if(missingAssets.length)throw Error('R9_WORLD_404_ASSETS '+missingAssets.slice(0,12).join(','));
 const result={result:'PASS',classes:classCount,previewGLBRequests:glbs.length,
   total3DRequests:network.length,playableWorld:true,s23Physical:'PENDING',
   runUrl:url,errors:failures.length,saveKey:saveReceipt.key,saveChecked:true};
 console.log('R9_BROWSER_REAL_PREVIEW_AND_WORLD_PASS '+JSON.stringify(result));
 await context.close();
}finally{
 if(browser)await browser.close();
 await new Promise(ok=>server.close(ok));
}
