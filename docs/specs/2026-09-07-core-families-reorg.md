Status: Approved (2026-09-07) — /code-review high aplicado

# Fase 0 + Fase 1 (parcial): reorganización a core/ + families/

## Review summary

Reorganiza el código existente (Fernet, Americano/Gancia, Campari) de
`modules/ensamblaje/*`, `modules/tinturas/*`, `modules/curvas/analyzer.py`
y `utils/validators.py` hacia la arquitectura de
`fernetos-diseño-y-roadmap.md`: lo genérico vive en `core/`, lo específico
de cada bebida vive en `families/<familia>/` y nunca se importa entre
familias. Precede al módulo de evaluación/torneo (Fase 2 del roadmap).

El movimiento de código existente es mecánico (mover/renombrar, no
reescribir lógica: el diff de los archivos de test es mínimo, solo
imports). Además se agrega andamiaje nuevo, todavía no conectado a la UI
— ver "Qué se agregó" más abajo; **este spec no es puramente un refactor
mecánico**, aunque la mayor parte del diff sí lo sea.

## Qué se movió

- `modules/ensamblaje/calculator.py` → `families/fernet/calculator.py`
- `modules/ensamblaje/calculator_americano.py` → `families/gancia/americano_calculator.py`
- `modules/ensamblaje/calculator_gancia.py` → `families/gancia/gancia_calculator.py`
- `modules/ensamblaje/calculator_campari.py` → `families/campari/campari_calculator.py`
- `modules/ensamblaje/common.py` → lógica repartida en `core/blend_math.py` y `core/validators.py`
- `modules/curvas/analyzer.py` → `core/curve_analysis.py` + `core/curve_visualizer.py`
- `modules/tinturas/models.py` → `core/tintura_models.py`
- `modules/tinturas/repository_sql.py` → `core/tintura_repository.py`
- `utils/validators.py` → `core/validators.py`

## Qué se agregó (nuevo, no existía antes)

- `core/recipe_engine_factory.py`: `RecipeEngineFactory.create("fernet"|"americano"|"campari", metodo=None)`
  como punto único de entrada (americano con `metodo="vinica"` devuelve
  `GanciaCalculator`, el resto `AmericanoCalculator` — ver decisión de
  naming ya documentada en `2026-09-06-americano-variantes-experimentales.md`).
- `core/receta_models.py` + `core/receta_repository.py`: modelo `Receta`
  genérico (una tabla `recetas` con columna `familia` obligatoria e
  indexada, en vez de una tabla por familia — alternativa explícitamente
  permitida en la sección 3 del roadmap).
- `core/perfil_familia.py` + `families/<familia>/profile.py`: rango de
  ABV y descripción sensorial objetivo por familia.
- `families/<familia>/curve_rules.py`: reglas de curva de extracción
  específicas de cada familia (Campari no tiene una propia, reutiliza la
  genérica de `core/curve_analysis.py`).
- Tabla `compatibilidad_familias` (dosis min/max de una tintura por
  familia) y tabla `recetas` en `data/schema/schema.sql`.

## Qué NO hace (deferred)

- No carga el catálogo inicial de tinturas típicas por familia con sus
  dosis min/max (ítem de la Fase 1 del roadmap) — es carga de datos
  reales, no código; queda pendiente para cuando el usuario confirme
  qué tinturas/dosis van en `compatibilidad_familias`.
- No toca `app.py` más allá de los imports (la UI sigue llamando a los
  calculators por su nombre viejo; no se migró a `RecipeEngineFactory`
  todavía).
- `RecipeEngineFactory`, `core/receta_repository.py` y
  `core/perfil_familia.py` no tienen ningún caller de producción todavía
  (solo sus propios tests) — es andamiaje construido para Fase 2/3 del
  roadmap, no código muerto por descuido. Queda pendiente decidir cuándo
  se migra `app.py` a usarlos.

## Hallazgos de `/code-review high` aplicados

- **Bug real, preexistente**: 3 chequeos `if analisis.dia_optimo_sugerido:`
  (truthy) en `modules/curvas/analyzer.py` trataban un día óptimo = 0
  como "sin día sugerido" (0 es falsy en Python), salteando el cálculo de
  `intensidad_optima` y `tiempo_estabilizacion`. El refactor los había
  cambiado a `is not None` en `core/curve_analysis.py`/`curve_visualizer.py`
  sin documentarlo (coló un fix real dentro de lo que se presentaba como
  refactor mecánico). Se mantiene el fix (`is not None` es lo correcto:
  0 es un día de corte válido) pero ahora documentado explícitamente acá
  y con test de regresión (`test_analizar_completo_maneja_dia_optimo_cero`
  en `tests/test_curve_analyzer.py`, usando Campari sin heurística propia
  como caso donde el fallback devuelve día 0).
- `core/validators.py`: `validar_familias_compatibles` no rechazaba
  familias duplicadas (violaría el `UNIQUE(tintura_id, familia)` del
  schema con un `IntegrityError` crudo) ni rangos de dosis inválidos
  (negativos o `dosis_min > dosis_max`). Agregadas ambas validaciones +
  tests en `tests/test_validators.py`.
- Deduplicada la lógica de `validar_familias_compatibles` y
  `validar_familia_receta` (ambas reimplementaban el mismo chequeo de
  nombre de familia) en un helper interno `_validar_nombre_familia`.
- El resto de los hallazgos (factory sin dispatch polimórfico,
  `RecipeEngineFactory`/`receta_repository`/`perfil_familia` sin caller
  de producción) se dejan como están: son consecuencia de construir
  andamiaje para las Fases 2/3 antes de conectarlo a la UI, no bugs —
  ya documentado arriba.

## Verificación

- `python -m pytest -q`: 131 passed (121 preexistentes + 10 nuevos:
  9 de validación de familias/dosis, 1 de regresión día-0).
- `python -m py_compile` sobre `app.py`, `main.py` y todo `core/`,
  `families/`, `modules/`: sin errores.
- Grep de referencias a los módulos borrados
  (`modules.ensamblaje.calculator*`, `modules.curvas.analyzer`,
  `modules.tinturas.models`/`repository_sql`, `utils.validators`):
  cero resultados fuera de los archivos borrados.
