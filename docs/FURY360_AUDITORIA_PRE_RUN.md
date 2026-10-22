# HIGHFLY REBIRTH × FURY 360° — Auditoría y contrato de integración
**Estado:** PREPARADO EN RAMA AISLADA, SIN RUN NUEVO NI PUBLICACIÓN
**Fuente del encargo:** Operación FURY 360° (22/10/2026, documento compartido)
**Motor objetivo:** ClaudeCraft `v0.44.7` + R1–R6 nativos REBIRTH + donante GOLDEN y Training.
**Repositorio de publicación independiente:** `drakentzy07/HIGHFLY-REBIRTH`.
**Donante/ramas históricas:** `drakentzy07/cobalt-hollow-lab`, especialmente `highfly-rebirth-044-nine-native-classes-20261022` (010e8ef…) y `highfly-origin-f263-collision-gesture-save-polish-20261020`.

## 0. Reglas inviolables
- **Nunca tocar** los guardados, la rama `main` ni Pages del HIGHFLY original. El repositorio REBIRTH tiene su propia URL, cache y perfil de partida.
- **Nueve clases originales:** Warrior, Paladin, Hunter, Rogue, Priest, Shaman, Mage, Warlock y Druid, habilidades y balance nativos conservados. Hunter Universal es un prototipo aparte, **no** este producto.
- **Un controlador por responsabilidad:** un dueño del joystick/movimiento GOLDEN, una cámara, un núcleo de acciones ATK/skills, un targeting, un adaptador de animaciones. Nunca multiplicar listeners/animators paralelos.
- **No autorizar una publicación** por mera compilación o verificación estática. El navegador debe mostrar el personaje y completar el spawn sin errores GLB.
- El documento FURY recomienda trabajar sobre una rama en `cobalt-hollow-lab`. La preparación técnica se hace aquí en **rama homónima aislada de REBIRTH**, porque la publicación, sus parches y los últimos rojos pertenecen al repositorio REBIRTH. Se fusionarán cambios de la otra rama *solo* tras comparación funcional y control de versiones.

## 1. Registro verificado de incidentes
| RUN | Estado | Dato probado | Acción |
|---|---|---|---|
| #7 | rojo | CSS cargaba imágenes `textures/loading/*.webp` desde rutas sin archivo tras `prune` | Reescritura de CSS/HTML a rutas hash correctas |
| #8 | rojo | Editor de apariencia `.ac-head` interceptó pulsación sobre clase Guerrero en 932 × 430 | Corrección del flujo en paisaje; sin clics JS forzados |
| #9 | rojo | Clases pulsables, pero nunca apareció `canvas` en contenedor `#offline-preview-container` | Montaje explícito del único `#char-preview-canvas` en el panel activo |
| #10 | rojo | **Canvas y GLB de vista previa pasaron**, pero `#loading-screen` no terminó + `window.__game?.sim?.player` no cumplió criterio antes de 220 s | Diagnóstico de boot: separar fallo de recursos, sim, carga 707, progresión UI, GPU y validación demasiado estricta; NO declarar juego jugable |
| R8 previos | mixto | Green CI con ERROR ASSET LOAD FAILED en Android | Corregir rutas en ejecución y exigir prueba de navegador |

**Medición del run #8:** 1.838 recursos hash validados (1.465 GLB, 112 KTX2), 3.676 URLs relativas/absolutas, SHA-256 y encabezados. Esto demuestra existencia/integridad, **no** garantiza lectura de GLB por Three.js ni tiempo de arranque.

### Errores de rutas que deben permanecer cerrados
1. `models/...` es una **clave lógica**; no anteponer `/HIGHFLY-REBIRTH/` antes de consultarla en `MEDIA_ASSETS`.
2. Producción emite `/media/models/foo.<hash>.glb` y sirve ese archivo en `/HIGHFLY-REBIRTH/media/...`.
3. `public/basis/{basis_transcoder.js,basis_transcoder.wasm}` requiere `/HIGHFLY-REBIRTH/basis/`, no la raíz del dominio.
4. CSS `url(/textures/...)` y HTML `src="/..."` no pasan por un wrapper JavaScript de fetch: resolver físicamente durante empaquetado.
5. Evitar reescribir tanto fuentes como bundles y además en ejecución: mantener **una única función canónica**, con fallback de compatibilidad bien acotado.
6. No eliminar originales salvo tras prueba exhaustiva de recursos realmente solicitados en Chromium y validación de Pages.
7. Case-sensitive real: Linux/GitHub Pages, nombres exactos, hashes y WebP/KTX2/GLB.
8. Detectar cache PWA viejo, service worker antiguo y URLs del dominio equivocado sin borrar guardados.

