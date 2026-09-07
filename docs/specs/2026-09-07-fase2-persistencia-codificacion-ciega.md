Status: Approved (2026-09-07) — /code-review high aplicado

# Fase 2 (2/N): persistencia SQL + codificacion ciega

## Review summary

Segundo slice de la Fase 2 (roadmap seccion 5), sobre el slice anterior
de modelos (`docs/specs/2026-09-07-fase2-evaluacion-modelos.md`). TDD
por decision del usuario: tests escritos antes que la implementacion en
`tests/test_evaluation_repository.py` y `tests/test_blind_coding.py`.

## Que agrega

- Tablas `eventos`, `categorias`, `muestras`, `jurados`, `puntajes`,
  `rankings` en `data/schema/schema.sql` y como migracion idempotente en
  `modules/core/db_manager.py` (mismo patron que
  `compatibilidad_familias`/`recetas`: `CREATE TABLE IF NOT EXISTS`,
  corre siempre, no rompe una BD real ya existente).
- `evaluation/repository.py`: un repositorio por entidad
  (`EventoRepository`, `CategoriaRepository`, `MuestraRepository`,
  `JuradoRepository`, `PuntajeRepository`, `RankingRepository`), mismo
  patron `guardar()`/`get_by_id()`/`listar()`/`eliminar()` que
  `core/receta_repository.py`.
- `evaluation/blind_coding.py`: `orden_cata_para_jurado(muestras,
  jurado_id)` — orden aleatorio pero reproducible por jurado (semilla
  estable via SHA-256 del `jurado_id`, no `hash()` de Python que esta
  salado por proceso y daria un orden distinto en cada reinicio de la
  app).

## Decisiones tomadas por mi cuenta

- **`PuntajeRepository.guardar()` y `RankingRepository.guardar()` usan
  `INSERT OR REPLACE`** (upsert por clave natural: `UNIQUE(muestra_id,
  jurado_id)` y `PRIMARY KEY(categoria_id, muestra_id)` respectivamente)
  — un jurado que corrige su puntaje, o un recalculo de ranking,
  reemplaza el valor anterior en vez de duplicarlo. Es el comportamiento
  deseado en ambos casos.
- **`MuestraRepository.guardar()` NO usa `INSERT OR REPLACE`**, usa un
  upsert explicito `ON CONFLICT(id) DO UPDATE`. `muestras` tiene un
  UNIQUE secundario (`categoria_id, codigo_ciego`) que protege el
  anonimato de la cata (seccion 5.3); `INSERT OR REPLACE` resuelve
  *cualquier* conflicto de UNIQUE borrando la fila existente e
  insertando la nueva — con `codigo_ciego` eso borraria en silencio una
  muestra distinta que ya tenia ese codigo. Con `ON CONFLICT(id)`, una
  colision de `codigo_ciego` entre dos ids distintos sigue lanzando
  `sqlite3.IntegrityError` en vez de pisar datos (cubierto por
  `test_muestra_codigo_ciego_duplicado_en_misma_categoria_lanza`, que
  primero fallo con `INSERT OR REPLACE` silencioso hasta corregirlo).
- `orden_cata_para_jurado()` no persiste el orden generado ni lo asocia
  a una sesion de cata — es una funcion pura, determinista por
  `jurado_id`, para que la UI (todavia no construida) la pueda invocar
  cada vez que carga la pantalla de un jurado sin necesitar guardar
  nada aparte.

## Hallazgo de `/code-review high` aplicado

Los filtros opcionales de `listar()` (`evento_id`, `categoria_id`,
`muestra_id`, `jurado_id`) chequeaban truthiness (`if evento_id:`) en
vez de `is not None`. Hoy es inalcanzable (los ids siempre vienen de
`_nuevo_id()`, nunca vacios), pero un `""` entrante desde una UI sin
validar habria desactivado el filtro en silencio en vez de no matchear
nada. Cambiado a `is not None` en los cuatro sitios.

## Que NO hace (deferred, siguientes slices de Fase 2)

- Agregacion de puntajes de multiples jurados con media recortada
  (poda de outliers, seccion 5.3) y calculo de `Ranking` a partir de
  los `Puntaje` (hoy `RankingRepository` solo persiste un `Ranking` ya
  calculado externamente).
- Reportes exportables.
- UI en `app.py`.

## Verificacion

- `python -m pytest -q`: 164 passed (151 previos + 13 nuevos: 8 de
  repositorios, 5 de codificacion ciega).
- `python -m py_compile` sobre los archivos nuevos/modificados: sin
  errores.
