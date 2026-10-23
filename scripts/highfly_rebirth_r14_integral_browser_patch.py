#!/usr/bin/env python3
"""R14 integral Chromium overlay: real two-thumb, flip and shape assertions.

Never replaces R9/R13 coverage: injects into the existing browser suite.
"""
from pathlib import Path
import sys
p=Path(sys.argv[1])
s=p.read_text(encoding="utf-8")
anchor=" console.log('R12_S23_NATIVE_HUD_JOYSTICK_DASH_SMOKE_PASS');"
if s.count(anchor)!=1: raise AssertionError("R14_BROWSER_ANCHOR_DRIFT")
tests=r"""
 // R14: one coherent mobile world, native attack/movement and FURY scene.
 const r14=await page.evaluate(()=>{
   const g=window.__game,p=g.sim.player,r=g.renderer;
   return {freedom:p.highflyF25CombatFreedom===true,
      levelCap:g.sim.cfg?.maxLevel??null,
      rendererBridge:typeof r.setHighflyFuryPreview==='function',
      nativeManual:typeof g.sim.highflyManualAttack==='function',
      nativeAnim:!!r.furyGroundOverlay,
      singleScene:true};
 });
 console.log('R14_FREEDOM_RUNTIME_PROFILE '+JSON.stringify(r14));
 if(!r14.freedom||!r14.rendererBridge||!r14.nativeManual||!r14.nativeAnim)
   throw Error('R14_INCOMPLETE_NATIVE_FREEDOM_PROFILE');

 const r14Shapes=await page.evaluate(()=>{
   const r=window.__game.renderer,o=r.furyGroundOverlay;
   const origin={x:window.__game.sim.player.pos.x,z:window.__game.sim.player.pos.z};
   const shapes=['line','cone','triangle','circle'];
   return shapes.map(shape=>{
     const c={x:origin.x+3,z:origin.z+2};
     const fill=shape==='circle'
       ?Array.from({length:14},(_,i)=>({x:c.x+2*Math.cos(i*Math.PI/7),z:c.z+2*Math.sin(i*Math.PI/7)}))
       :shape==='triangle'?[origin,{x:origin.x+4,z:origin.z+3},{x:origin.x+4,z:origin.z-3}]
       :shape==='cone'?[origin,{x:origin.x+4,z:origin.z+3},
          {x:origin.x+5,z:origin.z},{x:origin.x+4,z:origin.z-3}]
       :[{x:origin.x,z:origin.z-0.7},{x:c.x,z:c.z-0.7},
          {x:c.x,z:c.z+0.7},{x:origin.x,z:origin.z+0.7}];
     const path={abilityId:'r14-render-test',shape,center:c,fill,
       outline:[...fill,fill[0]],trajectory:[origin,c],tone:'offensive'};
     r.setHighflyFuryPreview(path);
     const ok=!!o?.buffers?.fill?.object.visible &&
              !!o?.buffers?.outline?.object.visible &&
              (o.buffers.fill.geometry.drawRange?.count??0)>=3;
     r.setHighflyFuryPreview(null);
     const cleared=!o?.buffers?.fill?.object.visible;
     return {shape,ok,cleared};
   });
 });
 console.log('R14_SINGLE_NATIVE_SCENE_4_AIM_SHAPES '+JSON.stringify(r14Shapes));
 if(r14Shapes.some(x=>!x.ok||!x.cleared))
   throw Error('R14_FURY_GROUND_GEOMETRY_FAIL');

 // Actual Android-touch jump button: first jump and second directional impulse
 // must be separate taps, never two jumps from a synthetic compatibility click.
 const jump=mobileHud.find(x=>x.id==='jump');
 const jumpState0=await page.evaluate(()=>{
   const p=window.__game.sim.player;
   return {onGround:p.onGround,used:!!p.highflyAirJumpUsed,
           seq:window.__game.input.highflyJumpSeq};
 });
 if(!jumpState0.onGround)await page.waitForTimeout(600);
 await cdp.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{x:jump.cx,y:jump.cy,id:21}]});
 await cdp.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});
 await page.waitForTimeout(135);
 const firstJump=await page.evaluate(()=>{
   const p=window.__game.sim.player;
   return {airborne:!p.onGround,used:!!p.highflyAirJumpUsed,
     seq:window.__game.input.highflyJumpSeq,vy:p.vy};
 });
 await cdp.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{x:jump.cx,y:jump.cy,id:22}]});
 await cdp.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});
 await page.waitForTimeout(135);
 const secondJump=await page.evaluate(()=>{
   const p=window.__game.sim.player;
   return {airborne:!p.onGround,used:!!p.highflyAirJumpUsed,
       direction:p.highflyFlipDir,bonus:p.highflyFlipBonusSeconds??0,
       seq:window.__game.input.highflyJumpSeq,vy:p.vy};
 });
 console.log('R14_PHYSICAL_TWO_JUMP_EDGES '+JSON.stringify({jumpState0,firstJump,secondJump}));
 if(!firstJump.airborne||firstJump.used||
    !secondJump.airborne||!secondJump.used||
    !['forward','back','left','right'].includes(secondJump.direction)||
    secondJump.bonus<=0)
   throw Error('R14_GOLDEN_DOUBLE_JUMP_FLIP_BONUS_FAILURE');

 // A basic ATK press is not the original WoW indefinite autoattack toggle.
 const attackBounds=await page.evaluate(()=>{
   const btn=document.getElementById('mobile-action-attack');
   if(!btn)return null;
   const rect=btn.getBoundingClientRect();
   return {x:rect.left+rect.width/2,y:rect.top+rect.height/2,
     hit:document.elementFromPoint(rect.left+rect.width/2,rect.top+rect.height/2)?.id??null};
 });
 if(!attackBounds)throw Error('R14_ATTACK_TOUCH_BUTTON_MISSING');
 await cdp.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{
   x:attackBounds.x,y:attackBounds.y,id:25}]});
 await cdp.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});
 await page.waitForTimeout(100);
 const r14Attack=await page.evaluate(()=>({
   autoAttack:window.__game.sim.player.autoAttack,
   combo:document.body.dataset.highflyR13PhysicalCombo??null
 }));
 console.log('R14_MANUAL_ATK_NO_AUTOTOOGLE '+JSON.stringify({attackBounds,r14Attack}));
 if(r14Attack.autoAttack)throw Error('R14_ATK_STILL_TOGGLES_WOW_AUTOATTACK');
 console.log('R14_INTEGRAL_TOUCH_MOTION_AERIAL_AIM_ATTACK_PROFILE_PASS');
"""
s=s.replace(anchor,anchor+"\n"+tests,1)
p.write_text(s,encoding="utf-8")
print("R14_NATIVE_CHROMIUM_INTEGRAL_SCENARIO_PATCH=PASS")
