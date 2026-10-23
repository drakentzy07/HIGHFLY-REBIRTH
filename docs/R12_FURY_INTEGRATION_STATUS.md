# HIGHFLY REBIRTH — R12 / FURY 360 Integration

## Fixed baseline
- **Base jugable y publicada:** `main@0c64f51fe2cfb79f92856989a9c4e1acc9e0e4d1` (R11).
- **Fuente FURY:** `drakentzy07/cobalt-hollow-lab@64e94970c903aad6552930a68bd78673ca5c796f`.
- **Rama de integración segura:** `highfly-rebirth-r12-fury360-staging-20261023`.
- **No despliegue automático**, no permisos Pages, no cambios a `cobalt-hollow-lab` ni a su guardado.
- ClaudeCraft **v0.44.7**, nueve clases originales, recetas R1-R6, GLB y autosave nativos conservados.

## Auditoría de la grabación S23 (2026-10-23)
- El mundo ya permite entrar. Es un cambio fundamental respecto de R8.
- Botón Dash visible pero flotante: encontrado su origen exacto en `rebirth-044/r2/r2_style.css`, selector `#mobile-evade` con `position:fixed`.
- Ring original con múltiples slots y controles no alineados. Requerimiento: **Pasiva → Salto → Dash → Skill 1 → Usar**, cinco centros separados para touch.
- Usuario afirma que mover joystick altera la cámara. No basta con mover CSS: hay que demostrar `player.pos` cambia y `input.camYaw` no. R2 **sí** incorporó el movimiento GOLDEN parcialmente, copiando `input.ts` y `player_motion.ts` del donante; NO volver a copiar esos controladores.
- Pasiva en R12 es **acceso al libro de habilidades nativo**, nunca una skill falsa que gaste maná.

## Paquete instalado en candidato CI
1. `node fury-source/fury360/tools/stage_in_candidate.mjs --candidate candidate` **DRY RUN** de ocho archivos, cero rutas protegidas.
2. `--apply` copia exclusivamente los 8 módulos en `src/highfly/fury/`; 41 tests Node del motor puro.
3. `scripts/highfly_rebirth_r12_hud.py`: usa elementos del Action Ring nativo, conserva callbacks nativos, posiciona cinco controles y skills restantes.
4. `scripts/highfly_rebirth_r12_camera.py`: desactiva el follow yaw únicamente en móvil REBIRTH; los eventos de cámara libre siguen en el Input original.
5. `scripts/highfly_rebirth_r12_aoe.py`: opt-in `?hfRebirth=1&hfFury=1` y build `VITE_HIGHFLY_FURY360=1`; primer círculo AoE FURY usa `GroundAimController` → `renderer.setGroundAimReticle` nativos. No cast, segundo canvas, segundo sim, gasto, cooldown o detección de daño.
6. Prueba CI Playwright Android/S23 simulado: entrada, nueve clases, GLB, guardado, overlay AoE, HUD, CDP touch joystick y señal nativa de Dash.

## Límites explícitos / siguiente fase
- Aún NO integrado: arrastrar/soltar/cancelar los nueve tipos de apuntado a los botones reales, targeting avanzado, combos físicos nativos y pistas de animación salto mortal.
- FURY no significa victoria de combate: `Sim.castAbilityAt` retorna `void`, no confirma daño ni aceptación.
- Si CI da rojo, **NO publicar** y corregir usando métricas `R12_S23_TOUCH_MODE_DIAGNOSTIC`, `R12_REAL_TOUCH_JOYSTICK_MEASURE` y `R12_NATIVE_DASH_EDGE`.
- Un GREEN headless **no valida 60 FPS ni táctil físico S23**. Pedir prueba en Samsung antes de merge a main.
- El primer ciclo debe probar AoE primero, joystick apuntando después, dash y salto, ATK/combo al final (orden FURY_HANDOFF).
