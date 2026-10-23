#!/usr/bin/env python3
"""R16: do NOT call a build GREEN unless native S23 player frame and More are real."""
from pathlib import Path
import sys
if len(sys.argv)!=2:raise SystemExit("usage: r16_browser_patch.py <browser.mjs>")
p=Path(sys.argv[1])
s=p.read_text(encoding="utf-8")
anchor="""   throw Error('R15_HUD_RESOURCE_NOT_READY '+JSON.stringify(r15HUD));
 }"""
assert s.count(anchor)==1, "R16_R15_BROWSER_ANCHOR_DRIFT "+str(s.count(anchor))
test=r"""
 const r16=await page.evaluate(()=>window.__hfR16VisualDiagnostics?.()??null);
 console.log('R16_NATIVE_TOP_HUD '+JSON.stringify(r16));
 if(!r16?.active||r16.playerFrameCount!==1||r16.nativeMoreCount!==1||
    !r16.originalMoreDialog||!r16.playerFrame||!r16.nativeMore||
    r16.playerFrame.x>40||r16.playerFrame.y>30||
    r16.nativeMore.x>45||r16.nativeMore.y>110||
    r16.nativeMore.width<43||r16.nativeMore.height<43)
   throw Error('R16_NATIVE_HUD_POSITION_WRONG '+JSON.stringify(r16));
 // This is the original ClaudeCraft More control, not a second fake button:
 // click it and require the original dialog body class + visible content.
 await page.locator('#mobile-more').click();
 const opened=await page.evaluate(()=>{
   const m=document.getElementById('mobile-extra-controls');
   if(!m)return false;
   const r=m.getBoundingClientRect(),s=getComputedStyle(m);
   return document.body.classList.contains('mobile-more-open') &&
     s.display!=='none'&&r.width>180&&r.height>120;
 });
 if(!opened)throw Error('R16_REAL_MORE_BUTTON_DID_NOT_OPEN_MODAL');
 await page.locator('#mobile-more-close').click();
 const closed=await page.evaluate(()=>!document.body.classList.contains('mobile-more-open'));
 if(!closed)throw Error('R16_REAL_MORE_DIALOG_DID_NOT_CLOSE');
 console.log('R16_NATIVE_SINGLE_TOP_FRAME_AND_MORE_CLICK=PASS');
"""
# Preserve R14's physical jump/attack order: opening a native modal before
# a held touch sequence can steal/focus a pointer on Chromium Android.
# Check R16 menu only AFTER every motion+save functional regression.
end_anchor=" if(failures.length)throw Error('R9_WORLD_ASSET_ERRORS '"
assert s.count(end_anchor)==1, "R16_END_TEST_ANCHOR_DRIFT "+str(s.count(end_anchor))
s=s.replace(end_anchor,test+"\n"+end_anchor,1)
# Retain actual S23-sized creator pixels and HUD screenshots for human QA.
creator_anchor="  const png=await page.locator('#offline-preview-container').screenshot({type:'png'});"
assert s.count(creator_anchor)==1,"R16_CREATOR_PNG_TEST_DRIFT"
s=s.replace(creator_anchor,creator_anchor+"\n  writeFileSync(join(DIAG,'r16-s23-creator.png'),png);",1)
open_anchor=" await page.locator('#mobile-more').click();"
assert s.count(open_anchor)==1,"R16_MENU_OPEN_TEST_DRIFT"
s=s.replace(open_anchor," await page.screenshot({path:join(DIAG,'r16-s23-world-hud.png'),fullPage:false});\n"+open_anchor,1)
p.write_text(s,encoding="utf-8")
print("R16_S23_ORIGINAL_MORE_AND_SINGLE_FRAME_BROWSER_ASSERTIONS_INSTALLED")
