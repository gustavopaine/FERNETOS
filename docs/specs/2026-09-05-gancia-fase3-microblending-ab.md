Status: Approved (2026-09-05)

# Fase 3: Micromezclas y Pruebas A/B para Gancia

## Review summary

Agrega dos secciones de menú nuevas y paralelas a las existentes de Fernet —
"🎯 Micromezclas Gancia" y "⚖️ Pruebas A/B Gancia" — replicando el patrón
inline que la app real ya usa (no las clases de `modules/microblending/`,
que están sin usar). Ambas reutilizan `GanciaCalculator` (ya construido en
la Fase 2, sin lógica de cálculo nueva) y siguen exactamente la estructura
de sus contrapartes de Fernet.

**Hallazgo que cambió el plan original** (documentado como decisión, no
como "added", porque corrige una premisa equivocada del spec de Fase 2):
`PilotBatch`, `ABTesting` y `CompetitiveAnalyzer`
(`modules/microblending/*.py`) no los usa la app real — `app.py` reimplementa
la misma lógica inline con dicts en `st.session_state`. El spec de Fase 2
asumía que estas clases estaban en el camino de ejecución real; no lo
están. Confirmado con grep exhaustivo (cero llamadas a `ab_testing.` o
`PilotBatch(` en `app.py`; `CompetitiveAnalyzer` no se instancia en
ningún lugar). Esos archivos quedan intactos y sin usar, igual que hoy —
no son parte de este spec.

**Agregado más allá de lo pedido literalmente:**
- **[added] Arreglar el ABV que no se recalcula tras un ajuste en
  Micromezclas de Fernet.** Bug preexistente encontrado durante la
  investigación: `aplicar_ajuste` muta `composicion.tinturas` pero nunca
  vuelve a calcular `abv_calculado`, así que la métrica en pantalla queda
  pegada al valor del blend base. Costo: bajo (recalcular con
  `FernetCalculator.calcular_abv_blend` tras cada ajuste). Por qué: el
  usuario pidió explícitamente arreglarlo en ambos productos para que
  Gancia no herede el mismo bug desde el día uno.

**Esto NO hace**: no toca `modules/microblending/pilot_batch.py`,
`ab_testing.py` ni `modules/sensory/competitive.py` (código muerto, fuera
de alcance); no comparte código entre las secciones Fernet/Gancia más allá
de `GanciaCalculator`/`FernetCalculator` ya existentes (sigue el mismo
criterio que "Ensamblaje Gancia" en la Fase 2: secciones paralelas
independientes, no una abstracción compartida de UI); no agrega tests
nuevos de lógica de cálculo (no hay cálculo nuevo - todo lo que usa esto
ya está cubierto por los tests de `GanciaCalculator`/`FernetCalculator` de
la Fase 2/1).

## Contexto y decisiones del usuario

- Encarar esto replicando el patrón inline (no generalizar ni conectar
  `PilotBatch`/`ABTesting` reales) - confirmado.
- Arreglar el bug de ABV no recalculado en ambos productos - confirmado.
- Referencias de mercado para Gancia: **Gancia Clásico, Cinzano, Martini,
  Otra** (mismo formato que las 6 de Fernet: Branca, Vittone, 1882,
  Cinzano Fernet, Capri Fernet, Otra - sin conflicto de claves porque son
  diccionarios `referencias` independientes, uno por sección).

## Arquitectura y cambios

Todo el trabajo es en `app.py`. No se toca ningún módulo de lógica de
negocio (calculator.py, calculator_gancia.py, models.py, etc.) - todo lo
necesario ya existe desde la Fase 1/2.

### 1. Fix del bug de ABV no recalculado (Fernet, existente)

En la sección "🎯 Micromezclas" (Tab 2, botón "✅ Aplicar Ajuste"): después
de mutar `nuevo_blend.composicion.tinturas[tintura_ajuste]`, construir
`tinturas_data` (fetch de cada tintura vía `repo.get_by_id`) y llamar a
`FernetCalculator.calcular_abv_blend(nuevo_blend.composicion, tinturas_data)`
para actualizar `nuevo_blend.abv_calculado` antes de guardar la iteración.

### 2. Nueva sección "🎯 Micromezclas Gancia"

Menú lateral: se agrega justo después de "🎯 Micromezclas".

Mismo patrón de 3 tabs (⚙️ Configuración, 📊 Iteraciones, 📈 Resultados) que
la versión Fernet, con estas diferencias:

- **Tab Configuración**: parámetros simplificados igual que Fernet (que
  solo expone volumen/ABV/azúcar, no pH ni ABV de fortificación) - acá:
  volumen objetivo (L), ABV objetivo (%, 15-18), % vino (75-80), azúcar
  (% p/v, 8-12). `vino_abv` y `alcohol_fortificacion_abv` quedan en sus
  defaults de `GanciaParameterRanges` (12.0/96.0) sin exponerse como
  input, igual criterio que Fernet no expone `alcohol_base_abv` en esta
  pantalla simplificada. `acido_citrico_g_l`/`caramelo_ml` quedan en 0.0
  por la misma razón.
- **Tinturas disponibles**: `repo.listar(estado="lista",
  producto=Producto.GANCIA.value)` en vez de sin filtro.
- **"Iniciar Microblending"**: construye `GanciaBlendParams`, resuelve
  `vino_ml`/`alcohol_fortificacion_ml`/`agua_ml` con
  `GanciaCalculator().calcular_base_vino_alcohol(params, tinturas_ml_total)`,
  arma `ComposicionBlendGancia` y calcula `abv_calculado` con
  `GanciaCalculator.calcular_abv_blend(...)` - misma secuencia que ya usa
  "🍷 Ensamblaje Gancia".
