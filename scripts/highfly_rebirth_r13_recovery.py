#!/usr/bin/env python3
"""HIGHFLY REBIRTH R13 / non-deploy candidate patch.

Patch the exact reconstructed ClaudeCraft v0.44.7 + R11/R12 source in CI.
Never touch persistent browser storage, main, production Pages or native GLBs.
Every source anchor must match ONCE. Fail closed on source drift.
"""
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit("usage: highfly_rebirth_r13_recovery.py CANDIDATE")
root = Path(sys.argv[1]).resolve()

def edit(path, replacements):
    p = root / path
    source = p.read_text(encoding="utf-8")
    for label, old, new in replacements:
        count = source.count(old)
        if count != 1:
            raise AssertionError("R13_ANCHOR_DRIFT " + path + " " + label + "=" + str(count))
        source = source.replace(old, new, 1)
    p.write_text(source, encoding="utf-8")
    print("R13_PATCH", path, len(replacements))

# 1. Save recovery. KEEP namespace isolation: R12 lab cannot overwrite R11.
save = "src/highfly/rebirth/offline_save.ts"
edit(save, [
    ("level_99", "s.level<=20&&Number.isFinite(s.xp)",
      "s.level<=99&&Number.isFinite(s.xp)"),
    ("safe_load",
     "const s:unknown=JSON.parse(raw);return validSlot(s,cls,name)?s:null;\n }catch{return null}",
     """const s:unknown=JSON.parse(raw);
  if(!validSlot(s,cls,name)){
   console.error('[HIGHFLY R13] Save exists but is invalid; original data preserved.', saveKey(cls,name));
   return null;
  }
  return s;
 }catch(err){console.error('[HIGHFLY R13] Save read failed; original data preserved.',err);return null}"""),
    ("durable_write",
     "try{localStorage.setItem(saveKey(cls,name),JSON.stringify(s));return true}catch{return false}",
     """try{
  const key=saveKey(cls,name),next=JSON.stringify(s);
  const previous=localStorage.getItem(key);
  // Preserve one untouched recovery snapshot (best effort: quota may be full).
  if(previous!==null && localStorage.getItem(key+'.r13-backup')===null){
   try{localStorage.setItem(key+'.r13-backup',previous)}
   catch(err){console.warn('[HIGHFLY R13] Backup quota warning',err)}
  }
  localStorage.setItem(key,next);
  if(localStorage.getItem(key)!==next)throw new Error('SAVE_VERIFY_READBACK_FAILED');
  return true;
 }catch(err){console.error('[HIGHFLY R13] Save write failed',err);return false}"""),
    ("protect_invalid_slot",
     """ active={sim,cls,name};
 if(listeners)return;""",
     """ // An invalid existing record is never overwritten with a fresh level-1
 // character. This guards future/legacy data as well as malformed JSON.
 try{
  const raw=localStorage.getItem(saveKey(cls,name));
  if(raw!==null && !validSlot(JSON.parse(raw),cls,name)){
   active=null;
   console.error('[HIGHFLY R13] Existing save quarantined in place. No overwrites.',saveKey(cls,name));
   return;
  }
 }catch(err){
  active=null;
  console.error('[HIGHFLY R13] Cannot inspect existing save; saving paused.',err);
  return;
 }
 active={sim,cls,name};
 if(listeners)return;"""),
    ("page_lifecycle",
     """window.addEventListener('pagehide',()=>{saveNow()});
 document.addEventListener('visibilitychange',()=>{if(document.visibilityState==='hidden')saveNow()});""",
     """window.addEventListener('pagehide',()=>{saveNow()});
 window.addEventListener('beforeunload',()=>{saveNow()});
 document.addEventListener('visibilitychange',()=>{if(document.visibilityState==='hidden')saveNow()});"""),
])

