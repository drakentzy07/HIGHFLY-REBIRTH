#!/usr/bin/env python3
"""R16: do NOT call a build GREEN unless native S23 player frame and More are real."""
from pathlib import Path
import sys
if len(sys.argv)!=2:raise SystemExit("usage: r16_browser_patch.py <browser.mjs>")
p=Path(sys.argv[1])
s=p.read_text(encoding="utf-8")
anchor="""   throw Error('R15_HUD_RESOURCE_NOT_READY '+JSON.stringify(r15HUD));
 }"""
assert s.count(anchor)==1, "R16_R15_BROWSER_ANCHOR_DRIFT "+str(s.count(anchor))
test=r"""
 const r16=await page.evaluate(()=>window.__hfR16VisualDiagnostics?.()??null);
 console.log('R16_NATIVE_TOP_HUD '+JSON.stringify(r16));
 if(!r16?.active||r16.playerFrameCount!==1||r16.nativeMoreCount!==1||
    !r16.originalMoreDialog||!r16.playerFrame||!r16.nativeMore||
    r16.playerFrame.x>40||r16.playerFrame.y>30||
    r16.nativeMore.x>45||r16.nativeMore.y>110||
    r16.nativeMore.width<43||r16.nativeMore.height<43)
   throw Error('R16_NATIVE_HUD_POSITION_WRONG '+JSON.stringify(r16));
 // This is the original ClaudeCraft More control, not a second fake button:
 // click it and require the original dialog body class + visible content.
 await page.locator('#mobile-more').click();
 const opened=await page.evaluate(()=>{
   const m=document.getElementById('mobile-extra-controls');
   if(!m)return false;
   const r=m.getBoundingClientRect(),s=getComputedStyle(m);
   return document.body.classList.contains('mobile-more-open') &&
     s.display!=='none'&&r.width>180&&r.height>120;
 });
 if(!opened)throw Error('R16_REAL_MORE_BUTTON_DID_NOT_OPEN_MODAL');
 await page.locator('#mobile-more-close').click();
 const closed=await page.evaluate(()=>!document.body.classList.contains('mobile-more-open'));
 if(!closed)throw Error('R16_REAL_MORE_DIALOG_DID_NOT_CLOSE');
 console.log('R16_NATIVE_SINGLE_TOP_FRAME_AND_MORE_CLICK=PASS');
"""
# Preserve R14's physical jump/attack order: opening a native modal before
# a held touch sequence can steal/focus a pointer on Chromium Android.
# Check R16 menu only AFTER every motion+save functional regression.
end_anchor=" if(failures.length)throw Error('R9_WORLD_ASSET_ERRORS '"
assert s.count(end_anchor)==1, "R16_END_TEST_ANCHOR_DRIFT "+str(s.count(end_anchor))
s=s.replace(end_anchor,test+"\n"+end_anchor,1)
# Retain actual S23-sized creator pixels and HUD screenshots for human QA.
creator_anchor="  const png=await page.locator('#offline-preview-container').screenshot({type:'png'});"
assert s.count(creator_anchor)==1,"R16_CREATOR_PNG_TEST_DRIFT"
s=s.replace(creator_anchor,creator_anchor+"\n  writeFileSync(join(DIAG,'r16-s23-creator.png'),png);",1)
open_anchor=" await page.locator('#mobile-more').click();"
assert s.count(open_anchor)==1,"R16_MENU_OPEN_TEST_DRIFT"
s=s.replace(open_anchor," await page.screenshot({path:join(DIAG,'r16-s23-world-hud.png'),fullPage:false});\n"+open_anchor,1)
# R16 lab-only: capture authoritative Sim/input state whenever
# Chromium misses the first real jump edge observation. Never spoof a jump.
jumpwait=""" await page.waitForFunction(()=>{
   const p=window.__game.sim.player;
   return p.highflyLastJumpSeq===1 && !p.onGround && p.jumping &&
          p.highflyAirJumpUsed!==true;
 },null,{timeout:2500,polling:25});"""
