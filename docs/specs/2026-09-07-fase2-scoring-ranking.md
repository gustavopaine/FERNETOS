Status: Implementado, /code-review high aplicado

# Fase 2 (3/N): puntaje ponderado con media recortada + ranking

## Review summary

Tercer slice de la Fase 2 (roadmap seccion 5.3/5.4), sobre los slices de
modelos y persistencia previos. TDD por decision del usuario: tests en
`tests/test_scoring.py` y `tests/test_ranking.py` escritos antes que la
implementacion.

## Que agrega

- `evaluation/scoring.py`: `puntaje_final_muestra(puntajes, jurados,
  podar_outliers=True)` combina los `Puntaje` de varios jurados sobre
  una misma muestra en un puntaje final, ponderando por
  `Jurado.peso_voto`. Con `podar_outliers=True` y al menos 3 puntajes,
  aplica media recortada (descarta el `puntaje_ponderado()` mas alto y
  el mas bajo antes de promediar) — la poda de outliers de la seccion
  5.3.
- `evaluation/ranking.py`: `calcular_ranking(categoria_id,
  puntajes_por_muestra, jurados, podar_outliers=True)` calcula el
  puntaje final de cada muestra de una categoria y devuelve la lista de
  `Ranking` ordenada de mayor a menor puntaje, con posiciones
  secuenciales desde 1.

## Decisiones tomadas por mi cuenta

- **Umbral de poda: minimo 3 puntajes.** Podar el maximo y el minimo de
  2 puntajes no deja nada que promediar; con menos de 3 se promedian
  todos sin podar. El roadmap no fija el umbral, esto es la unica lectura
  consistente de "descartar el mas alto y el mas bajo".
- **La poda opera sobre `puntaje_ponderado()`** (el puntaje ya combinado
  con la rubrica 15/30/55 de cada jurado), no sobre los sub-puntajes
  crudos (visual/aroma/sabor_boca) por separado — la seccion 5.3 habla
  de "el puntaje mas alto y el mas bajo" en singular, consistente con
  operar sobre el puntaje ya agregado por jurado.
- **`peso_voto` se aplica DESPUES de la poda**, no antes: se descartan
  los `Puntaje` extremos por su valor, y el promedio de los que quedan
  se pondera por el peso de sus jurados. Alternativa descartada: podar
  por "puntaje ya multiplicado por peso" mezclaria la severidad del
  jurado con su influencia declarada, doble-contando el peso.
- **Jurado no encontrado en la lista `jurados` lanza `ValueError`** en
  vez de asumir `peso_voto=1.0` por defecto — es una inconsistencia de
  datos (un puntaje de un jurado que no se paso), no un caso valido a
  tolerar en silencio.
- **Desempate por `muestra_id`** cuando dos muestras quedan con el mismo
  puntaje final — el roadmap no especifica una regla de empate; ambas
  reciben posiciones distintas (no hay posiciones compartidas), orden
  estable y determinista.
- `calcular_ranking` recibe `puntajes_por_muestra` ya armado (un dict
  `muestra_id -> List[Puntaje]`) en vez de ir a buscarlo el mismo via
  `PuntajeRepository` — mantiene la funcion pura y testeable; armar ese
  dict a partir del repositorio es responsabilidad de la capa que
  todavia no existe (servicio/UI de cierre de ronda).

## Que NO hace (deferred, siguientes slices de Fase 2)

- Persistir el `Ranking` calculado (ya existe `RankingRepository` del
  slice anterior, pero nada los conecta todavia).
- Reportes exportables, UI en `app.py`.

## Hallazgos de /code-review high aplicados

- **`Jurado.peso_voto` sin validar permitia ZeroDivisionError en
  `puntaje_final_muestra`**: un `peso_voto` de 0 (o negativo) en todos
  los jurados considerados tras la poda dejaba `suma_pesos == 0`. Fix
  en la raiz: `Jurado.__post_init__` ahora rechaza `peso_voto <= 0`
  (igual patron que la validacion de rango de `Puntaje`), lo que hace
  la division por cero estructuralmente imposible en vez de
  parchearla en `scoring.py`.
- **`calcular_ranking` con una muestra sin puntajes tumbaba el calculo
  de toda la categoria** con un `ValueError` generico que no decia
  cual muestra. Ahora se chequea explicitamente antes de llamar a
  `puntaje_final_muestra` y el error identifica el `muestra_id`.
- `tests/test_ranking.py`: import de `pytest` sin usar, resuelto al
  agregar el test de regresion de arriba (usa `pytest.raises`).

## Verificacion

- `python -m pytest -q`: 176 passed (173 previos + 3 nuevos de
  regresion: peso_voto no positivo, muestra sin puntajes en ranking).
- `python -m py_compile` sobre los archivos nuevos: sin errores.
