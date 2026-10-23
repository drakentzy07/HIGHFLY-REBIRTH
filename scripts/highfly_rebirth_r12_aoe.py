#!/usr/bin/env python3
"""R12: first FURY visual-on-native-host bridge, flagged OFF by default.

Only decorates the EXISTING GroundAimController -> Renderer reticle path.
Never calls castAbilityAt, mutates native abilities, adds a canvas/tick loop,
or creates a second touch owner. No protected classes, saves, or resources.
"""
from pathlib import Path
import sys
p=Path(sys.argv[1])/"src/render/renderer.ts"
s=p.read_text()
def replace(old,new,tag):
 global s
 n=s.count(old)
 if n!=1:raise AssertionError("R12_AOE_ANCHOR_DRIFT_"+tag+"_"+str(n))
 s=s.replace(old,new)

replace("import * as THREE from 'three';",
"""import * as THREE from 'three';
import { FuryThreeGroundOverlay } from '../highfly/fury/three_ground_overlay';
import type { FuryThreeFacade } from '../highfly/fury/three_ground_overlay';
import { makeFurySkillPreview } from '../highfly/fury/skill_preview';""","imports")
replace("  private groundAimReticle: GroundAimReticleVisual;",
"""  private groundAimReticle: GroundAimReticleVisual;
  // FURY F2 uses the NATIVE scene; it is visualization ONLY. Default disabled.
  private furyGroundOverlay: FuryThreeGroundOverlay | null = null;""","field")
replace("    setRenderCategory(this.groundAimReticle.group, 'ui3d');",
"""    setRenderCategory(this.groundAimReticle.group, 'ui3d');
    // A/B switch: public R11 is unaffected without both the build flag and
    // explicit URL opt-in. Use native terrain and ONE shared Three scene.
    if (import.meta.env.VITE_HIGHFLY_FURY360 === '1' &&
        new URLSearchParams(location.search).get('hfFury') === '1' &&
        new URLSearchParams(location.search).get('hfRebirth') === '1') {
      this.furyGroundOverlay = new FuryThreeGroundOverlay({
        scene: this.scene,
        three: THREE as unknown as FuryThreeFacade,
        terrainHeightAt: (x, z) => groundHeight(x, z, this.sim.cfg.seed),
      });
    }""","initialize")
replace("  dispose(): void {\n    setBuildSpanSink(null);",
"""  dispose(): void {
    this.furyGroundOverlay?.dispose();
    this.furyGroundOverlay = null;
    setBuildSpanSink(null);""","dispose")
replace("""  ): void {
    this.groundAimReticle.setAim(
      aim
        ? {
            x: aim.x,
            z: aim.z,
            radius: aim.radius,""",
"""  ): void {
    // Reticle authority remains GroundAimController: x/z/radius arrive AFTER
    // the native range and terrain-placement checks. This previews only the
    // true native AoE radius; no extra cast, hitbox or resource manipulation.
    if (this.furyGroundOverlay) {
      if (aim && !aim.blocked && Number.isFinite(aim.radius) && aim.radius > 0) {
        const origin = { x: aim.x, z: aim.z };
        const spec = { abilityId: 'native-ground-area', shape: 'circle' as const,
          range: 0, radius: aim.radius };
        const intent = { abilityId: spec.abilityId, shape: 'circle' as const,
          world: origin, facing: 0, distance: 0, isTap: false };
        const geometry = makeFurySkillPreview(origin, intent, spec);
        if (geometry && this.furyGroundOverlay.show(geometry)) {
          this.groundAimReticle.setAim(null);
          return;
        }
      }
      this.furyGroundOverlay.hide();
    }
    this.groundAimReticle.setAim(
      aim
        ? {
            x: aim.x,
            z: aim.z,
            radius: aim.radius,""","native_reticle")
p.write_text(s)
print("R12_FURY_FIRST_NATIVE_AREA_PREVIEW_FLAGGED_OFF_BY_DEFAULT=PASS")
