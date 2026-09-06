Status: Approved (2026-09-05)

# Gancia Casero: receta real de referencia (resuelve dos ítems deferred)

## Review summary

El usuario aportó una receta real de Gancia casero (infusión directa, sin
base vínica) y datos reales de maceración, resolviendo dos ítems que las
Fases 2 y 3 habían dejado explícitamente en `Deferred aspects` a la espera
de justamente esto. No es un spec nuevo de feature — es carga de dato real
en tres puntos ya preparados para recibirlo: la taxonomía de grupos, la
heurística de `CurveAnalyzer`, y una nueva función de cálculo de ABV para
este estilo de receta (paralela a `calcular_abv_blend`, no lo reemplaza).

**Esto NO hace**: no toca el motor de base vínica (`calcular_base_vino_alcohol`,
`calcular_abv_blend`) construido en la Fase 2 para la receta "competitiva"
— ambas recetas (vínica y casera/infusión directa) son reales y coexisten
como dos formas de calcular un blend de Gancia, no una reemplaza a la
otra. No agrega UI nueva para la receta casera (ni un formulario de
Ensamblaje, ni un preset) - eso queda para cuando el usuario lo pida.

## Receta real aportada por el usuario

Gancia casero, para 3.5-5.5 L según agua elegida:
- Alcohol etílico 96°: 500 ml
- Cáscara de pomelo, limón, naranja: 1 unidad c/u
- Romero: 2 ramas
- Clavo de olor: 4 unidades
- Agua: 3000-5000 ml (parametrizable)
- Azúcar: 800-1000 g
- Maceración: 40 días, agitación cada 2 días

ABV: alcohol diluido en el agua total (alcohol + agua elegida); azúcar y
sólidos (cáscaras, hierbas) no aportan alcohol y no entran en el cálculo.
Confirmado con dos casos: 3L agua → ~13.7% ABV, 5L agua → ~8.7% ABV.

## Cambios

1. **`modules/tinturas/models.py`**: `GrupoFuncional.CITRICOS_DULCES` →
   `CITRICOS_AMARGOS` (valor `"citricos_amargos"`). Corrección de
   dominio: las cáscaras cítricas (pomelo, limón, naranja) aportan
   amargor, no dulzor. `GRUPOS_POR_PRODUCTO[Producto.GANCIA]` actualizado.
   `QUINADOS` queda definido pero documentado como sin receta propia
   todavía (comentario en el Enum), para poder sumar quina/genciana como
   ingrediente futuro sin romper el modelo. Sin filas reales en la BD
   usaban el valor viejo (verificado antes del rename) - rename seguro,
   sin migración de datos necesaria. `app.py`: color del grupo actualizado
   (`get_grupo_color`).
2. **`modules/curvas/analyzer.py`**: `CurveAnalyzer.sugerir_dia_corte()`
   gana una rama para `self.tintura.producto == Producto.GANCIA` (los 4
   grupos comparten la heurística, porque en esta receta todo macera
   junto en un solo lote): 40 días, mismo patrón que las ramas existentes
   de Fernet (si ya pasaron, sugiere el día actual; si no, sugiere 40).
3. **`modules/ensamblaje/calculator_gancia.py`**: nuevo
   `GanciaCalculator.calcular_abv_infusion(alcohol_ml, alcohol_abv,
   agua_ml) -> float`, usa el helper compartido `abv_resultante` de
   `modules/ensamblaje/common.py` (mismo mecanismo de composición que ya
   conecta `FernetCalculator`/`GanciaCalculator`).

## Testing (TDD, como pidió el usuario)

Tests escritos antes de la implementación, confirmados en rojo y luego en
verde:
- `tests/test_calculator_gancia.py`: `calcular_abv_infusion` con 3L
  (~13.7%), 5L (~8.7%), y 0L de agua (= grado del alcohol, caso límite).
- `tests/test_models.py`: `CITRICOS_AMARGOS` existe con el valor
  correcto, `CITRICOS_DULCES` ya no existe como atributo, una tintura de
  Gancia con ese grupo no lanza.
- `tests/test_curve_analyzer.py` (nuevo): heurística de 40 días para
  varios grupos de Gancia, antes/después/exactamente en el día 40.

Verificado con pytest (80 tests, exit 0) y con la app real (smoke test:
arranca sin errores, Curvas de Extracción renderiza sin excepciones).

## Deferred aspects (actualización de Fase 2/3)

- **Heurística de día de corte por grupo de Gancia**: resuelto por este
  documento con datos reales del usuario. Ya no está deferred.
- **Soporte de Gancia en microblending/A-B**: sin cambios, sigue vigente
  lo de la Fase 3.
- **UI/preset para la receta de Gancia casero** (formulario de Ensamblaje
  específico para infusión directa, o receta de ejemplo en el README):
  no se pidió en este turno - queda como posible extensión futura si el
  usuario la pide. `calcular_abv_infusion` ya está listo para que una UI
  lo use cuando se arme.

## Implementation guidance
- TDD: aplicado, como se pidió explícitamente.
- Isolation: checkout actual (`main`).
- Verify: `pytest` (suite completa, exit 0).
- Review: a criterio del usuario para este cambio puntual - no se lanzó
  `/code-review high` automáticamente dado el tamaño acotado (3 archivos
  de producción, todo cubierto por tests nuevos); se ofrece si lo pide.
- Scope: taxonomía + heurística + una función de cálculo, nada más.
