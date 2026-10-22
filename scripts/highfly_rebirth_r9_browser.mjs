#!/usr/bin/env node
/**
 * R9 in-browser gate. Opens built GitHub Pages-shaped app with a fresh mobile
 * profile, waits for a real GLB-backed native creator and completes world boot.
 * A green static build alone is insufficient.
 */
import { createServer } from 'node:http';
import { createReadStream, existsSync, statSync } from 'node:fs';
import { resolve, join, extname, sep } from 'node:path';
import { chromium } from 'playwright';

const ROOT=resolve(process.cwd(),'dist');
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
   if(/\.(glb|ktx2|wasm)(\?|$)/.test(new URL(r.url()).pathname)){
     network.push({status:r.status(),path:new URL(r.url()).pathname});
     if(r.status()>=400)failures.push('ASSET HTTP '+r.status()+' '+r.url());
   }
 });
 page.on('console',m=>{
   const str=m.text();
   if(m.type()==='error'||(m.type()==='warning' && /webgl|ktx2|glb|character|preview|transcode|shader|wasm/i.test(str)))
     consoleIssues.push(m.type()+': '+str.slice(0,500));
   if(/asset load failed|missing file or bad GLB|Error: Failed to fetch/i.test(str))
     failures.push('BROWSER '+str.slice(0,300));
 });
 const url='http://127.0.0.1:4187'+PREFIX+'/?hfRebirth=1&lang=es';
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
       pageText:document.body.innerText.slice(-900)};
   });
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
 await page.locator('#char-name').fill('R9AuditHunter');
 await page.locator('#btn-start-offline').click();
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
       assetError:visible('#asset-error'),
       allCanvases:[...document.querySelectorAll('canvas')].map(x=>({
         id:x.id,parent:x.parentElement?.id,width:x.width,height:x.height})),
       storageKeys:localStorageKeys,bodyText:document.body.innerText.slice(-1100)};
   });
   const payload={reason,state,networkTail:network.slice(-45),errors:failures.slice(-30),
     consoleIssues:consoleIssues.slice(-35),requestFailures:requestFailures.slice(-24),
     serverMissing:missing.slice(-30)};
   console.error('R9_WORLD_FORENSICS '+JSON.stringify(payload));
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
 if(failures.length)throw Error('R9_WORLD_ASSET_ERRORS '+failures.slice(0,12).join(' | '));
 const missingAssets=missing.filter(p=>/\.(glb|ktx2|wasm|woff2?|png|webp)(\?|$)/.test(p));
 if(missingAssets.length)throw Error('R9_WORLD_404_ASSETS '+missingAssets.slice(0,12).join(','));
 const result={result:'PASS',classes:classCount,previewGLBRequests:glbs.length,
   total3DRequests:network.length,playableWorld:true,s23Physical:'PENDING',
   runUrl:url,errors:failures.length};
 console.log('R9_BROWSER_REAL_PREVIEW_AND_WORLD_PASS '+JSON.stringify(result));
 await context.close();
}finally{
 if(browser)await browser.close();
 await new Promise(ok=>server.close(ok));
}
