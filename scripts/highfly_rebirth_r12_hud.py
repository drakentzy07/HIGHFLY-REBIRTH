#!/usr/bin/env python3
"""R12 S23 native HUD: passive, jump, dash, skill 1, use; no new controller."""
from pathlib import Path
import sys
candidate=Path(sys.argv[1])
controls=candidate/"src/game/mobile_controls.ts"
s=controls.read_text()
old="    this.bindButton('mobile-menu-spellbook', () => this.callbacks.onSpellbook());"
assert s.count(old)==1,"R12_CALLBACK_ANCHOR_DRIFT"
s=s.replace(old,old+"\n    this.bindButton('hf-r12-passive', () => this.callbacks.onSpellbook());")
controls.write_text(s)
css="""
<style id="hf-r12-native-mobile-hud">
@media (orientation:landscape) and (pointer:coarse){
 body.mobile-touch.hf-rebirth-r2 #mobile-action-ring{
 --hf-r12-size:clamp(39px,4.7vw,51px);
 --hf-r12-gap:clamp(7px,1vw,11px);
 --hf-r12-step:calc(var(--hf-r12-size) + var(--hf-r12-gap));
 position:absolute!important;right:max(8px,env(safe-area-inset-right))!important;
 bottom:calc(13px + env(safe-area-inset-bottom))!important;
 width:calc(5 * var(--hf-r12-size) + 4 * var(--hf-r12-gap) + 8px)!important;
 height:calc(2 * var(--hf-r12-step) + 18px)!important;
 overflow:visible!important;z-index:31!important;
 }
 body.mobile-touch.hf-rebirth-r2 #mobile-action-ring #hf-r12-passive,
 body.mobile-touch.hf-rebirth-r2 #mobile-action-ring #mobile-jump,
 body.mobile-touch.hf-rebirth-r2 #mobile-action-ring #mobile-evade,
 body.mobile-touch.hf-rebirth-r2 #mobile-action-ring .mobile-action-slot[data-mobile-index="0"],
 body.mobile-touch.hf-rebirth-r2 #mobile-action-ring #mobile-interact{
 display:flex!important;align-items:center!important;justify-content:center!important;
 flex-direction:column!important;position:absolute!important;
 top:auto!important;left:auto!important;
 width:var(--hf-r12-size)!important;height:var(--hf-r12-size)!important;
 margin:0!important;min-width:0!important;min-height:0!important;
 bottom:2px!important;transform:none!important;border-radius:50%!important;
 pointer-events:auto!important;touch-action:manipulation!important;
 border:1px solid var(--color-mobile-btn-warm-rim,#d9b979)!important;
 background:rgba(23,31,45,.93)!important;color:var(--color-mobile-btn-warm,#f4d18a)!important;
 box-shadow:inset 0 0 12px #f1c45e25,0 2px 9px #0008!important;z-index:33!important;
 }
 body.mobile-touch.hf-rebirth-r2 #mobile-action-ring #mobile-interact{right:2px!important}
 body.mobile-touch.hf-rebirth-r2 #mobile-action-ring .mobile-action-slot[data-mobile-index="0"]{right:calc(2px + var(--hf-r12-step))!important}
 body.mobile-touch.hf-rebirth-r2 #mobile-action-ring #mobile-evade{right:calc(2px + 2 * var(--hf-r12-step))!important}
 body.mobile-touch.hf-rebirth-r2 #mobile-action-ring #mobile-jump{right:calc(2px + 3 * var(--hf-r12-step))!important}
 body.mobile-touch.hf-rebirth-r2 #mobile-action-ring #hf-r12-passive{right:calc(2px + 4 * var(--hf-r12-step))!important}
 body.mobile-touch.hf-rebirth-r2 #mobile-action-ring #mobile-action-attack,
 body.mobile-touch.hf-rebirth-r2 #mobile-action-ring .mobile-action-slot[data-mobile-index="1"],
 body.mobile-touch.hf-rebirth-r2 #mobile-action-ring .mobile-action-slot[data-mobile-index="2"],
 body.mobile-touch.hf-rebirth-r2 #mobile-action-ring .mobile-action-slot[data-mobile-index="3"],
 body.mobile-touch.hf-rebirth-r2 #mobile-action-ring #mobile-action-page-toggle{
 position:absolute!important;top:auto!important;left:auto!important;
 bottom:calc(var(--hf-r12-step) + 11px)!important;transform:none!important;z-index:32!important;
 }
 body.mobile-touch.hf-rebirth-r2 #mobile-action-ring #mobile-action-attack{right:2px!important;width:var(--hf-r12-size)!important;height:var(--hf-r12-size)!important}
 body.mobile-touch.hf-rebirth-r2 #mobile-action-ring .mobile-action-slot[data-mobile-index="1"]{right:calc(2px + var(--hf-r12-step))!important;width:var(--hf-r12-size)!important;height:var(--hf-r12-size)!important}
 body.mobile-touch.hf-rebirth-r2 #mobile-action-ring .mobile-action-slot[data-mobile-index="2"]{right:calc(2px + 2 * var(--hf-r12-step))!important;width:var(--hf-r12-size)!important;height:var(--hf-r12-size)!important}
 body.mobile-touch.hf-rebirth-r2 #mobile-action-ring .mobile-action-slot[data-mobile-index="3"]{right:calc(2px + 3 * var(--hf-r12-step))!important;width:var(--hf-r12-size)!important;height:var(--hf-r12-size)!important}
 body.mobile-touch.hf-rebirth-r2 #mobile-action-ring #mobile-action-page-toggle{right:calc(2px + 4 * var(--hf-r12-step))!important}
 body.mobile-touch.hf-rebirth-r2 #mobile-action-ring #mobile-target-cycle{
 top:auto!important;left:auto!important;right:2px!important;
 bottom:calc(2 * var(--hf-r12-step) + 6px)!important;transform:none!important;
 }
 body.mobile-touch.hf-rebirth-r2 #mobile-action-ring #mobile-stance-anchor{
 top:auto!important;left:auto!important;right:calc(2px + var(--hf-r12-step))!important;
 bottom:calc(2 * var(--hf-r12-step) + 6px)!important;transform:none!important;
 }
 body.mobile-touch.hf-rebirth-r2 #mobile-action-ring #hf-r12-passive .mobile-label,
 body.mobile-touch.hf-rebirth-r2 #mobile-action-ring #mobile-evade .mobile-label{
 font:600 9px/1.1 system-ui!important;color:#ead9b3!important
 }
 body.mobile-touch.hf-rebirth-r2 #mobile-move-zone,
 body.mobile-touch.hf-rebirth-r2 #mobile-move-joystick{
 z-index:34!important;touch-action:none!important;
 }
}
</style>
"""
button='      <button type="button" class="mobile-btn" id="hf-r12-passive" aria-label="Pasivas (abrir libro de habilidades)" title="Pasivas" data-icon="spellbook"><span class="mobile-label">Pasiva</span></button>\n'
for name in ("index.html","play.html"):
 p=candidate/name
 h=p.read_text()
 anchor='      <button type="button" id="mobile-jump"'
 assert h.count(anchor)==1,"R12_MOBILE_HUD_HTML_ANCHOR "+name
 assert h.count("</head>")==1,"R12_HUD_HEAD_ANCHOR "+name
 h=h.replace(anchor,button+anchor)
 h=h.replace("</head>",css+"</head>")
 p.write_text(h)
print("R12_S23_HUD_ORDER_PASSIVE_JUMP_DASH_SKILL1_USE=PASS")
