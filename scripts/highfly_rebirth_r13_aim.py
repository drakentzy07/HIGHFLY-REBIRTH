#!/usr/bin/env python3
"""R13 FURY position-AoE touch PILOT, off outside HIGHFLY rebirth + hfFury.

Uses the EXISTING radial gesture pointer ownership and the EXISTING renderer/Sim.
Never claims all skills, changes native ability definitions, or adds a canvas.
"""
from pathlib import Path
import sys
if len(sys.argv)!=2: raise SystemExit("usage: highfly_rebirth_r13_aim.py CANDIDATE")
root=Path(sys.argv[1]).resolve()
def edit(path, changes):
    p=root/path
    s=p.read_text(encoding="utf-8")
    for tag,old,new in changes:
        n=s.count(old)
        if n!=1: raise AssertionError("R13_AIM_ANCHOR "+path+" "+tag+" count="+str(n))
        s=s.replace(old,new,1)
    p.write_text(s,encoding="utf-8")
    print("R13_AIM_PATCH",path,len(changes))

edit("src/ui/hud/action_bar/radial_gesture_controller.ts",[
 ("deps",
  """  /** The player opened the radial and chose nothing. */
  onCancel(): void;""",
  """  /** Optional HIGHFLY native-position skill drag, using THIS pointer router. */
  furySkill?: {
    begin(buttonIndex:number, event:PointerEvent, button:HTMLElement):boolean;
    move(event:PointerEvent):boolean;
    release(event:PointerEvent):boolean;
    cancel(pointerId:number):boolean;
  };
  /** The player opened the radial and chose nothing. */
  onCancel(): void;"""),
 ("cancel_pointer",
  """btn.addEventListener('pointercancel', (e) => this.clearDrag((e as PointerEvent).pointerId));""",
  """btn.addEventListener('pointercancel', (e) => {
        const id=(e as PointerEvent).pointerId;
        this.deps.furySkill?.cancel(id);
        this.clearDrag(id);
      });"""),
 ("lost_capture",
  """const release = (e: Event) => this.clearDrag((e as PointerEvent).pointerId);""",
  """const release = (e: Event) => {
      const id=(e as PointerEvent).pointerId;
      this.deps.furySkill?.cancel(id);
      this.clearDrag(id);
    };"""),
 ("begin",
  """  private onDown(e: PointerEvent, buttonIndex: number, btn: HTMLElement): void {
    if (this.drags.has(e.pointerId)) return;""",
  """  private onDown(e: PointerEvent, buttonIndex: number, btn: HTMLElement): void {
    if(this.deps.furySkill?.begin(buttonIndex,e,btn)){
      this.suppressClick=true;
      try{btn.setPointerCapture?.(e.pointerId)}catch{}
      if(e.pointerType==='touch')e.preventDefault();
      return;
    }
    if (this.drags.has(e.pointerId)) return;"""),
 ("move",
  """  private onMove(e: PointerEvent): void {
    const d = this.drags.get(e.pointerId);""",
  """  private onMove(e: PointerEvent): void {
    if(this.deps.furySkill?.move(e))return;
    const d = this.drags.get(e.pointerId);"""),
 ("release",
  """  private onUp(e: PointerEvent): void {
    const d = this.drags.get(e.pointerId);""",
  """  private onUp(e: PointerEvent): void {
    if(this.deps.furySkill?.release(e)){
      this.suppressClick=true;
      return;
    }
    const d = this.drags.get(e.pointerId);"""),
])

edit("src/ui/hud/action_bar/mobile_action_ring_controller.ts",[
 ("delegate_type",
  """  attackNearest: (() => void) | null;
  attackTapState(): { autoAttack: boolean; hasLiveHostileTarget: boolean };""",
  """  attackNearest: (() => void) | null;
  /** For the native FURY AoE pilot; the existing radial owns pointers. */
  furySkillGesture?(phase:'begin'|'move'|'release'|'cancel',abilityId:string|null,
    pointerId:number,at:{x:number;y:number},center:{x:number;y:number}):boolean;
  attackTapState(): { autoAttack: boolean; hasLiveHostileTarget: boolean };"""),
 ("delegate_wiring",
  """    buttons: slotBtns,
    // Hud's shared facet""",
  """    buttons: slotBtns,
    furySkill: {
      begin:(i,e,btn)=>{
        if(e.pointerType!=='touch'||!document.body.classList.contains('hf-rebirth-r2')||
           deps.bindModeActive()||
           deps.empoweredAbilityIdForSlot(deps.sourceSlot(i,'center'))!==null)return false;
        const ability=deps.abilityForSlot(deps.sourceSlot(i,'center'));
        // No targeting conversion for enemy/friendly/self, no counterfeit reticles.
        if(!ability||ability.def.targetMode!=='position')return false;
        const b=btn.getBoundingClientRect();
        return deps.furySkillGesture?.('begin',ability.def.id,e.pointerId,
          {x:e.clientX,y:e.clientY},{x:b.x+b.width/2,y:b.y+b.height/2})??false;
      },
      move:e=>deps.furySkillGesture?.('move',null,e.pointerId,
        {x:e.clientX,y:e.clientY},{x:0,y:0})??false,
      release:e=>deps.furySkillGesture?.('release',null,e.pointerId,
        {x:e.clientX,y:e.clientY},{x:0,y:0})??false,
      cancel:id=>deps.furySkillGesture?.('cancel',null,id,
        {x:0,y:0},{x:0,y:0})??false,
    },
    // Hud's shared facet"""),
])

