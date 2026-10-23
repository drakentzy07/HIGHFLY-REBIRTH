#!/usr/bin/env python3
"""R16 STRICT HIGHFLY CORE: only training increases STR/AGI/VIT/PER/INT.

Levels continue normally in native ClaudeCraft gameplay: access, skills,
talents, unlocks and combat derived stats are NOT touched.
Armor/weapons affect native combat derived attributes but not Highfly Core.
70 training / 30 adventure is a BALANCE TARGET, not a fabricated live metric.
R11 remains byte-identical, and training save schema remains v5.
"""
from pathlib import Path
import json
import sys

if len(sys.argv)!=2:
    raise SystemExit("usage: highfly_rebirth_r16_progression.py <candidate>")
root=Path(sys.argv[1]).resolve()
p=root/"src/highfly/training/core.ts"
s=p.read_text(encoding="utf-8")
original="""  const normalizedLevel = clampHighflyNormalLevel(level);
  const totalGrowth =
    HIGHFLY_NATURAL_GROWTH_BUDGET *
    ((normalizedLevel - 1) / (HIGHFLY_NORMAL_MAX_LEVEL - 1));
  const weights = HIGHFLY_NATURAL_GROWTH_WEIGHTS[classId];
  const weightTotal = HIGHFLY_CORE_STATS.reduce((sum, stat) => sum + weights[stat], 0);
  if (weightTotal <= 0) return { ...ZERO_CORE_VECTOR };
  return Object.fromEntries(
    HIGHFLY_CORE_STATS.map((stat) => [
      stat,
      totalGrowth * (weights[stat] / weightTotal),
    ]),
  ) as HighflyCoreVector;"""
assert s.count(original)==1,"R16_TRAINING_CORE_LEVEL_DRIFT"
new="""  // R16 canonical HIGHFLY rule: XP and level NEVER mint permanent Training Core.
  // Level's combat effectiveness is computed in the original ClaudeCraft Sim
  // and unlocks/skills, NOT converted into STR/AGI/VIT/PER/INT points.
  // The frozen nine-class weights remain as archival donor data only.
  void classId;
  void level;
  return { ...ZERO_CORE_VECTOR };"""
s=s.replace(original,new,1)
assert s.count("return { ...ZERO_CORE_VECTOR };")>=1
p.write_text(s,encoding="utf-8")
# Ensure source-level files enforce separation; only HIGHFLY isolated profile
# stats are affected. NO recalcPlayerStats, network, economy or serialized
# ClaudeCraft character files change.
ui=root/"src/highfly/training/ui.ts"
t=ui.read_text(encoding="utf-8")
old='BASE DE CLASE + NIVEL + TRAINING · sólo TRAINING se asigna libremente'
new='BASE DE CLASE + TRAINING · el NIVEL no entrega Stats base'
assert t.count(old)==1,"R16_TRAINING_UI_CORE_DRIFT"
t=t.replace(old,new,1)
ui.write_text(t,encoding="utf-8")
status=root/"public/highfly-r16-status.json"
d=json.loads(status.read_text(encoding="utf-8"))
d.update({
 "coreStatsRule":"AWAKENING_BASE + REAL_TRAINING_ONLY",
 "adventureLevelsGrantPermanentCoreStats":False,
 "adventureLevelsStillUnlockNativeContent":True,
 "equipmentMayGrantDerivedAttributesOnly":True,
 "trainingPowerTarget":0.70,
 "adventurePowerTarget":0.30,
 "trainingPowerSplitDynamicallyEnforced":False,
 "combatBalancePhysicalS23Verified":False
})
status.write_text(json.dumps(d,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
print("R16_TRAINING_ONLY_PERMANENT_STATS_NO_NATIVE_SIM_MUTATION=PASS")
