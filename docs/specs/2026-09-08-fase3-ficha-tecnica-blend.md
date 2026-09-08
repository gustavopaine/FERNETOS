Status: Implementado, verificado en el navegador, pendiente /code-review high

# Fase 3 (3/N): ficha tecnica exportable del blend de Fernet

## Contexto: por que no opera sobre el modelo Receta

El ultimo item de la seccion 5.5 del roadmap ("Exportacion de ficha
tecnica de receta, para eventual registro de marca o proveedor")
asumia el modelo generico `core.receta_models.Receta`. Al investigar
para este slice encontre que:

- `Receta`/`RecetaRepository` nunca se conecto a `app.py` (cero UI,
  `grep` de `RecetaRepository` en `app.py` no encuentra nada).
- La tabla `recetas` en la base de datos real tiene 0 filas.
- Los blends de Fernet/Gancia **tampoco se persisten en ningun lado**:
  el boton "💾 Guardar Receta" en Ensamblaje Fernet era un stub
  literal (`st.info("Funcionalidad de guardado en desarrollo")`) y el
  tab "Historial de Blends" muestra datos hardcodeados de ejemplo
  ("Próximamente"). Micromezclas si guarda el `BlendResult` en
  `st.session_state` durante la sesion del navegador, pero eso se
  pierde al cerrar la pestaña.

Con el usuario: en vez de construir sobre un modelo vacio y sin UI,
la ficha tecnica se genera al vuelo a partir del `BlendResult` que ya
devuelve `FernetCalculator` en el mismo momento del calculo -
reemplazando el boton "Guardar Receta" muerto por uno que
efectivamente hace algo util hoy.

## Que agrega

- `core/receta_reportes.py`:
  - `_filas_composicion_fernet(resultado, tinturas)`: una fila por
    componente del blend (tinturas resueltas a nombre + alcohol base
    + agua) con volumen y porcentaje del total. Una `tintura_id` sin
    `Tintura` correspondiente en el dict se omite (mismo criterio que
    ya usaba la UI de Ensamblaje).
  - `generar_ficha_tecnica_blend_fernet(resultado, tinturas) -> bytes`:
    PDF (reportlab, mismo patron que `evaluation/reportes.py`) con
    parametros objetivo, composicion, y resultado calculado
    (ABV/azucar/pH/volumen real/margen de error).
- `app.py` (Ensamblaje Fernet, tab "Nuevo Blend"): el boton
  "💾 Guardar Receta" (stub) se reemplaza por
  "📄 Descargar ficha técnica (PDF)" (`st.download_button`) que genera
  la ficha del `resultado` recien calculado.

## Decisiones tomadas por mi cuenta

- **Solo Fernet en este slice.** Gancia tiene su propio
  `GanciaBlendResult` con una `ComposicionBlendGancia` de forma
  distinta (vino_ml, alcohol_fortificacion_ml, agua_ml, en vez de
  alcohol_base_ml/agua_base_ml) - generalizar ambas familias en una
  sola funcion hubiera sido una abstraccion prematura sobre dos
  formas de datos distintas. Confirmado con el usuario: Gancia queda
  para un slice posterior si hace falta.
- **PDF, no Excel** - mismo criterio que Fase 2 (5/N): reportlab ya es
  dependencia del proyecto, y una ficha tecnica es un documento para
  imprimir/archivar, no datos para reprocesar.
- **No incluye `notas_batch`** porque `BlendResult` no tiene ese
  campo (es del modelo `Receta`, no del blend calculado) - la ficha
  solo refleja lo que efectivamente devuelve `FernetCalculator`.
- La preparacion de filas (`_filas_composicion_fernet`) vive separada
  del render a PDF, testeada pura - mismo patron que
  `evaluation/reportes.py`.

## Que NO hace (deferred)

- Ficha tecnica para Gancia/Americano/Campari.
- Persistir el blend calculado (el problema de fondo que hace que
  esto sea "al vuelo" en vez de un lookup historico) - fuera de
  alcance de este slice, es una feature de infraestructura mas grande
  ("Historial de Blends" real, no el placeholder actual).
- Reemplazar el modelo generico `Receta`/`RecetaRepository` - sigue
  existiendo como scaffolding sin uso, sin tocar.

## Verificacion

- `python -m pytest -q`: 216 passed (210 previos + 6 nuevos de
  `tests/test_receta_reportes.py`).
- Verificacion manual en navegador (DB aislada, no la real - verificado
  por mtime): sembrada una Tintura de prueba minima, creado un blend
  de Fernet completo en la UI (Ensamblaje -> Nuevo Blend -> Calcular
  Blend), descargado el PDF real con el nuevo boton "📄 Descargar
  ficha técnica (PDF)" (`ficha_tecnica_B-20260908-6694.pdf`, 2544
  bytes, header `%PDF-`). Sin errores de consola ni tracebacks.
