#!/usr/bin/env python3
"""R14 HIGHFLY FURY 360°: join GOLDEN locomotion to native damage, casting and visuals.

Called AFTER R13 recovery + FURY ground aim scripts in a scratch candidate.
All changes are fenced by hf-rebirth-r2 / the offline Sim and exact source
anchors. This is not a third physics engine and does not change base classes.
"""
from pathlib import Path
import sys, json
if len(sys.argv)!=2: raise SystemExit("Usage: highfly_rebirth_r14_freedom.py candidate")
root=Path(sys.argv[1]).resolve()
def edit(path,replacements):
    file=root/path
    source=file.read_text(encoding="utf-8")
    for name,old,new in replacements:
        count=source.count(old)
        if count!=1: raise AssertionError("R14_SOURCE_DRIFT "+path+" "+name+"="+str(count))
        source=source.replace(old,new,1)
    file.write_text(source,encoding="utf-8")
    print("R14_PATCH",path,len(replacements))

# A) Resolve the *physical* gesture as one action. Pointerdown is immediate;
# the browser's delayed synthetic touch click must NEVER fire Dash again.
# Mouse and keyboard click remain independently operable.
edit("src/game/mobile_controls.ts",[
 ("touch_click_native_edge",
  """      button.addEventListener('click', (e) => {
        if (suppressNextClick) {
          suppressNextClick = false;
          e.preventDefault();
          return;
        }
        run(e);
      });
      return;""",
  """      button.addEventListener('click', (e) => {
        // HIGHFLY: primary touch browsers can deliver a delayed compatibility
        // click after the 700-ms timer. Pointer identity, NOT a debounce clock,
        // owns Dash. Mouse/keyboard retain the normal click path.
        if ((id === 'mobile-evade' || id === 'mobile-jump') &&
            (e as PointerEvent).pointerType === 'touch') {
          suppressNextClick = false;
          e.preventDefault();
          return;
        }
        if (suppressNextClick) {
          suppressNextClick = false;
          e.preventDefault();
          return;
        }
        run(e);
      });
      return;"""),
])

# The old R13 180ms wall-clock filter could swallow legitimate distinct inputs.
# Native Sim already gates stamina and 0.55-second evade cooldown.
edit("src/game/input.ts",[
 ("remove_stale_timer_field",
  "  private highflyLastEvadePressAt = -Infinity;\n",
  ""),
 ("evade_press_one_native_edge",
  """  triggerHighflyEvade(): void {
    const now=performance.now();
    if(now-this.highflyLastEvadePressAt<180)return;
    this.highflyLastEvadePressAt=now;
    this.highflyEvadeSeq += 1;
  }""",
  """  triggerHighflyEvade(): void {
    this.highflyEvadeSeq += 1;
  }"""),
])

# B) Enable mobile freedom ONLY on a real REBIRTH offline character. Training,
# quest state, class skills, native physics, GCD and save schema stay unchanged.
edit("src/main.ts",[
 ("freedom_local_only",
  """  const highflyR13Combo = new FuryComboClock();""",
  """  // One local action-body profile: do not alter online/other class players.
  if(offlineSim && document.body.classList.contains('hf-rebirth-r2')){
    offlineSim.player.highflyF25CombatFreedom = true;
    offlineSim.player.highflyF261Controls = true;
  }
  const highflyR13Combo = new FuryComboClock();"""),
])

# Native caster movement checker is the SAME checker used by cast admission
# and mid-cast interruption. We do not overwrite each ability's castTime, cost,
# cooldown, targeting, GCD, or animated effect.
edit("src/sim/combat/cast_move_gate.ts",[
 ("movement_cast_native",
  """    resolved.def.castWhileMoving ||
      resolved.castWhileMoving ||""",
  """    // Opt-in HIGHFLY body: moving must not cancel a valid original spell.
    // Invalid abilities are still rejected by the native cast admission.
    p.highflyF25CombatFreedom === true ||
    resolved.def.castWhileMoving ||
      resolved.castWhileMoving ||"""),
])