edit("src/ui/hud.ts",[
 ("host_property",
  """  onMobileAttackNearest: (() => void) | null = null;""",
  """  onMobileAttackNearest: (() => void) | null = null;
  onHighflyFurySkillGesture: ((
    phase:'begin'|'move'|'release'|'cancel',abilityId:string|null,
    pointerId:number,at:{x:number;y:number},center:{x:number;y:number}
  )=>boolean)|null = null;"""),
 ("host_callback",
  """      attackNearest: this.onMobileAttackNearest,
      attackTapState: () => {""",
  """      attackNearest: this.onMobileAttackNearest,
      furySkillGesture:(phase,abilityId,pointerId,at,center)=>
        this.onHighflyFurySkillGesture?.(phase,abilityId,pointerId,at,center)??false,
      attackTapState: () => {"""),
])

edit("src/main.ts",[
 ("import_adapter",
  """import { FuryComboClock } from './highfly/fury/fury_core';""",
  """import { FuryComboClock } from './highfly/fury/fury_core';
import { FuryRebirthAdapter } from './highfly/fury/rebirth_adapter';"""),
 ("install_adapter",
  """  const highflyR13Combo = new FuryComboClock();
  hud.onMobileAttackNearest = () => attackNearest();""",
  """  const highflyR13Combo = new FuryComboClock();
  hud.onMobileAttackNearest = () => attackNearest();
  // Pilot: native position-ground AoE only, original class/skill state retained.
  // Uses the single native radial owner, native reticle, and Sim cast API.
  const highflyR13Fury = offlineSim &&
    document.body.classList.contains('hf-rebirth-r2') &&
    import.meta.env.VITE_HIGHFLY_FURY360 === '1' &&
    new URLSearchParams(location.search).get('hfFury') === '1'
    ? new FuryRebirthAdapter({
        readContext:()=>({
          player:{x:world.player.pos.x,z:world.player.pos.z},
          cameraYaw:input.camYaw,
        }),
        findKnownAbility:(id)=>{
          const known=offlineSim.known.find(k=>k.def.id===id);
          if(!known)return null;
          return {
            id:known.def.id,range:known.def.range,
            requiresTarget:!!known.def.requiresTarget,
            targetMode:known.def.targetMode==='position'?'position':undefined,
            targetType:known.def.targetType==='friendly'?'friendly':
                       known.def.targetType==='enemy'?'enemy':'any',
            selfCentered:!!known.def.selfCentered,
            effects:(known.effects??known.def.effects??[]).map(e=>({
              type:e.type,
              radius:'radius' in e&&typeof e.radius==='number'?e.radius:undefined,
            })),
          };
        },
        tryNativeSkill:(intent)=>{
          // 'true' means only submitted, never implies impact/resource spending.
          offlineSim.castAbilityAt(intent.abilityId,intent.world);
          return true;
        },
        nativeBasicAttackAllowed:()=>false,
        tryNativeBasicAttack:()=>false,
        renderGroundPreview:(geometry)=>{
          if(!geometry || geometry.shape!=='circle'){
            renderer.setGroundAimReticle(null);
            return;
          }
          const perimeter=geometry.outline[0];
          const radius=perimeter?Math.hypot(
            perimeter.x-geometry.center.x,perimeter.z-geometry.center.z):0;
          renderer.setGroundAimReticle(radius>0?{
            x:geometry.center.x,z:geometry.center.z,radius,
            school:'fire',dimmed:false,blocked:false,
          }:null);
        },
      }):null;
  hud.onHighflyFurySkillGesture=(phase,abilityId,pointerId,at,center)=>{
    const fury=highflyR13Fury;
    if(!fury)return false;
    if(phase==='begin')return !!abilityId&&
      fury.beginNativeSkill(pointerId,abilityId,center);
    if(phase==='move')return fury.moveNativeSkill(pointerId,at);
    if(phase==='release')return fury.releaseNativeSkill(pointerId,at)!=='ignored';
    return fury.cancelNativeSkill(pointerId);
  };"""),
])
print("R13_FURY_NATIVE_AOE_PILOT_INSTALLED_NOT_FULL_SKILL_CATALOG=PASS")
