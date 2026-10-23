#!/usr/bin/env python3
"""HIGHFLY REBIRTH R15 / precise opt-in native integration (no new Sim).

Runs AFTER R14 in CI. Protects v0.44.7 ability data, levels, specializations,
world, inventory, native resource costs and gameplay simulation.
Fail closed on every unexpected upstream source change.
"""
from pathlib import Path
import sys, json
if len(sys.argv)!=2:raise SystemExit("usage: highfly_rebirth_r15.py candidate")
root=Path(sys.argv[1]).resolve()
def edit(path,changes):
    p=root/path;s=p.read_text(encoding='utf8')
    for name,old,new in changes:
        count=s.count(old)
        if count!=1:raise AssertionError("R15_PATCH_DRIFT "+path+" "+name+"="+str(count))
        s=s.replace(old,new,1)
    p.write_text(s,encoding='utf8')
    print('R15_PATCH',path,len(changes))

# A. Character preview ownership: the original preview is initialized after
# async charactersReady. Our mobile entry may have ALREADY changed panels, so
# never leave the canvas at online-preview-container (currently hidden).
edit('src/main.ts',[
('creator_attach_after_async_asset',
"""        // If a token auto-login already rendered the roster and selected a
        // character before assets finished, show its real appearance; otherwise""",
"""        // R15: HIGHFLY's gate may switch to offline AFTER the async asset
        // decision. Always reattach the SAME WebGL canvas to the live panel;
        // do not create a second WebGL renderer or lose the current class.
        const hfPanel=document.getElementById('offline-select');
        if(hfPanel && !hfPanel.hasAttribute('hidden') &&
           (hfPanel.classList.contains('cs-wow') ||
            getComputedStyle(hfPanel).display!=='none')){
          updatePreviewContainer('#offline-select');
          requestAnimationFrame(()=>characterPreview?.syncSize());
        }
        // If a token auto-login already rendered the roster and selected a
        // character before assets finished, show its real appearance; otherwise"""),
('creator_preview_after_original',
"""    .catch((err: unknown) => {
      console.error('character preview assets failed to load, preview will stay blank:', err);
    });
}""",
"""    .catch((err: unknown) => {
      console.error('character preview assets failed to load, preview will stay blank:', err);
    });
  // R15: native player preview is a separate canvas from the world. Its
  // viewport can be zero during fullscreen transition, or owned by online
  // panel while HIGHFLY offline selector is active. Listen to panel entry and
  // orientation changes and REFIT the same existing CharacterPreview.
  const hfOffline=document.getElementById('offline-select');
  const hfReseat=()=>{
    if(!characterPreview||!hfOffline||
       hfOffline.hasAttribute('hidden')||
       getComputedStyle(hfOffline).display==='none')return;
    const c=document.getElementById('offline-preview-container');
    const canvas=document.getElementById('char-preview-canvas') as HTMLCanvasElement|null;
    if(!c||!canvas)return;
    if(canvas.parentElement!==c)updatePreviewContainer('#offline-select');
    characterPreview.syncSize();
    requestAnimationFrame(()=>characterPreview?.syncSize());
  };
  if(hfOffline){
    new MutationObserver(hfReseat).observe(hfOffline,{
      attributes:true,attributeFilter:['class','hidden','style']
    });
    window.addEventListener('resize',hfReseat,{passive:true});
    document.addEventListener('fullscreenchange',hfReseat);
    window.addEventListener('orientationchange',hfReseat,{passive:true});
    requestAnimationFrame(hfReseat);
    (window as Window & {__hfR15PreviewDiagnostics?:()=>object})
      .__hfR15PreviewDiagnostics=()=>{
        const c=document.getElementById('offline-preview-container');
        const canvas=document.getElementById('char-preview-canvas') as HTMLCanvasElement|null;
        return {mounted:!!characterPreview,
          attached:canvas?.parentElement===c,
          width:c?.clientWidth??0,height:c?.clientHeight??0,
          canvasWidth:canvas?.width??0,canvasHeight:canvas?.height??0,
          webglLost:canvas?.getContext('webgl2')?.isContextLost?.()??false,
          active:!!hfOffline&&!hfOffline.hasAttribute('hidden')};
      };
  }
}""")
])