# C) Directional second jump is PHYSICALLY authorized by the existing Sim.
# Reward next successfully damaging native physical attack or spell ONE TIME.
# A miss, preview, failed cast, or mere somersault cannot grant damage.
edit("src/sim/types.ts",[
 ("second_jump_bonus_state",
  """  highflyFlipDir?: "forward"|"back"|"left"|"right";""",
  """  highflyFlipDir?: "forward"|"back"|"left"|"right";
  /** R14 time-limited 12% damage bonus after an approved directional flip.
   * Runtime-only, absent in serialized saves; one successful native hit consumes. */
  highflyFlipBonusSeconds?: number;"""),
])
edit("src/sim/player_motion.ts",[
 ("flip_bonus_tick",
  """  if (p.onGround) p.highflyAirJumpUsed = false;""",
  """  if (p.onGround) p.highflyAirJumpUsed = false;
  if((p.highflyFlipBonusSeconds??0)>0)
    p.highflyFlipBonusSeconds=Math.max(0,(p.highflyFlipBonusSeconds??0)-DT);"""),
 ("native_second_jump_bonus",
  """    p.highflyAirJumpUsed = true;
  }
  if (!p.onGround) {""",
  """    // Only HIGHFLY's actual SECOND impulse grants the bonus, never an input
    // without sufficient stamina/clearance and never the first jump.
    if(p.highflyF25CombatFreedom === true) p.highflyFlipBonusSeconds=2.5;
    p.highflyAirJumpUsed = true;
  }
  if (!p.onGround) {"""),
])
edit("src/sim/sim.ts",[
 ("actual_damage_consumes_flip_buff",
  """  ): number {
    return dealDamageImpl(
      this.ctx,
      source,
      target,
      amount,
      crit,
      school,
      ability,
      kind,
      noRage,""",
  """  ): number {
    // HIGHFLY R14: one confirmed real native damaging event (physical or
    // original spell) consumes the flip follow-up. No preview/combo clock can
    // invent hits. Preserve all original damage-resolution and aggro rules.
    if(source?.highflyF25CombatFreedom===true &&
       (source.highflyFlipBonusSeconds??0)>0 &&
       target.kind==='mob' && !target.dead && amount>0 &&
       kind==='hit') {
      amount=Math.ceil(amount*1.12);
      source.highflyFlipBonusSeconds=0;
    }
    return dealDamageImpl(
      this.ctx,
      source,
      target,
      amount,
      crit,
      school,
      ability,
      kind,
      noRage,"""),
])

