Status: Implementado, /code-review high aplicado

# Fase 2 (6/N): historico por productor/receta a traves de ediciones

## Que agrega

- `evaluation/models.py::AparicionHistorica`: una participacion de una
  receta/productor en una categoria de un evento (evento, categoria,
  muestra, y `posicion`/`puntaje_final` si la ronda ya fue cerrada).
- `evaluation/historico.py`:
  - `historico_receta(receta_id_interna, muestra_repo, categoria_repo,
    evento_repo, ranking_repo)`
  - `historico_productor(productor_id, muestra_repo, categoria_repo,
    evento_repo, ranking_repo)`

  Ambas recorren las `Muestra` de todos los eventos, filtran por el
  campo pedido, resuelven categoria/evento de cada una y el `Ranking`
  si la ronda de esa categoria ya fue cerrada, y devuelven la lista
  ordenada cronologicamente por fecha de evento.

Cierra el tercer item de la seccion 5.5 del roadmap ("Historico por
productor/receta a traves de ediciones"), que Fase 2 (5/N) habia
dejado deferred por falta de datos reales multi-evento. Al ser una
funcion pura sobre los repositorios (mismo patron que
`cerrar_ronda_categoria`), se pudo testear con datos sinteticos sin
esperar a tener eventos reales.

## Decisiones tomadas por mi cuenta

- **Una funcion por campo (`historico_receta`/`historico_productor`)
  en vez de una sola con un parametro "campo"**: la API publica queda
  mas clara para quien la llama (nombres explicitos, no un string
  magico como `campo="receta_id_interna"`); ambas comparten la logica
  real via el helper privado `_historico_por_campo`.
- **`valor=None` lanza `ValueError`** en ambas funciones: pedir el
  historico de "ninguna receta/productor" no tiene sentido de negocio
  y silenciosamente devolver `[]` ocultaria un bug del caller (ej. un
  `receta_id_interna` que nunca se seteo).
- **Sin filtro de repositorio por el campo**: `MuestraRepository` no
  tiene un metodo para buscar por `receta_id_interna`/`productor_id`
  (solo por `categoria_id`), asi que se trae toda la tabla
  `muestras` con `listar()` y se filtra en Python. La escala real de
  esto (cuantas veces compitio una receta especifica a traves de la
  historia de la competencia) es intrinsecamente chica para siempre -
  a diferencia del N+1 de `cierre_ronda` (una categoria puede tener
  decenas de muestras EN VIVO), acá no hay nada que optimizar.
- **Orden cronologico por `Evento.fecha`** (string `YYYY-MM-DD`,
  ordenable lexicograficamente), con `edicion_numero` como desempate -
  el roadmap pide "a traves de ediciones" pero no fija el criterio de
  orden; fecha es la lectura mas natural de "cronologico".
- Reutiliza los repositorios ya existentes (`MuestraRepository`,
  `CategoriaRepository`, `EventoRepository`, `RankingRepository`) sin
  agregar tablas ni columnas nuevas.

## Que NO hace (deferred)

- Exportar el historico a PDF/Excel (se puede reusar el patron de
  `evaluation/reportes.py` despues si hace falta).
- UI en `app.py` (Fase 3).

## Hallazgo de /code-review high aplicado

- **`Evento.fecha` sin validar como fecha ISO**: `historico_receta`/
  `historico_productor` ordenan por ese string asumiendo formato
  `YYYY-MM-DD`; una fecha mal formada (ej. `"15/11/2026"`) ordenaria
  mal en silencio, sin ningun error que lo delate. Fix: `Evento.
  __post_init__` ahora valida el formato con `datetime.strptime`
  (mismo patron que la validacion de `Categoria.familia`).

## Verificacion

- `python -m pytest -q`: 203 passed (199 previos + 4 nuevos de
  regresion de `Evento.fecha`).