# Native HUD labels the ACTUAL class resource. Never synthesize resource
# consumption or overwrite native unit-frame rendering.
edit('src/ui/hud.ts',[
('native_resource_label',
"""    playerFrame.resourceKind = p.resourceType;
    playerFrame.resFrac = p.resource / Math.max(1, p.maxResource);""",
"""    playerFrame.resourceKind = p.resourceType;
    // R15: annotate one existing class-resource bar. It remains fully owned
    // by the native unit-frame painter, including actual costs and regen.
    if(document.body.classList.contains('hf-rebirth-r2')){
      const labelHost=document.getElementById('pf-resource');
      if(labelHost){
        const kind=p.resourceType;
        const label=kind==='mana'?'MANÁ':kind==='energy'?'ENERGÍA':
                    kind==='rage'?'IRA':kind==='focus'?'CONCENTRACIÓN':'RECURSO';
        labelHost.dataset.highflyR15Resource=label;
        labelHost.dataset.highflyR15Available=String(Math.round(p.resource));
        labelHost.dataset.highflyR15Maximum=String(Math.round(p.maxResource));
      }
    }
    playerFrame.resFrac = p.resource / Math.max(1, p.maxResource);"""),
])

# B. Single native rig: the original animation mixer can run a base gait AND
# an overlay made only of native GLB arm/chest tracks. NO pelvis/leg/root tracks,
# so casts cannot accidentally plant feet or introduce unwanted translation.
module=root/'src/highfly/rebirth/r15_cast_mask.ts'
module.write_text("""/** R15: isolate the arm/chest pose from ClaudeCraft's already-loaded GLB cast clips.
 * Exact track names from Rig_Medium; never duplicate keyframes or movement authority.
 */
export function highflyR15IsUpperBodyTrack(path:string):boolean {
  if(!/\\\\.(?:quaternion|rotation)(?:\\\\[[^\\\\]]+\\\\])?$/.test(path))return false;
  return /(?:spine|chest|clavicle|shoulder|upperarm|lowerarm|forearm|rightarm|leftarm|wrist|hand|finger|thumb|neck|head|torso|arm_l|arm_r)/i.test(path);
}
export function highflyR15HasBodyMask(paths:readonly string[]):boolean{
  const arms=paths.filter(highflyR15IsUpperBodyTrack);
  return arms.length>=4 && arms.length<paths.length;
}
""",encoding='utf8')
# Advertise the presentation-only capability, deriving the gate from the Sim's
# actual live player flag (which R14 already enables on the local player).
edit('src/render/characters/anim_state.ts',[
 ('upper_body_cast_type',
  """  highflyFlipDir?: 'forward'|'back'|'left'|'right';""",
  """  highflyFlipDir?: 'forward'|'back'|'left'|'right';
  highflyFreeCast?: boolean;""")
])
edit('src/render/characters/anim_state_entity_core.ts',[
 ('upper_body_cast_entity',
  """  st.highflyFlipDir = e.highflyFlipDir;""",
  """  st.highflyFlipDir = e.highflyFlipDir;
  st.highflyFreeCast=e.highflyF25CombatFreedom===true && !visuallyDead;"""),
])
edit('src/render/characters/visual.ts',[
 ('import_cast_mask',
  """import * as THREE from 'three';""",
  """import * as THREE from 'three';
import { highflyR15IsUpperBodyTrack, highflyR15HasBodyMask } from '../../highfly/rebirth/r15_cast_mask';"""),
 ('cast_mask_fields',
  """  private highflyFlipWasActive = false;""",
  """  private highflyR15UpperCast: THREE.AnimationAction|null = null;
  private highflyR15MovingCast=false;
  private highflyFlipWasActive = false;"""),
 ('cast_mask_update',
  """  update(dt: number, s: AnimState, animate: boolean, reducedMotion = false): void {
    const nativeFlip =""",
  """  update(dt: number, s: AnimState, animate: boolean, reducedMotion = false): void {
    // Movement and casting both remain owned by native Sim. Overlay only the
    // upper body from native authored GLB tracks, not an unrelated animation.
    const wantsMoveCast=s.highflyFreeCast===true&&s.casting&&
      s.moving&&!s.dead&&!s.swimming&&!s.airborne;
    if(wantsMoveCast&&!this.highflyR15UpperCast){
      const src=this.action('Spellcast_Raise') ??
        this.action(this.def.clips.cast);
      if(src){
        const clip=src.getClip();
        const allPaths=clip.tracks.map(t=>t.name);
        if(highflyR15HasBodyMask(allPaths)){
          const tracks=clip.tracks.filter(t=>highflyR15IsUpperBodyTrack(t.name));
          const upper=new THREE.AnimationClip('hf_r15_upper_cast_'+this.def.clips.idle,
            clip.duration,tracks);
          this.highflyR15UpperCast=this.mixer.clipAction(upper);
        }
      }
    }
    const movingCast=wantsMoveCast&&this.highflyR15UpperCast!==null;
    if(movingCast&&!this.highflyR15MovingCast){
      this.highflyR15UpperCast!.reset()
        .setLoop(THREE.LoopRepeat,Infinity)
        .setEffectiveWeight(1).fadeIn(.09).play();
    }else if(!movingCast&&this.highflyR15MovingCast){
      this.highflyR15UpperCast?.fadeOut(.12);
    }
    this.highflyR15MovingCast=movingCast;
    const nativeFlip ="""),
 ('cast_mask_native_gait',
  """    return desiredBaseState(
      s,
      !!this.action(this.def.clips.walkBack),""",
  """    // HIGHFLY moves while a spell counts down: legs keep native walk/run
    // clip, not native planted 'cast'. All cooldowns, casting duration and
    // resource spend are unchanged, because this is renderer-only.
    const displayed = this.highflyR15MovingCast && s.casting
      ? {...s,casting:false} : s;
    return desiredBaseState(
      displayed,
      !!this.action(this.def.clips.walkBack),"""),
])

