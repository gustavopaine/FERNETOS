Status: Approved (2026-09-06)

# Campari: cuarto producto (receta real, batch de referencia 1.5L)

## Review summary

Agrega Campari como cuarto producto del sistema (Fernet, Gancia,
Americano, Campari), con la receta real de referencia del usuario
(batch de 1.5L: 1000ml alcohol 40° + botánicos macerados + hibiscus de
incorporación tardía + dilución con azúcar y agua). Reutiliza taxonomía
ya existente donde corresponde (`amargos_estructurales` con Fernet,
`citricos_amargos` con Gancia) en vez de crear grupos redundantes.

**Corrección de contexto**: el usuario pidió inicialmente "reemplazar
placeholders" de un supuesto trabajo previo de Campari - se verificó con
grep exhaustivo (código, git log, specs) que ese trabajo nunca existió en
este proyecto. Confirmado con el usuario que es un producto nuevo desde
cero, no una continuación.

**Esto NO hace**: no agrega una capa de "variantes experimentales" como
Americano (no se pidió); no agrega UI; no modela la incorporación tardía
del hibiscus con ningún cálculo de timing (se guarda como lista aparte,
sin lógica de "últimos 3-5 días" todavía).

## Receta real (batch de referencia 1.5L)

Maceración: ajenjo 10g, quina 5g, genciana 5g, angélica 5g, ruibarbo 2g,
chips de roble 5g, cáscara de naranja/pomelo/limón 1 unidad c/u, alcohol
(vodka o alcohol de cereal) 40° 1000ml. Incorporación tardía (últimos 3-5
días): hibiscus 10g. Dilución: azúcar 225g + agua 500cc → volumen final
1500ml.

Taxonomía: `amargos_estructurales` (ajenjo, quina, genciana, ruibarbo -
compartido con Fernet), `raices_aromaticas` (angélica, nuevo),
`amaderados` (roble, nuevo), `colorantes_naturales` (hibisco, nuevo),
`citricos_amargos` (naranja, pomelo, limón - compartido con Gancia).

## Arquitectura y cambios

### 1. `modules/tinturas/models.py`
- `Producto.CAMPARI = "campari"` (nuevo).
- `GrupoFuncional` gana `RAICES_AROMATICAS`, `AMADERADOS`,
  `COLORANTES_NATURALES`. `AMARGOS_ESTRUCTURALES` y `CITRICOS_AMARGOS` se
  reutilizan tal cual - el diseño de Enum único + `GRUPOS_POR_PRODUCTO`
  (Fase 2) ya soporta grupos compartidos entre productos sin cambios
  adicionales: `grupos_disponibles_para()` ya deduplica con
  `dict.fromkeys()`, no solo para EXPERIMENTAL.
- `GRUPOS_POR_PRODUCTO[Producto.CAMPARI]` agregado.

### 2. `modules/ensamblaje/calculator_campari.py` (nuevo)
- `ComposicionCampari`: `alcohol_ml`, `alcohol_abv`, `agua_ml`,
  `azucar_g`, `ingredientes_maceracion: List[ComposicionBotanica]`,
  `ingredientes_incorporacion_tardia: List[ComposicionBotanica]` (para el
  hibiscus, sin lógica de timing todavía - solo separado de la lista
  principal para que quede documentado que no macera todo el tiempo).
- `CampariBlendResult`: `composicion`, `abv_calculado`,
  `azucar_efectiva_gpl`, `control_calidad: Optional[ControlCalidad]`
  (reutiliza el dataclass ya existente en `modules.tinturas.models` en
  vez de inventar un campo nuevo - `densidad` ya vivía ahí).
- `CampariCalculator.calcular_abv()`: alcohol diluido en volumen final
  (alcohol+agua) - misma fórmula que `AmericanoCalculator.calcular_abv()`,
  cada una llama a `abv_resultante` de `common.py` por separado (sin
  compartir clase entre sí, mismo criterio "composición" del resto del
  proyecto).
- `calcular_azucar_efectiva_gpl()`: azúcar_g / litros, para verificar
  contra un ratio de referencia conocido.
- `calcular_blend()`: arma el `CampariBlendResult`; `control_calidad` se
  pasa tal cual, nunca se deriva de la receta (la densidad es un dato de
  densímetro, no un cálculo).

### 3. `app.py`
`get_grupo_color()`: colores agregados para los 3 grupos nuevos de
Campari (consistente con lo hecho para los grupos de Gancia en la Fase 2).

## Testing (TDD)

Tests escritos y confirmados en rojo antes de la implementación:
- `tests/test_calculator_campari.py` (nuevo): ABV (1000ml@40° en 1500ml
  final ≈ 26.7%, verificado que no depende de azúcar/botánicos), azúcar
  efectiva (225g/1.5L = 150 g/L exacto), densidad como dato medido no
  recalculado (1060 se conserva sin importar cambios en la receta),
  `calcular_blend()` sin `control_calidad` da `None`.
- `tests/test_models.py`: `Producto.CAMPARI` existe; sus grupos incluyen
  los compartidos (`amargos_estructurales` con Fernet, `citricos_amargos`
  con Gancia) y los nuevos; una `Tintura` de Campari con esos grupos no
  lanza; `grupos_disponibles_para("campari")` no incluye grupos
  exclusivos de otros productos (ej. `aromatica_alta`).

Verificado con pytest (105 tests, exit 0 - no había ningún test de
Campari antes de este spec, confirmado por grep).

## No-goals / alternativas rechazadas
- **Capa de variantes experimentales para Campari** (como
  `VarianteExperimental` de Americano): no se pidió - esta receta es la
  base con cantidades exactas, no un banco de opcionales para probar.
- **Lógica de timing para la incorporación tardía del hibiscus**: se
  modela como una lista aparte por ahora; automatizar "agregar el día 35"
  necesitaría integrarse con `CurveAnalyzer`/registros de maceración, que
  no se pidió en este turno.

## Deferred aspects
- **UI para Campari** (crear tinturas, calcular blend): no pedida.
- **Timing de incorporación tardía**: ver No-goals - vuelve a estar en
  alcance si el usuario quiere que el sistema recuerde/alerte cuándo
  agregar el hibiscus.
- **Variantes experimentales para Campari**: vuelve a estar en alcance si
  el usuario pide comparar variantes como ya existe para Americano.

## Implementation guidance
- TDD: aplicado.
- Isolation: checkout actual (`main`).
- Verify: `pytest` (suite completa, exit 0).
- Review: a criterio del usuario - cambio acotado, cubierto por tests
  nuevos.
- Scope: receta base + taxonomía + cálculo, nada más.
