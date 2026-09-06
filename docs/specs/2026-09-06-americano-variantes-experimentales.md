Status: Approved (2026-09-06)

# Americano: banco de botánicos y variantes experimentales

## Review summary

Agrega la capa de modelo para probar variantes de la receta de Americano
(ex-Gancia casero, confirmada como definitiva contra una segunda
transcripción de la fuente) sin tocar sus cantidades ni fases: un banco de
botánicos categorizado (core intocable / core-secundario / opcional), una
`VarianteExperimental` con `batch_id` legible y un campo de notas contra
referencias comerciales, y la generalización de `PilotBatch` para que su
mecanismo de iteración/ajuste ya no dependa exclusivamente de
`FernetCalculator`. Solo modelo de datos y cálculo - sin UI.

**Decisiones tomadas y confirmadas con el usuario en el turno anterior**
(no "added": ya fueron presentadas como plan y aprobadas antes de escribir
código):
- Los nombres internos (`Producto.GANCIA`, `GanciaCalculator`, los menús
  "... Gancia" de la Fase 3) NO se renombran a "Americano" - ya hay datos
  reales (`producto='gancia'`) y ~10 archivos dependientes. "Americano" es
  la categoría correcta del producto; "Gancia" queda como nombre interno
  del código y como una de las marcas comerciales de referencia.
- `calcular_abv_infusion` se **mueve** (no se duplica) desde
  `GanciaCalculator` (base vínica) a `AmericanoCalculator.calcular_abv`
  (infusión directa) - la receta de Americano no tiene vino, le
  correspondía a un módulo propio.

**Esto NO hace**: no agrega UI (ni un formulario de Ensamblaje, ni una
pantalla de variantes); no reactiva `CompetitiveAnalyzer` (el campo
`referencia_comercial` es una nota de texto libre, no el motor de
comparación ponderada contra perfiles hardcodeados); no cambia las
cantidades/fases de la receta base ya cargada (`docs/specs/2026-09-05-
gancia-receta-real-casero.md`); no construye `AmericanoCalculator.
escalar_blend()` (ver limitación abajo).

## Banco de botánicos (dato real del usuario)

- **CORE** (intocable, identidad del producto): genciana, melisa.
- **CORE secundarios** (definen el estilo - cambiarlos da un Americano
  "diferente" según la fuente, pero forman parte de la receta base
  actual, no de las variantes): canela, anís estrellado, angélica,
  enebro, cítricos (pomelo, limón, naranja).
- **OPCIONALES/EXPERIMENTALES** (banco para variantes): clavo de olor,
  raíz de galanga, paico, romero.

## Arquitectura y cambios

### 1. `modules/ensamblaje/calculator_americano.py` (nuevo)
- `INGREDIENTES_CORE`, `INGREDIENTES_CORE_SECUNDARIOS`,
  `INGREDIENTES_OPCIONALES`: el banco de botánicos como listas de
  strings. No se superponen entre sí (test dedicado).
- `validar_ingrediente_variante(especie)`: exige que cualquier ingrediente
  de una variante venga de `INGREDIENTES_OPCIONALES` - ni el core ni los
  core-secundarios entran ahí (esos se cambian editando
  `ingredientes_base`, es decir, definiendo una receta distinta).
- `ComposicionAmericano`: `alcohol_ml`, `alcohol_abv`, `agua_ml`,
  `azucar_g`, `ingredientes_base: List[ComposicionBotanica]` (fijos),
  `ingredientes_variante: List[ComposicionBotanica]` (valida cada entrada
  contra el banco de opcionales en `__post_init__`).
- `VarianteExperimental`: `batch_id: str` (ej. `"AMERICANO_CLAVO_v1"`,
  sin formato impuesto - lo define quien lo crea), `composicion:
  ComposicionAmericano`, `referencia_comercial: Optional[str]` (notas de
  cata libres contra Gancia comercial u otra marca), `abv_calculado`
  (se computa solo en `__post_init__`), `fecha_creacion`.
- `AmericanoCalculator.calcular_abv(composicion)`: la fórmula ya validada
  (alcohol diluido en agua total), movida desde `GanciaCalculator`.
  `calcular_azucar`/`calcular_volumen_con_azucar` se reutilizan
  directamente de `GanciaCalculator` (mismo mecanismo, sin duplicar).

### 2. `modules/ensamblaje/calculator_gancia.py`
Se retira `calcular_abv_infusion` (movido al punto 1). Sin cambios a
`calcular_base_vino_alcohol`/`calcular_abv_blend` ni a ningún otro método.

