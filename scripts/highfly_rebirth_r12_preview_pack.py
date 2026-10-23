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
import re
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
    # The input may ALREADY contain the lab prefix from Vite --base.
    # Plain str.replace doubled it (/fury-lab/fury-lab/assets/), which is
    # exactly what broke RUN #1. Preserve existing scoped paths.
    new=re.sub(re.escape(base)+r'(?!fury-lab/)',lab,old)
    if lab+'fury-lab/' in new:
        raise RuntimeError('R12_DOUBLE_LAB_BASE '+str(path))
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
    # Vite's import.meta.env.BASE_URL is /fury-lab/ but the release
    # intentionally shares the original R11 hashed /media/ tree. Resolve every
    # native GLB and KTX2 through the SAME R11 resource. No asset duplication.
    media_ts=candidate/"src/render/assets/media.ts"
    media_js=media_ts.read_text()
    anchor="  return base && raw.startsWith('/') && !raw.startsWith(`${base}/`) ? `${base}${raw}` : raw;"
    assert media_js.count(anchor)==1,"R12_MEDIA_ROUTER_ANCHOR_DRIFT"
    media_js=media_js.replace(anchor,
       "  if (base.endsWith('/fury-lab') && raw.startsWith('/media/')) return '/HIGHFLY-REBIRTH' + raw;\\n" + anchor)
    media_js=media_js.replace(";\\n  return base", ";\n  return base")
    media_ts.write_text(media_js)
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
    # Both apps share IDENTICAL v0.44.7 hashed media assets. Keep one copy
    # at the protected R11 root and route FURY media there at runtime.
    # The R11 catalogue hashes are validated by its own complete audit.
    media=dist/"media"
    if not media.is_dir():
        raise RuntimeError("R12_LAB_MEDIA_NOT_EMITTED")
    media_files=sum(1 for x in media.rglob("*") if x.is_file())
    if media_files<1800:
        raise RuntimeError("R12_LAB_MEDIA_COUNT_INVALID "+str(media_files))
    # All bundled file URLs that would target /fury-lab/media/ are served from
    # the original root /media/ to avoid publishing >1GB of duplicated GLBs.
    relocated=0
    for p in dist.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in extensions:continue
        try: before=p.read_text()
        except (UnicodeDecodeError,OSError):continue
        after=before.replace(lab+"media/",base+"media/")
        if after!=before:
            p.write_text(after)
            relocated+=1
    shutil.rmtree(media)
    print("R12_LAB_SHARED_R11_MEDIA_NO_DUPLICATION",media_files,relocated)
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
    assert not (dist/"media").exists(),"R12_PREVIEW_MEDIA_DUPLICATED"
    assert base+"media/" in "".join(p.read_text(errors="ignore") for p in dist.glob("assets/*.js")),"R12_PREVIEW_ROOT_MEDIA_ALIAS_MISSING"
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
    assert not (labdir/"media").exists(),"R12_SHARED_MEDIA_DUPLICATED"
    assert (site/"media/models/creatures/bull.a00c2c292526.glb").is_file(),"R12_R11_SHARED_MEDIA_MISSING"
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
