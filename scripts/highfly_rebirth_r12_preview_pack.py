#!/usr/bin/env python3
"""Package an additive /fury-lab/ under exactly rebuilt R11 GitHub Pages root.

All R11 files are kept byte-identical after the site's copied. No edits to main
branch and no reading/writing R11 offline character keys from the lab.
"""
from pathlib import Path
import hashlib
import json
import sys
import shutil
root=Path.cwd()
mode=sys.argv[1]
candidate=Path(sys.argv[2]) if len(sys.argv)>2 else root/"candidate"
base="/HIGHFLY-REBIRTH/"
lab="/HIGHFLY-REBIRTH/fury-lab/"
save_source="highfly.rebirth044.offline.r6:"
save_lab="highfly.rebirth044.offline.r6.fury-lab:"
extensions={".ts",".tsx",".js",".mjs",".css",".html",".json",".webmanifest",".xml",".txt"}

def rewrite(path:Path):
    try: old=path.read_text(encoding="utf-8")
    except (UnicodeDecodeError,OSError):return False
    new=old.replace(base,lab)
    if new!=old:
        path.write_text(new,encoding="utf-8")
        return True
    return False

def tree_hash(path:Path):
    result={}
    for p in path.rglob("*"):
        if p.is_file() and "fury-lab" not in p.relative_to(path).parts:
            result[str(p.relative_to(path))]=hashlib.sha256(p.read_bytes()).hexdigest()
    return result

if mode=="source":
    save=candidate/"src/highfly/rebirth/offline_save.ts"
    data=save.read_text()
    if data.count(save_source)!=1:raise RuntimeError("R12_UNEXPECTED_SAVE_KEY_SOURCE")
    save.write_text(data.replace(save_source,save_lab))
    files=0
    for p in list((candidate/"src").rglob("*")) + [candidate/n for n in ("index.html","play.html","admin.html","editor.html","guide.html")]:
        if p.is_file() and p.suffix.lower() in extensions:
            files+=int(rewrite(p))
    index=(candidate/"index.html").read_text()
    assert lab in index,"R12_LAB_ASSET_BASE_NOT_REWRITTEN"
    print("R12_FURY_LAB_ISOLATED_SAVE_KEY",save_lab)
    print("R12_FURY_LAB_SOURCE_BASE_REWRITES",files)
elif mode=="dist":
    dist=candidate/"dist"
    assert dist.is_dir()
    files=0
    for p in dist.rglob("*"):
        if p.is_file() and p.suffix.lower() in extensions:
            files+=int(rewrite(p))
    manifest=dist/"manifest.webmanifest"
    data=json.loads(manifest.read_text())
    data.update({"id":lab,"scope":lab,"start_url":lab+"?hfRebirth=1&hfFury=1&lang=es",
      "name":"HIGHFLY REBIRTH — FURY 360 LAB","short_name":"FURY LAB"})
    manifest.write_text(json.dumps(data,indent=2)+"\n")
    (dist/".nojekyll").touch()
    (dist/"fury-lab-version.json").write_text(json.dumps({
      "version":"REBIRTH-R12-FURY360-STAGING",
      "base":"ClaudeCraft-v0.44.7 + REBIRTH R11",
      "publicRootVersion":"R11_UNCHANGED_IN_THIS_COMPOSITE",
      "furyPreviewShape":"circle-native-aoe",
      "furyNativeMovement":"GOLDEN_R2_WITH_CAMERA_DECOUPLING",
      "dash":"native_edge",
      "saveNamespace":save_lab,
      "advancedCombosReady":False,
      "advancedDragAimingReady":False,
      "physicalS23Verified":False,
    },indent=2)+"\n")
    app=(dist/"index.html").read_text()
    assert lab+"assets/" in app,"R12_PREVIEW_BAD_JS_BASE"
    assert (dist/"media/models/creatures/bull.a00c2c292526.glb").is_file(),"R12_PREVIEW_GLB_NOT_EMITTED"
    assert save_lab in "".join(p.read_text(errors="ignore") for p in dist.glob("assets/*.js")),"R12_PREVIEW_SAVE_NOT_ISOLATED"
    print("R12_FURY_LAB_BUILD_ISOLATED",files)
elif mode=="assemble":
    site=root/"site"
    dist=candidate/"dist"
    assert site.is_dir() and dist.is_dir()
    before=tree_hash(site)
    # The R12 lab must be a new child, never allowed to replace R11 root.
    labdir=site/"fury-lab"
    assert not labdir.exists(),"R12_LAB_ALREADY_EXISTS"
    shutil.copytree(dist,labdir)
    after=tree_hash(site)
    assert before==after,"R12_PRODUCTION_R11_BYTES_MUTATED"
    assert (site/"index.html").is_file() and (labdir/"index.html").is_file()
    assert (site/"rebirth-version.json").is_file() and (labdir/"fury-lab-version.json").is_file()
    (site/"fury-lab-integrity.json").write_text(json.dumps({
      "main_files_preserved":len(before),
      "main_bytes_sha256":hashlib.sha256(json.dumps(before,sort_keys=True).encode()).hexdigest(),
      "lab_files":sum(1 for p in labdir.rglob("*") if p.is_file()),
      "r11_root_untouched":True,
      "main_character_save_namespace":save_source,
      "lab_character_save_namespace":save_lab
    },indent=2)+"\n")
    print("R12_COMPOSITE_PAGES_ROOT_R11_UNCHANGED_AND_FURY_CHILD_OK",len(before))
elif mode=="browser":
    script=candidate/"scripts/highfly_rebirth_r9_browser.mjs"
    old=script.read_text()
    replacements={
      "const PREFIX='/HIGHFLY-REBIRTH';":"const PREFIX='/HIGHFLY-REBIRTH/fury-lab';",
      "highfly.rebirth044.offline.r6:warrior:rebirthtester":"highfly.rebirth044.offline.r6.fury-lab:warrior:rebirthtester",
    }
    for src,dst in replacements.items():
        assert old.count(src)==1,("R12_LAB_BROWSER_ANCHOR_MISMATCH",src,old.count(src))
        old=old.replace(src,dst)
    script.write_text(old)
    print("R12_LAB_BROWSER_TEST_BASE_AND_SAVE_SCOPE_READY")
else:
    raise SystemExit("expected source|dist|assemble|browser")
