Status: Implementado, /code-review high aplicado (sin hallazgos)

# Fase 2 (5/N): reportes exportables (PDF) por categoria y por muestra

## Que agrega

- `evaluation/reportes.py`, dos funciones publicas (roadmap, seccion
  5.5):
  - `generar_planilla_resultados_categoria(categoria, muestras,
    ranking) -> bytes`: planilla de resultados de una categoria
    (posicion, codigo ciego, puntaje final, productor si ya fue
    revelado).
  - `generar_ficha_cata_muestra(muestra, puntajes, jurados,
    puntaje_final) -> bytes`: ficha de cata de una muestra para
    devolver feedback al productor (puntaje de cada jurado con su
    comentario libre, mas el puntaje final).
  - Ambas devuelven los bytes del PDF (via reportlab, ya usado en
    `scripts/generar_manual_pdf.py`) en vez de escribir a disco -
    guardar el archivo es responsabilidad de quien las llama (misma
    logica que `cerrar_ronda_categoria` recibe los repositorios en
    vez de resolverlos el mismo).

## Decisiones tomadas por mi cuenta

- **Solo PDF, no Excel.** El item de Fase 2 dice "PDF/Excel"; genero
  solo PDF porque reuse `reportlab` (ya es dependencia del proyecto,
  cero costo nuevo) y ambas salidas (planilla, ficha) son
  fundamentalmente documentos para imprimir/leer, no datos para
  reprocesar en una hoja de calculo. Un export a Excel/CSV es
  agregable despues sin tocar esto si hace falta.
- **"Historico por productor/receta a traves de ediciones"** (tercer
  item de la seccion 5.5) queda deferred: requiere consultar varias
  ediciones/eventos cruzando `receta_id_interna`, es una feature de
  reporting distinta (agregacion historica) y no hay todavia mas de
  un evento real cargado para validarla contra datos reales.
- La preparacion de filas (orden por posicion, resolucion de nombre
  de jurado, deteccion de referencias invalidas) vive en helpers
  puros (`_filas_planilla`, `_filas_ficha_cata`) separados del render
  a PDF - permite testear esa logica directo sin parsear un binario
  PDF, mismo motivo por el que `evaluation.ranking`/`scoring` son
  funciones puras separadas de la persistencia.
- `_filas_planilla` sigue el patron ya establecido en el modulo
  (`calcular_ranking`, `puntaje_final_muestra`): una `Muestra`
  desconocida referenciada por el `Ranking` lanza `ValueError`
  identificandola, no se ignora en silencio.
- `_filas_ficha_cata` es la excepcion a ese patron: un `jurado_id` sin
  `Jurado` correspondiente usa el id crudo como nombre de fallback en
  vez de lanzar. Es un reporte de lectura humana (no un calculo cuya
  correctitud dependa de tener todos los jurados), y truncar la
  generacion de la ficha completa por un dato de nombre faltante es
  peor que mostrar el id.
- `Muestra.productor_id` se muestra como `"-"` cuando es `None` (ronda
  no cerrada/revelada todavia) en vez de omitir la columna.

## Que NO hace (deferred)

- Excel/CSV.
- Historico multi-edicion por productor/receta.
- Integracion con `app.py` (Fase 3 del roadmap).
- Guardar los PDFs generados a disco (queda a cargo del caller).

## Verificacion

- `python -m pytest -q`: 189 passed (180 previos + 9 nuevos de
  `tests/test_reportes.py`).
