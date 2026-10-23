#!/usr/bin/env python3
"""R12 GOLDEN: left stick may TURN the character but never forcibly orbit camera.

The native WoW camera-follow springs player yaw toward camYaw and makes an
action joystick feel like a camera stick. In REBIRTH touch, both hands need
independent ownership. Keeps all native camera yaw/right-finger input as-is.
"""
from pathlib import Path
import sys
p=Path(sys.argv[1])/"src/main.ts"
s=p.read_text()
old="""    prevPlayerDead = playerDead;
    prevPlayerGhost = playerGhost;
    const next = updateFollowCameraYaw({"""
new="""    prevPlayerDead = playerDead;
    prevPlayerGhost = playerGhost;
    // R12: GOLDEN independent right-finger camera. The left radial joystick
    // already feeds a camera-relative WORLD vector through resolveFreedom360.
    // Do NOT turn that facing into a camera rotation. Resync the follow angle
    // so toggling interface-mode cannot later cause a yaw snap.
    if (document.body.classList.contains('hf-rebirth-r2') &&
        input.isHighflyMobileCameraDecoupled()) {
      lastInterpFacing = interpFacing;
      return;
    }
    const next = updateFollowCameraYaw({"""
if s.count(old)!=1:raise AssertionError("R12_GOLDEN_CAMERA_FOLLOW_ANCHOR_DRIFT "+str(s.count(old)))
p.write_text(s.replace(old,new))
print("R12_GOLDEN_LEFT_STICK_CAMERA_DECOUPLING_PASS")