- **"Aplicar Ajuste"**: mismo patrón dict que Fernet
  (`nuevo_blend.composicion.tinturas[tid] += incremento`), pero recalcula
  `abv_calculado` con `GanciaCalculator.calcular_abv_blend(...)` (fix del
  punto 1, construido correcto desde el principio - no hay bug que
  replicar acá).
- **Tabs Iteraciones/Resultados**: idénticas a Fernet (evaluación
  sensorial, gráfico de evolución de puntaje, reset) - no hay nada
  producto-específico en esta parte, se copia tal cual.
- Estado de sesión propio: `micro_gancia_iteraciones`,
  `micro_gancia_blend_actual` (namespace separado de Fernet).

### 3. Nueva sección "⚖️ Pruebas A/B Gancia"

Menú lateral: se agrega justo después de "⚖️ Pruebas A/B".

Mismo patrón de 4 tabs (🎯 Nueva Prueba, 📊 Resultados, 📈 Análisis
Competitivo, 📋 Historial) que la versión Fernet:

- **Nueva Prueba**: `opciones_blends` se arma desde
  `st.session_state.micro_gancia_iteraciones` en vez de
  `micro_iteraciones`. `referencias` = `{"gancia_clasico": "Gancia
  Clásico", "cinzano": "Cinzano", "martini": "Martini", "otra": "Otra
  referencia"}`. El resto del formulario (tipo de prueba, catadores,
  ciego, atributos a evaluar) es idéntico - vocabulario sensorial
  compartido entre productos.
- **Resultados, Análisis Competitivo, Historial**: idénticas a Fernet
  (registro de evaluaciones, radar chart, significancia estadística,
  tabla de historial) - cero lógica producto-específica en estas tres
  pestañas, se copian tal cual.
- Estado de sesión propio: `pruebas_ab_gancia`, `prueba_actual_gancia`.

## Testing

Sin TDD - no hay lógica de cálculo nueva, todo el wiring usa métodos ya
cubiertos por tests de la Fase 1/2 (`FernetCalculator.calcular_abv_blend`,
`GanciaCalculator.calcular_abv_blend`/`calcular_base_vino_alcohol`).
Verificación: `pytest` completo (debe seguir en verde, no se toca ningún
archivo bajo test) + smoke test manual de la app real (crear una tintura
de Gancia si hace falta, correr Micromezclas Gancia end-to-end, correr una
prueba A/B Gancia end-to-end) - mismo criterio que Ensamblaje Gancia en la
Fase 2.

## No-goals / alternativas rechazadas

- **Conectar `PilotBatch`/`ABTesting` reales en vez de duplicar inline**:
  rechazado por el usuario - más riesgo (tocar una pantalla que hoy
  funciona) sin beneficio inmediato para el objetivo pedido.
- **Compartir código de UI entre las secciones Fernet/Gancia** (helpers
  parametrizados por producto): rechazado - el mismo criterio que
  "Ensamblaje Gancia" en la Fase 2 (secciones paralelas independientes),
  y evita tocar código Fernet que funciona salvo el fix puntual acordado.
- **Arreglar la incompletitud del "blend personalizado" en Pruebas A/B**
  (los inputs de ABV/azúcar custom no se usan en el resto del flujo,
  bug/limitación preexistente en Fernet): fuera de alcance, no reportado
  como problema por el usuario - se replica el mismo comportamiento
  (incompleto) en la versión Gancia para no introducir asimetría, y queda
  documentado como hallazgo menor.

## Deferred aspects

- **Código muerto en `modules/microblending/`** (`PilotBatch`,
  `ABTesting`, `CompetitiveAnalyzer`) y en `modules/sensory/competitive.py`
  (una segunda clase `CompetitiveAnalyzer` con firma distinta, tampoco
  usada): candidato a limpieza en una futura pasada de robustez, fuera de
  alcance de esta fase. Vuelve a estar en alcance si el usuario pide
  limpiar código muerto o si decide conectar esas clases de verdad en vez
  de la duplicación inline.
- **Incompletitud del "blend personalizado"** en Pruebas A/B (ver
  No-goals): vuelve a estar en alcance si el usuario reporta que quiere
  usarlo de verdad.

## Implementation guidance
- TDD: apagado - no hay lógica de cálculo nueva en esta fase.
- Isolation: checkout actual (`main`), sin worktree.
- Verify: `pytest` (suite completa, exit 0 - no debe cambiar el conteo de
  tests) antes de dar por terminada cada tarea; smoke test manual de la
  app real para Micromezclas Gancia y Pruebas A/B Gancia end-to-end.
- Review: `/code-review high` sobre el diff completo de la fase, una sola
  vez, al terminar y con pytest en verde (mismo mecanismo que Fases 1-2).
- Scope: construir solo lo que este spec especifica; Deferred aspects se
  proponen, no se construyen.
- Deferred aspects: ver ledger arriba. Sin sistema de tracking externo -
  este spec es el registro canónico.
- Build order:
  1. Fix del bug de ABV no recalculado en Micromezclas (Fernet existente)
  2. "🎯 Micromezclas Gancia" (Pruebas A/B Gancia depende de sus datos)
  3. "⚖️ Pruebas A/B Gancia"
  4. Smoke test end-to-end de la app real (ambas secciones)
  5. `/code-review high`
- Routing: secuencial, orquestador directo - trabajo de UI mecánico,
  delegar no ahorraría tokens.
- Orchestrator: modelo/effort actual de esta sesión (Opus, alto esfuerzo).