### 3. `modules/microblending/pilot_batch.py`
`PilotBatch.__init__` gana un parámetro `calculator: Optional[Any] = None`
(default `FernetCalculator()`, comportamiento existente sin cambios). El
resto de la clase (`aplicar_ajuste`, `aplicar_ajustes_multiples`,
`registrar_evaluacion`, `get_mejor_iteracion`, etc.) ya era genérico -
solo manipula el dict `composicion.tinturas`, no le importa qué producto
representa. Type hints de `blend`/`blend_base` y los retornos de
`aplicar_ajuste`/`aplicar_ajustes_multiples`/
`crear_lote_piloto_desde_base` aflojados de `BlendResult` a `Any` para
reflejar esto con honestidad.

**Limitación real, no resuelta en este spec**: `PilotBatch.
_crear_iteracion_inicial()` llama incondicionalmente a
`self.calculator.escalar_blend(blend_base, volumen_piloto_ml/1000)`.
`AmericanoCalculator` no tiene `escalar_blend()` - no hay un concepto de
"volumen objetivo" separado del volumen real en `ComposicionAmericano`
(a diferencia de `BlendParams`/`GanciaBlendParams`), porque esta receta no
se escala de piloto a industrial en la descripción original. Instanciar
un `PilotBatch` con una `VarianteExperimental` real fallaría hoy salvo
que se le inyecte un calculador con `escalar_blend` compatible (ej. uno
que devuelva el blend sin modificar si no hace falta escalar). Se deja
como ítem abierto en Deferred aspects en vez de construirlo sin que se
haya pedido.

### 4. `modules/microblending/ab_testing.py`
Sin cambios - `ABTesting` ya acepta muestras `Any`, lista para usarse con
`VarianteExperimental` en una prueba ciega A/B o triangular tal cual está.

## Testing (TDD, como en el turno anterior)

Tests escritos y confirmados en rojo antes de la implementación:
- `tests/test_calculator_americano.py` (nuevo): los 3 tests de ABV
  movidos desde `test_calculator_gancia.py` (adaptados a
  `ComposicionAmericano`), banco de botánicos sin superposición y con los
  ingredientes reales, `VarianteExperimental` válida/con core en variante
  (lanza)/con core-secundario en variante (lanza)/con desconocido (lanza)/
  con y sin `referencia_comercial`.
- `tests/test_calculator_gancia.py`: se quitan los 3 tests movidos: el
  resto (`calcular_base_vino_alcohol`, `calcular_abv_blend`, azúcar) sigue
  intacto.
- `tests/test_pilot_batch.py` (nuevo - no existía ninguno): default sigue
  usando `FernetCalculator` sin pasar `calculator`; un calculador inyectado
  (stub) se usa en su lugar y queda registrado; `aplicar_ajuste` funciona
  igual sin importar el calculador (confirma que el resto del pipeline es
  genérico).

Verificado con pytest (92 tests, exit 0).

## No-goals / alternativas rechazadas
- **Renombrar Gancia a Americano en el código**: rechazado por ahora (ver
  Review summary) - alto costo, sin beneficio inmediato para este pedido.
- **Reactivar `CompetitiveAnalyzer`**: el pedido fue un campo de notas
  libres, no el motor de comparación ponderada contra perfiles
  hardcodeados de `ab_testing.py`.
- **UI para cargar variantes**: no se pidió en este turno.

## Deferred aspects
- **`AmericanoCalculator.escalar_blend()`**: no construido (ver
  limitación en el punto 3). Vuelve a estar en alcance si el usuario
  quiere instanciar un `PilotBatch` real alrededor de una
  `VarianteExperimental`, o si aparece un caso real de escalar el batch
  de Americano a un volumen mayor.
- **UI de Variantes Americano** (crear variantes, correr pruebas A/B
  contra Gancia comercial, ver historial): natural siguiente paso, no
  pedido todavía.
- **Rename Gancia -> Americano**: documentado como decisión explícita de
  "por ahora no", no como pendiente activo - se retoma solo si el usuario
  lo pide.

## Implementation guidance
- TDD: aplicado.
- Isolation: checkout actual (`main`).
- Verify: `pytest` (suite completa, exit 0).
- Review: a criterio del usuario - cambio acotado (2 archivos de
  producción nuevos/tocados relevantes, más el ajuste de tipos en
  PilotBatch), todo cubierto por tests nuevos.
- Scope: banco de botánicos + VarianteExperimental + generalización de
  PilotBatch, nada más.