# C. Layout: one native ring and buttons, no second controls, no false skills.
# R12 positioned a two-row strip. R15 assigns a readable S23 932x430 action
# cluster, keeping its 4 real slot elements, passives, page switch and target.
css = r"""/* HIGHFLY R15 / responsive S23 landscape single native HUD */
@media (orientation:landscape) and (max-height:650px){
 body.mobile-touch.hf-rebirth-r2 #mobile-action-ring{
   position:fixed!important;inset:auto 0 0 auto!important;
   width:min(59vw,558px)!important;height:min(52vh,224px)!important;
   display:block!important;overflow:visible!important;
   background:transparent!important;pointer-events:none!important;z-index:130!important
 }
 body.mobile-touch.hf-rebirth-r2 #mobile-action-ring button{
   position:absolute!important;inset:auto!important;pointer-events:auto!important;
   display:flex!important;align-items:center!important;justify-content:center!important;
   width:clamp(40px,5.3vw,51px)!important;height:clamp(40px,5.3vw,51px)!important;
   border-radius:50%!important;touch-action:none!important
 }
 body.mobile-touch.hf-rebirth-r2 #mobile-action-ring #mobile-action-attack{
   right:14px!important;bottom:78px!important;width:74px!important;height:74px!important;
   border:2px solid #e6bd69!important;background:#303844f0!important;
   z-index:9!important;box-shadow:0 0 0 4px #121a27ab,0 0 16px #d6a64755!important
 }
 body.mobile-touch.hf-rebirth-r2 #mobile-action-ring .mobile-action-slot[data-mobile-index="0"]{
   right:96px!important;bottom:23px!important
 }
 body.mobile-touch.hf-rebirth-r2 #mobile-action-ring .mobile-action-slot[data-mobile-index="1"]{
   right:157px!important;bottom:65px!important
 }
 body.mobile-touch.hf-rebirth-r2 #mobile-action-ring .mobile-action-slot[data-mobile-index="2"]{
   right:160px!important;bottom:125px!important
 }
 body.mobile-touch.hf-rebirth-r2 #mobile-action-ring .mobile-action-slot[data-mobile-index="3"]{
   right:98px!important;bottom:163px!important
 }
 body.mobile-touch.hf-rebirth-r2 #mobile-action-ring #mobile-jump{
   right:269px!important;bottom:23px!important
 }
 body.mobile-touch.hf-rebirth-r2 #mobile-action-ring #mobile-evade{
   right:324px!important;bottom:23px!important
 }
 body.mobile-touch.hf-rebirth-r2 #mobile-action-ring #mobile-interact{
   right:22px!important;bottom:13px!important;
   width:45px!important;height:45px!important
 }
 body.mobile-touch.hf-rebirth-r2 #mobile-action-ring #mobile-target-cycle{
   right:16px!important;bottom:168px!important;
   width:42px!important;height:42px!important
 }
 body.mobile-touch.hf-rebirth-r2 #mobile-action-ring #hf-r12-passive{
   right:267px!important;bottom:132px!important
 }
 body.mobile-touch.hf-rebirth-r2 #mobile-action-ring #mobile-action-page-toggle{
   right:217px!important;bottom:81px!important;
   width:42px!important;height:42px!important;opacity:.8!important
 }
 body.mobile-touch.hf-rebirth-r2 #mobile-action-ring #mobile-consumable-seat{
   right:218px!important;bottom:15px!important;
   width:39px!important;height:39px!important
 }
 body.mobile-touch.hf-rebirth-r2 #mobile-action-ring #mobile-stance-anchor{
   right:374px!important;bottom:25px!important;
   width:43px!important;height:43px!important
 }
 body.mobile-touch.hf-rebirth-r2 #mobile-action-ring .mobile-label{
   font-size:9px!important;max-width:100%!important;text-align:center!important;
   line-height:1.1!important;white-space:normal!important
 }
 body.mobile-touch.hf-rebirth-r2 #pf-resource{
   position:relative!important;min-height:12px!important
 }
 body.mobile-touch.hf-rebirth-r2 #pf-resource::before{
   content:attr(data-highfly-r15-resource)!important;position:absolute!important;
   right:2px!important;top:0!important;font:bold 9px system-ui!important;
   color:#fff!important;text-shadow:0 1px 2px #000!important;
   z-index:8!important;pointer-events:none!important
 }
 body.mobile-touch.hf-rebirth-r2 #pf-hp,
 body.mobile-touch.hf-rebirth-r2 #pf-res{
   transition:width .08s linear!important
 }
 html.hf-r7 #offline-select #offline-preview-container{
   min-height:155px!important;flex:1 1 45%!important;
 }
 html.hf-r7 #offline-select #offline-preview-container canvas{
   display:block!important;width:100%!important;height:100%!important;
   visibility:visible!important;opacity:1!important
 }
}
"""
style=root/'src/highfly/rebirth/r15_style.css'
style.write_text(css,encoding='utf8')
edit('src/main.ts',[('r15_style_import',
"""import { Sim } from './sim/sim';""",
"""import { Sim } from './sim/sim';
import './highfly/rebirth/r15_style.css';""")])
manifest=root/'public/highfly-r15-status.json'
manifest.write_text(json.dumps({
 "version":"R15_HUD_CREATOR_NATIVE_MOVING_CAST",
 "levelCap":20,"originalClasses":9,
 "nativeResourceTypes":["mana","energy","rage","focus"],
 "nativeResourceBilling":True,
 "mobilityStaminaBar":"not fabricated; native resource bar only",
 "creator":"reactive shared WebGL canvas reattach; physical Android QA pending",
 "nativeSkillCastTimesPreserved":True,
 "movingCast":"masked upper body GLB + native locomotion if >=4 matching tracks",
 "hud":"4 real native skill buttons, ATK, jump, evade, use, target, passives",
 "fourPhysicalAttackClipsVerified":False,
 "allSkillAimingVerified":False,
 "s23PhysicalVerified":False,
 "productionR11Overwritten":False,
},indent=2,ensure_ascii=False)+'\n',encoding='utf8')
print('R15_NATIVE_HUD_RESOURCES_CREATOR_MOVING_CAST_PATCHED=PASS')