### Carga y UI pendientes hasta validación
- Creador en S23 Ultra horizontal: modelo renderizado, personalización visible, clase elegible, botones accesibles y texto sin espejo.
- Loader de HIGHFLY: identidad propia **y arte de carga auténtico**. R8 sustituyó el logo por texto; no equivale a recuperar el arte previo. Buscar asset fuente o incorporar el arte legítimo cuando esté disponible, sin fingir que existe.
- Recurso **Ira/Concentración**: el puente R4 convierte recursos nativos `rage/focus` al sistema `highflyVitals.energy` en gameplay, pero los datos/títulos de clase persisten. No parchear solo etiquetas; verificar costo, regen, gasto, talento y guardado en Warrior/Hunter. No modificar todas las habilidades nativas sin contrato.
- World boot: comprobar player/sim, overlay, recursos fallidos, duración, memory/GPU, caché, reentrada y persistencia de partida. El RUN #10 ya demostró la vista previa; no repetir depuración de ese punto sin evidencia.

## 2. Arquitectura FURY 360° (contrato ANTES de integrar motor externo)
```
Pointer/TouchOwnerLedger (propietario exclusivo de cada dedo)
  ├── joystick izquierdo GOLDEN (camera-relative XZ, 0..1)
  ├── cámara derecha libre (sin forzar yaw durante skill)
  ├── botones salto/doble mortal/dash
  ├── ATK manual independiente de USAR
  └── skill press/hold/drag/release/cancel
          │  intención (nunca mueve al jugador por sí sola)
          ▼
ActionIntentBridge (sin listeners nuevos de movimiento)
  ├── Locomotion: GOLDEN + sim/player_motion existente
  ├── Combat: Attack/Combo/Recovery, cancel windows validadas
  ├── SkillAim: Idle→Pressed→Aiming→Committed|Cancelled
  ├── Targeting: Assist/Closest/LowestHP/Lock, solo enemigos válidos
  └── Animation: adaptadores AnimationMixer para las 9 clases
          │
          ▼
Native simulation/skills/cooldowns + HP/MP/Stamina
```
**Regla de propiedad:** al tomar contacto, la coordenada del dedo y el selector interactivo asignan una sola tarea; una habilidad no secuestra joystick ni cámara. Combate usa intenciones inmutables `{actorId,actionId,aimWorld,direction,targetId,castMode}`, validadas por el sim nativo.

### Mobile Legends: qué se adapta, qué NO
Referencias públicas contrastadas: App Store «5 pro tips for MLBB» (configuración de select targeting, lowest HP %, lock-on y assisted aiming), y documentación de control/patches sobre skill wheel, cast slip protection y drag-to-aim. Tomamos **principios de UX**, no código ni recursos de MLBB.

- **Tap:** habilidad rápida con orientación válida (autocast configurable por skill). **Hold:** apuntado explícito. **Drag:** dirección continuamente actualizada. **Release:** lanzamiento confirmado si hay objetivo/posición válida. **Cancel-zone:** abortar sin gastar MP/ST.
- Geometrías reutilizables: line, cone, circle, rectangle, triangle, directional dash, jump-to-point y selected target. Proyecto 3D: Raycaster/collider contra terreno real, `world XZ`, altura Y calculada, no decals a través de muros.
- Target score configurable: enemigo visible y vivo, rango correcto, prioridad por distancia/% HP, bonus por orientación, lock opcional y reacquire limitado. Hero lock de MLBB se traduce a monster/NPC hostil, jamás a un selector que teleporte al personaje.
- Tap o drag no altera la cámara sin pedido del jugador. Evitar autoataque permanente, bloquear/paro obligatorio y deslizamiento al golpear.
- ATK manual → combos suelo/aire/carrera con ventanas; castear andando sin detener locomoción cuando habilidad lo permita.
- **NippleJS, XState, Rapier:** NO agregar por defecto. Ya existen entrada táctil, simulación de movimiento y Three.js; solo evaluar mediante pruebas A/B si hay defecto demostrado.

