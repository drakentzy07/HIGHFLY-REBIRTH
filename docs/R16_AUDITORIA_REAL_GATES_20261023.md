# HIGHFLY R16 — Auditoría real y gates de aceptación (23 oct 2026)

## Alcance técnico

**Base exacta:** R15 `81bd9f7ce7aae6c086481f0110a24e115fb2bf85`, ClaudeCraft `v0.44.7`. Se conserva R11, progreso, nueve clases/especializaciones y tope LV20. No ejecutar publicación de Pages ni mezclar este PR borrador mientras falte QA Samsung físico.

### Resuelto en R16 etapa visual

- Mismo `#player-frame` nativo trasladado arriba a la izquierda; ninguna copia ni barra HTML simulada.
- Reutilización de **idéntico botón nativo** `#mobile-more` con el listener existente de `MobileControls`, para abrir el mismo cuadro `#mobile-extra-controls` mostrado en la captura S23.
- 4 ranuras nativas, ATK, saltar, dash, usar, objetivo y pasivas siguen siendo controles nativos; CSS R16 importado al final para evitar colisión R12/R15.
- El creador mantiene un único `CharacterPreview` original y un WebGL canvas; un `ResizeObserver` resincroniza al cambiar el tamaño del panel Android; viewport derecho no nulo.
- Tests Chromium a 932×430: creator raster real, conteo y posición de barra, native MORE abrir/cerrar, joystick, dash, doble salto, guardado. La prueba de menú ocurre **después** de las comprobaciones de salto para no robar foco táctil.
- Scripts nuevos: `scripts/highfly_rebirth_r16_visual.py`, `scripts/highfly_rebirth_r16_browser_patch.py`. Workflows `rebirth-r16-{build,integral}.yml` tienen estrictamente **NO DEPLOY**.

### Evidencia de primera ronda

- Build **SUCCESS**: [39966644077](https://github.com/drakentzy07/HIGHFLY-REBIRTH/actions/runs/39966644077)
- Primer integral: [39966653030](https://github.com/drakentzy07/HIGHFLY-REBIRTH/actions/runs/39966653030) **FAIL** por timeout del salto tras abrir/cerrar MÁS; no ocultar.
- Integral con orden corregido **SUCCESS**: [39967536387](https://github.com/drakentzy07/HIGHFLY-REBIRTH/actions/runs/39967536387).
- Más reciente RUN de evidencia visual en [GitHub Actions de la rama](https://github.com/drakentzy07/HIGHFLY-REBIRTH/actions?query=branch%3Ahighfly-rebirth-r16-s23-hud-creator-combat-20261023). Subida de capturas desde `candidate/.run-diagnostics/r16-s23-creator.png` y `r16-s23-world-hud.png` si pasan/alcanzan los puntos de QA.
- Primer integral: `R15_CREATOR_WEBGL_OWNER`: 452×240 con WebGL activo y 75 grupos de color en raster del creador; `R16_NATIVE_TOP_HUD`: un player-frame x=11,y=7 y native More x=15.8,y=73.1, 49×49; `R16_NATIVE_SINGLE_TOP_FRAME_AND_MORE_CLICK=PASS`.

## Recuperación de combate R16 etapa siguiente — NO CERTIFICADA

1. **Ataque 1→2→3→4, físicamente animado y con whiff legal:**
   - `cobalt-hollow-lab/overlays/highfly_v15_manual_strike_p2.py` incluye reutilización de `highflyBasicAttack(step)` de CLEAN V1.
   - `overlays/highfly_origin_r39a_no_slide.py` y `game/c1/highfly_origin_r39a_anim_split.ts` separan piernas/cadera del torso/brazos sin cambiar hitboxes del Sim.
   - `overlays/highfly_origin_r39c2_170ms_combo_buffer.py` contiene buffer de 170 ms y golpe al aire sin target.
   - R13 actual `scripts/highfly_rebirth_r13_recovery.py` hace ONE native strike mediante `tryPlayerSwingImpl`, pero exige target real y sólo registra reloj de combo; **no** certifica 4 golpes únicos ni ataque sin target. Adaptar componentes al ABI de REBIRTH; no importar overlays que asuman CLEAN 0.44.0 sin confirmar anclas.

2. **Recursos reales HP+MP+EN para las 9 clases:** R15 sólo dispone de `p.resource` y `p.resourceType`; en primer test Warrior reportó `resourceType='rage'` y `shownType='IRA'`. Requiere un mismo Sim con dos reservas y redes independientes de costes/regen de habilidades mágicas y físicas, revisión de pasivas/especializaciones, serialización versionada, migration de guardados R16 sin sobreescribir R11; **no dibujar barras falsas**.

3. **Apuntado Mobile Legends completo:** R13 `scripts/highfly_rebirth_r13_aim.py` ya conecta `FuryRebirthAdapter` sólo a skills `targetMode='position'`. FURY contiene `skill_gestures` + `skill_preview` + `three_ground_overlay`; extender con adaptadores para line/cone/position/self/target, prioridades nearest/lowest HP/lock, soltar una vez, cancelar no consume ni GCD, prioridad total a aim manual; Sim valida hit/damage.

4. **Animación y dash:** conservar movimiento GOLDEN y físico R14, upper-mask de R15 (ya usa GLB). Testear run+attack en aire/tierras y cuarto remate; bonus mortal ya autorizado por hit nativo, pero debe validarse físicamente en S23.

## Bloqueos para promoción/publicación

- Captura de **personaje real visible** en el creador sobre Samsung S23 Ultra en horizontal, no sólo un canvas en Chromium.
- Comprobar manualmente botones ATK, USAR, cuatro skills y multitouch sin superposiciones.
- Validar HP, MP y EN **reales** por consumo/regeneración en las nueve clases, mismo Sim y persistencia.
- Cuatro clips/melee/whiff/cadena y targeting/skill CANCELAR reales; no considerar SUCCESS CI equivalente a funcionalidad completa.
- R11 root hash-identical, guardado de progreso real intacto, no fusión ni publicación antes de todo lo anterior.