assert s.count(jumpwait)==1,"R16_JUMP_FIRST_CONTRACT_DRIFT "+str(s.count(jumpwait))
diagnosed=""" try {
 await page.waitForFunction(()=>{
   const p=window.__game.sim.player;
   return p.highflyLastJumpSeq===1 && !p.onGround && p.jumping &&
          p.highflyAirJumpUsed!==true;
 },null,{timeout:4500,polling:25});
 } catch(jumpError) {
   const state=await page.evaluate(()=>{
     const p=window.__game?.sim?.player,i=window.__game?.input;
     return {onGround:p?.onGround,jumping:p?.jumping,
       vy:p?.vy,used:p?.highflyAirJumpUsed,
       inputJumpSeq:i?.highflyJumpSeq,consumedSeq:p?.highflyLastJumpSeq,
       rooted:p?.rooted,stamina:p?.stamina,energy:p?.highflyVitals?.energy,
       highflyFreedom:p?.highflyF25CombatFreedom,
       bodyClasses:document.body.className,
       targetAtJump:document.elementFromPoint(640,386)?.id??null};
   });
   console.error('R16_FIRST_JUMP_RUNTIME_FORENSICS '+JSON.stringify(state));
   await page.screenshot({path:join(DIAG,'r16-first-jump-failure.png')});
   throw jumpError;
 }"""
s=s.replace(jumpwait,diagnosed,1)
# R16 native direct-Sim targetless basic attack safety gate.
# Run at the END, after original save/movement/Menu proof.
whiff_anchor=" if(failures.length)throw Error('R9_WORLD_ASSET_ERRORS '"
assert s.count(whiff_anchor)==1,"R16_WHIFf_TEST_INSERT_DRIFT"
whiff_test=r"""
 await page.waitForFunction(()=>!!window.__game?.sim?.player &&
   window.__game.sim.player.swingTimer<=0,null,{timeout:12000,polling:100});
 const r16Whiff=await page.evaluate(()=>{
   const sim=window.__game.sim,p=sim.player;
   const hpBefore=Array.from(sim.entities.values())
     .filter(e=>e.kind==='mob').map(e=>[e.id,e.hp]);
   const manaBefore=p.highflyVitals?.mana??null;
   const energyBefore=p.highflyVitals?.energy??null;
   const nativeBefore=p.resource;
   const accepted=sim.highflyManualAttack(null);
   const timer=p.swingTimer,autoAttack=p.autoAttack;
   const repeated=sim.highflyManualAttack(null);
   const hpAfter=Array.from(sim.entities.values())
     .filter(e=>e.kind==='mob').map(e=>[e.id,e.hp]);
   return {accepted,repeated,timer,autoAttack,
     hpUnchanged:JSON.stringify(hpBefore)===JSON.stringify(hpAfter),
     resourcesUnchanged:nativeBefore===p.resource &&
       manaBefore===(p.highflyVitals?.mana??null) &&
       energyBefore===(p.highflyVitals?.energy??null)};
 });
 console.log('R16_NATIVE_TARGETLESS_MANUAL_WHIFf '+JSON.stringify(r16Whiff));
 if(!r16Whiff.accepted||r16Whiff.repeated||r16Whiff.autoAttack||
   r16Whiff.timer<=0||!r16Whiff.hpUnchanged||!r16Whiff.resourcesUnchanged)
   throw Error('R16_INVALID_NATIVE_TARGETLESS_MANUAL_ATTACK '+JSON.stringify(r16Whiff));
"""
s=s.replace(whiff_anchor,whiff_test+"\n"+whiff_anchor,1)
p.write_text(s,encoding="utf-8")
print("R16_S23_ORIGINAL_MORE_AND_SINGLE_FRAME_BROWSER_ASSERTIONS_INSTALLED")