# D) Restore physically meaningful directional flip to the ONE native GLB rig,
# NOT a fake root-motion teleport. Both authored armor and equipped props spin.
# Renderer facts derive from the real Sim entity, not a second movement loop.
edit("src/render/characters/anim_state.ts",[
 ("anim_flip_data",
  """  airborne: boolean;
  /** Airborne AND genuinely falling""",
  """  airborne: boolean;
  /** R14 optional visual state for the real native second jump. */
  highflyAirFlip?: boolean;
  highflyFlipDir?: 'forward'|'back'|'left'|'right';
  /** Airborne AND genuinely falling"""),
])
edit("src/render/characters/anim_state_entity_core.ts",[
 ("anim_entity_shape",
  """  riftSliding?: boolean;
}""",
  """  riftSliding?: boolean;
  highflyF25CombatFreedom?: boolean;
  highflyAirJumpUsed?: boolean;
  highflyFlipDir?: 'forward'|'back'|'left'|'right';
}"""),
 ("anim_native_flip",
  """  st.combat = e.aggroTargetId !== null && !visuallyDead;""",
  """  st.combat = e.aggroTargetId !== null && !visuallyDead;
  st.highflyAirFlip = e.highflyF25CombatFreedom===true &&
    e.highflyAirJumpUsed===true && st.airborne && !visuallyDead;
  st.highflyFlipDir = e.highflyFlipDir;"""),
])
edit("src/render/characters/visual.ts",[
 ("flip_runtime_fields",
  """  private attackIdx = 0;""",
  """  // R14: presentation clock for the REAL second jump. Never moves entity.
  private highflyFlipWasActive = false;
  private highflyFlipSeconds = 0;
  private attackIdx = 0;"""),
 ("flip_clock",
  """  update(dt: number, s: AnimState, animate: boolean, reducedMotion = false): void {
    if (this.surfaceResponse.update(dt, this.root, this.height)) this.applyVisualMaterials();""",
  """  update(dt: number, s: AnimState, animate: boolean, reducedMotion = false): void {
    const nativeFlip = s.highflyAirFlip===true && !s.dead && !s.swimming;
    if(nativeFlip && !this.highflyFlipWasActive) this.highflyFlipSeconds=0;
    this.highflyFlipWasActive=nativeFlip;
    if(nativeFlip) this.highflyFlipSeconds=Math.min(.66,this.highflyFlipSeconds+dt);
    else this.highflyFlipSeconds=0;
    if (this.surfaceResponse.update(dt, this.root, this.height)) this.applyVisualMaterials();"""),
 ("full_directional_glb_flip",
  """    this.poseWrap.rotation.x =
      (proneAngle + swimPitch) * this.swimBlend + this.lean + CLIMB_BODY_PITCH * climb * climbLevel;
    this.poseWrap.rotation.z = 0;""",
  """    // Additive 360-degree pitch/roll, ending at the rest rotation. Direction
    // comes from actual joystick at second-jump impulse, not camera orbit.
    const phase=nativeFlip?Math.min(1,this.highflyFlipSeconds/.66):0;
    const angle=phase*2*Math.PI;
    const direction=s.highflyFlipDir??'forward';
    const flipPitch=direction==='forward'?angle:
                    direction==='back'?-angle:0;
    const flipRoll=direction==='left'?-angle:
                   direction==='right'?angle:0;
    this.poseWrap.rotation.x =
      (proneAngle + swimPitch) * this.swimBlend + this.lean + CLIMB_BODY_PITCH * climb * climbLevel +
      (reducedMotion?0:flipPitch);
    this.poseWrap.rotation.z = reducedMotion?0:flipRoll;"""),
])

# E) Existing FURY geom produces accurate line, cone, triangle, leap and
# circle polylines: expose it through the ONE native THREE scene. R12's
# FURYThreeGroundOverlay already creates/owns/disposes the GPU buffers.
edit("src/render/renderer.ts",[
 ("renderer_full_shape_bridge",
  """  setGroundAimReticle(
    aim: {""",
  """  /** R14: full native-host FURY footprint: never decides cast/damage. */
  setHighflyFuryPreview(preview: import('../highfly/fury/skill_preview').FuryGroundPreview|null): void {
    if(this.furyGroundOverlay){
      this.furyGroundOverlay.show(preview);
      if(preview)this.groundAimReticle.setAim(null);
    }
  }

  setGroundAimReticle(
    aim: {"""),
])
edit("src/main.ts",[
 ("render_all_ground_shapes",
  """        renderGroundPreview:(geometry)=>{
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
        },""",
  """        renderGroundPreview:(geometry)=>{
          // Native ONE scene: geometry owns accurate footprint visualization.
          // No fabricated cast or damage, cancel clears it immediately.
          renderer.setHighflyFuryPreview(geometry);
        },"""),
])

# F) Make the candidate self-describing (not a claim of 100% integration).
status=root/"public"/"highfly-r14-status.json"
status.write_text(json.dumps({
  "version":"R14_FREEDOM_INTEGRATION_CANDIDATE",
  "levelCap":20, "nineClassesPreserved":True,
  "singleNativeSim":True, "singleThreeScene":True,
  "manualNativeAttack":"R13",
  "movingSpells":"R14 opt-in native cast rules (original cast times)",
  "nativeSomersault":"R14 opt-in directional GLB presentation",
  "secondJumpBonus":"one accepted native hit, 12%",
  "aimVisual":"native position skills / authored FURY footprints",
  "comboFourClipsComplete":False,
  "treeClimb":"native ledges only; tree climbing unproven",
  "androidPhysicalVerified":False,
  "autoDeploy":False,
},indent=2)+"\n",encoding="utf-8")
print("R14_NATIVE_FREEDOM_PATCHES_APPLIED=PASS")
