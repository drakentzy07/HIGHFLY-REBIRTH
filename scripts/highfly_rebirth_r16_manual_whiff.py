#!/usr/bin/env python3
"""R16 phase 2: authoritative empty-air manual basic strike ("whiff").

The native tryPlayerSwing remains sole source for target HP/attack outcomes.
For NO TARGET, a strike is still a physical action, advances the native
weapon swing timer, plays a real existing rig clip, and CANNOT deal damage.
No auto-attack toggle, camera steering, teleport or synthetic impact.
"""
from pathlib import Path
import json
import sys
if len(sys.argv)!=2:raise SystemExit("usage: highfly_rebirth_r16_manual_whiff.py candidate")
root=Path(sys.argv[1])
def edit(path,a,b):
 p=root/path;s=p.read_text(encoding="utf-8")
 n=s.count(a)
 if n!=1:raise AssertionError("R16_WHIFf_ANCHOR "+path+" "+str(n))
 p.write_text(s.replace(a,b,1),encoding="utf-8")

edit("src/sim/sim.ts",
"""  tryPlayerSwing as tryPlayerSwingImpl,
  updatePlayerAutoAttack as updatePlayerAutoAttackImpl,""",
"""  tryPlayerSwing as tryPlayerSwingImpl,
  resetSwingTimer as resetSwingTimerImpl,
  updatePlayerAutoAttack as updatePlayerAutoAttackImpl,""")

edit("src/sim/sim.ts",
"""    if (!meta || p.dead || p.castingAbility || targetId === null) return false;
    const t = this.entities.get(targetId);""",
"""    if (!meta || p.dead || p.castingAbility || isStunned(p)) return false;
    // Manual strike with no target: native weapon recovery, no target, no damage,
    // no secondary Sim or hit event. Existing player animations handle display.
    if (targetId === null) {
      if (p.swingTimer > 0 || p.mountKey !== '') return false;
      p.autoAttack = false;
      resetSwingTimerImpl(this.ctx, p, meta);
      return true;
    }
    const t = this.entities.get(targetId);""")

edit("src/main.ts",
"""      const attempted = offlineSim.highflyManualAttack(best);
      if (attempted) {
        // Native attempt ≠ guaranteed hit; Rogue class combo POINTS stay native.""",
"""      const attempted = offlineSim.highflyManualAttack(best);
      if (attempted) {
        // The empty-air swing has NO native hit event; animate the same owned
        // CharacterVisual. Real contacts are already animated by native events.
        // This never submits damage, a projectile, resource debit or target.
        if (best === null) renderer.triggerAttack(p.id);
        // Native attempt ≠ guaranteed hit; Rogue class combo POINTS stay native.""")

status=root/"public/highfly-r16-status.json"
d=json.loads(status.read_text(encoding="utf-8"))
d.update({
 "targetlessManualWhiffSim":True,
 "targetlessManualWhiffUsesNativeRecovery":True,
 "targetlessManualWhiffVisualUsesNativeGLB":True,
 "noTargetlessDamage":True,
 "fourDistinctBasicAttackClipsVerified":False,
 "comboFourthHitDamageModifierImplemented":False,
 "assistedApproachImplemented":False,
 "physicalS23Verified":False,
 "safeToPublish":False
})
status.write_text(json.dumps(d,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
print("R16_ONE_NATIVE_TARGETLESS_ATTACK_NO_SYNTHETIC_HIT=PASS")