# 2. SINGLE manual melee/ranged strike using ClaudeCraft's own swing pipeline.
# Never use startAutoAttack() to drive continued swings from the ATK button.
edit("src/sim/sim.ts", [
    ("manual_native_strike",
     """  stopAutoAttack(pid?: number): void {
    stopAutoAttackImpl(this.ctx, pid);
  }

  private updatePlayerAutoAttack""",
     """  stopAutoAttack(pid?: number): void {
    stopAutoAttackImpl(this.ctx, pid);
  }

  /** HIGHFLY R13 offline-only one-shot basic attack. Native hit table,
   * reach, facing, weapon cadence, procs, LoS and cooldown remain authoritative.
   * The temporary autoAttack gate is closed before the NEXT sim tick.
   * True = native swing was ATTEMPTED, not proof of damage or contact. */
  highflyManualAttack(targetId: number | null): boolean {
    const p = this.player;
    const meta = this.players.get(p.id);
    p.autoAttack = false;
    if (!meta || p.dead || p.castingAbility || targetId === null) return false;
    const t = this.entities.get(targetId);
    if (!t || t.dead || !this.isHostileTo(p, t)) return false;
    p.targetId = targetId;
    const mainBefore = p.swingTimer;
    const offBefore = p.offhandSwingTimer;
    p.autoAttack = true;
    try {
      tryPlayerSwingImpl(this.ctx, p, meta);
    } finally {
      p.autoAttack = false;
    }
    return p.swingTimer > mainBefore || p.offhandSwingTimer > offBefore;
  }

  private updatePlayerAutoAttack"""),
])

# 3. REBIRTH-only ATK tap, while leaving WoC / desktop's classic attack alone.
edit("src/ui/hud/action_bar/mobile_action_ring_controller.ts", [
    ("manual_button",
     """    handleMobileAttackTap(deps.attackTapState(), {
      activateAttack: () => deps.activateFixedAttackSlot(),
      attackNearest: deps.attackNearest,
    });""",
     """    if (document.body.classList.contains('hf-rebirth-r2') && deps.attackNearest) {
      // HIGHFLY ATK is an intentional single press, never a WoW toggle.
      deps.attackNearest();
    } else {
      handleMobileAttackTap(deps.attackTapState(), {
        activateAttack: () => deps.activateFixedAttackSlot(),
        attackNearest: deps.attackNearest,
      });
    }"""),
])

edit("src/main.ts", [
    ("combo_import",
     "import { Sim } from './sim/sim';",
     "import { Sim } from './sim/sim';\nimport { FuryComboClock } from './highfly/fury/fury_core';"),
    ("combo_clock",
     """  hud.onMobileAttackNearest = () => attackNearest();""",
     """  const highflyR13Combo = new FuryComboClock();
  hud.onMobileAttackNearest = () => attackNearest();"""),
    ("manual_button_command",
     """    if (best === null) {
      hud.showError(t('errors.noEnemyNearby'));
      return;
    }
    world.targetEntity(best);
    world.startAutoAttack();
  }""",
     """    if (document.body.classList.contains('hf-rebirth-r2') && offlineSim) {
      if (best !== null) {
        const enemy = world.entities.get(best);
        if (enemy) {
          const dx = enemy.pos.x - p.pos.x, dz = enemy.pos.z - p.pos.z;
          // Native melee arc requires facing; never rotate the camera.
          if (Math.hypot(dx, dz) > 0.001) p.facing = Math.atan2(dx, dz);
        }
        world.targetEntity(best);
      }
      const attempted = offlineSim.highflyManualAttack(best);
      if (attempted) {
        // Native attempt ≠ guaranteed hit; Rogue class combo POINTS stay native.
        const step = highflyR13Combo.registerAcceptedHit(performance.now(), 2400, 4);
        document.body.dataset.highflyR13PhysicalCombo = String(step);
      }
      // A targetless press never opens autoattack or displays invalid-target.
      // An animation-only unarmed swing still requires validated GLB clips.
      return;
    }
    if (best === null) {
      hud.showError(t('errors.noEnemyNearby'));
      return;
    }
    world.targetEntity(best);
    world.startAutoAttack();
  }"""),
])

# 4. Runtime testable version stamp, no declaration of full Fury completion.
version = root / "public" / "highfly-r13-status.json"
version.write_text('{"version":"R13_RECOVERY_CANDIDATE","saveLevelCap":99,'
                   '"r11SaveNamespacePreserved":true,"manualNativeBasicAttack":true,'
                   '"physicalFourClipComboComplete":false,'
                   '"dragSkillIntegrated":false,"androidVerified":false}\n',
                   encoding="utf-8")
print("R13_SAFETY no publication, no save migration, no GLB writes")
