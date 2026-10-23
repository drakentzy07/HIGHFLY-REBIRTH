#!/usr/bin/env python3
"""R16 Pages lab progress isolation: NO shared R11 Training or Vital saves.
The original R11 root is staged and SHA-frozen BEFORE applying this patch.
Never import an ambiguously shared old key into the new lab namespace.
"""
from pathlib import Path
import sys
if len(sys.argv)!=2:raise SystemExit("usage: highfly_rebirth_r16_lab_keys.py candidate")
root=Path(sys.argv[1])
for path,old,new in [
 ("src/highfly/rebirth/training_entry.ts",
  "const PREFIX = 'highfly.rebirth044.training.r1:';",
  "const PREFIX = 'highfly.rebirth044.training.r1.fury-lab.r16:';"),
 ("src/highfly/rebirth/vitals_runtime.ts",
  "'highfly.rebirth044.vitals.r3:'",
  "'highfly.rebirth044.vitals.r3.fury-lab.r16:'")
]:
 file=root/path
 s=file.read_text(encoding="utf-8")
 assert s.count(old)==1, "R16_ISOLATED_STORAGE_ANCHOR_DRIFT "+path+" "+str(s.count(old))
 file.write_text(s.replace(old,new,1),encoding="utf-8")
 assert new in file.read_text(encoding="utf-8")
 print("R16_LAB_PROGRESS_ISOLATED",path)
print("R16_R11_TRAINING_VITALS_SAVES_UNTOUCHED=PASS")