### Interface de integración sugerida (sin imponer implementación al motor nuevo)
```ts
type SkillAimShape='line'|'cone'|'circle'|'rectangle'|'triangle'|'dash'|'leap'|'target';
type CombatIntent={
  source:'atk'|'skill', actionId:string, castMode:'quick'|'manual',
  aimDirection:{x:number,z:number},
  targetId?:number,
  groundPoint?:{x:number,y:number,z:number}
};
type InputOwnership='move'|'camera'|'attack'|'skill-aim'|'jump'|'dash'|'ui';
```
Verificar contrato exacto de las clases/habilidades del motor que Lucas compartirá antes de escribir el adaptador definitivo. No suplantar interfaces existentes a ciegas.

## 3. Gates requeridos antes del RUN de integración
**G0 — Seguridad:** branch/source tag exactos; no modificación de original ni producción. Restore/rollback por SHA. Guardados: no borrar IndexedDB/localStorage.
**G1 — Filesystem:** all manifests + GLB header + KTX2 header + hashes + WebP, fonts, basis/wasm, case, HTML/CSS.
**G2 — Browser assets:** móvil 932×430; 9 clases; tocar Warrior/Hunter; 3D real; 3D network 200; no canvas oculto; logs y screenshots al fallo.
**G3 — World boot:** nombre/clase, click normal, assetsReady/ls-status, sim/player y estado overlay, spawn, 3D world, frame, save/reload; capturar duración y causas antes de lanzar RUN siguiente. No esperar 220s sin diagnósticos.
**G4 — Movement/Control:** stick camera-relative, diagonales normalizadas, look multitouch, cámara libre, wall collision, dash/roll y segundo salto mortal, sin teleport ni patinaje.
**G5 — Combat:** ATK≠USAR, cancels, action state, move/cast, target turning sin camera jerk.
**G6 — Skills:** tap vs drag vs cancel, geometría visible con pendientes, costes MP/ST sólo commit, no doble gasto, efectos/daño original.
**G7 — Nine classes:** al menos 1 skill real por clase; idealmente smoke de todo catálogo nativo; ataques desde aire sólo si autorizados.
**G8 — Mobile 60 FPS:** medir mediana/p95 de frame time, memoria, duración de carga, contexts WebGL; objetivo, no garantía incondicional.
**G9 — Publish:** run de validación GREEN y deploy aislado; QA Android físico sigue siendo validación final.

## 4. Flujo de trabajo autorizado
1. Preparar archivos solamente en `highfly-rebirth-fury360-integration-20261022` del repositorio aislado.
2. No ejecutar `workflow_dispatch`, no tocar `main` y **no publicar** sin "LANZÁ RUN".
3. Cuando llegue el motor supremo: inspeccionar archivos reales y mapear entradas, states, habilidades, movimiento y dependencias; aplicar adaptadores pequeños y tests primero.
4. Separar errores de test (falsos negativos) de errores reales (404, GLB parse, falta canvas, sim fallida). Nunca aflojar una prueba real solo para verla verde.
5. Al recibir autorización: integrar los cambios aprobados, ejecutar el workflow aislado de REBIRTH, verificar logs, regresar resultados y enlace de prueba solo si terminó GREEN.
6. Rollback: mantener commit último de Pages; revertir exclusivamente el commit de publicación en REBIRTH si falla la app. No modificar `cobalt-hollow-lab`.

## 5. Estado de esta preparación
- Rama de integración creada y documentación de aceptación incorporada.
- Test de navegador ampliado en rama para generar **`R9_WORLD_FORENSICS`** en caso de timeout y registrar HTTP 4xx/5xx críticos.
- La causa raíz del **timeout del mundo sigue abierta** hasta ejecutar la prueba corregida y revisar su informe.
- **FURY 360° no está integrado ni demostrado jugable aún**: falta recibir/comparar implementación del motor supremo y aprobar la ejecución.
