Status: Implementado, /code-review high aplicado

# Fase 2 (4/N): servicio de cierre de ronda (persiste el Ranking)

## Que agrega

- `evaluation/cierre_ronda.py`: `cerrar_ronda_categoria(categoria_id,
  muestra_repo, puntaje_repo, jurado_repo, ranking_repo,
  podar_outliers=True)`. Lee las `Muestra` de la categoria y los
  `Puntaje` ya persistidos de cada una, arma el
  `puntajes_por_muestra` que pide `calcular_ranking`, calcula el
  `Ranking` y lo persiste con `RankingRepository.guardar()` (upsert
  por `(categoria_id, muestra_id)`, ya existente del slice de
  persistencia). Devuelve la lista de `Ranking` calculada.

Cierra el item que quedaba explicitamente pendiente desde Fase 2
(2/N) y (3/N): "nada conecta los repositorios con el calculo de
ranking todavia".

## Decisiones tomadas por mi cuenta

- Recibe los 4 repositorios ya construidos (inyeccion simple) en vez
  de construirlos internamente a partir de un `DatabaseManager` -
  mismo patron de dependencias explicitas que el resto del modulo
  (`calcular_ranking` recibe `jurados` ya armado, no un repositorio).
- Si una `Muestra` de la categoria no tiene ningun `Puntaje`
  persistido, no se persiste nada y se deja propagar el `ValueError`
  de `calcular_ranking` que identifica esa muestra (fix del slice
  anterior) - cerrar una ronda con jurados faltantes es un error de
  proceso a nivel del organizador, no un caso a saltear en silencio
  (ej. ignorando esa muestra y rankeando el resto).
- Recalcular una ronda ya cerrada (ej. un jurado corrige un puntaje
  antes de la revision final) vuelve a llamar a la funcion completa:
  no hay estado de "ronda cerrada" que lo bloquee - ese candado, si
  hace falta, es una decision de UI/proceso de una fase posterior,
  no de este servicio.

## Que NO hace (deferred)

- Reportes exportables (PDF/Excel) por categoria y por muestra -
  seccion 5.5 del roadmap, siguiente slice de Fase 2.
- UI en `app.py` (Fase 3 del roadmap, fase separada).
- Revelar `receta_id_interna`/`productor_id` de las muestras al
  cerrar la ronda (mencionado en el docstring de `Muestra` como
  responsabilidad de la capa que expone los datos, no de este
  servicio ni del dataclass).

## Hallazgo de /code-review high aplicado

- **N+1 de consultas SQL**: la version inicial hacia un
  `puntaje_repo.listar(muestra_id=...)` por cada muestra de la
  categoria. Con una categoria de muchas muestras eso son muchos
  round-trips secuenciales innecesarios. Fix: una sola
  `puntaje_repo.listar()` (todos los Puntaje) agrupada por
  `muestra_id` en Python - sin agregar un metodo nuevo al
  repositorio.

## Verificacion

- `python -m pytest -q`: 180 passed (176 previos + 4 nuevos de
  `tests/test_cierre_ronda.py`).
