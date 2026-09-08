Status: Implementado, verificado en el navegador, /code-review high aplicado (2 pasadas)

# Fase 3 (2/N): panel de productor

## Que agrega

Quinta tab dentro de "🏆 Torneo": "👤 Panel de productor". UI de
lectura sobre `evaluation/historico.py` (ya construido en Fase 2
(6/N), sin logica nueva): radio "Buscar por" (Receta interna /
Productor) + un `text_input` con el valor a buscar, resultado en una
tabla (evento, edicion, fecha, categoria, codigo ciego, posicion,
puntaje final) o un mensaje "Sin apariciones registradas" si no hay
coincidencias. No depende del "evento activo" seleccionado - busca a
traves de TODOS los eventos, que es el punto de esta pantalla
("trazabilidad ... a traves de ediciones").

Este slice tambien incluye los 4 hallazgos de `/code-review high`
sobre Fase 3 (1/N) (torneo UI, todavia no commiteado) porque tocan el
mismo bloque de `app.py` que este slice extiende - ver seccion
siguiente.

## Segunda pasada de /code-review high (sobre el diff combinado 1/N+2/N)

Tres hallazgos mas, aplicados:

- **PDFs de Resultados recalculados en cada rerun ajeno**: Streamlit
  ejecuta el cuerpo de las 5 tabs en cada rerun de la app entera (no
  solo la tab visible), asi que la planilla y cada ficha de cata se
  reconstruian en cada interaccion en cualquier lado del modulo
  (ej. un jurado moviendo un slider en otra tab). Fix:
  `_pdf_planilla_resultados`/`_pdf_ficha_cata` (funciones locales
  envueltas en `@st.cache_data`) memoizan por contenido - mismos
  argumentos (categoria/muestras/ranking o muestra/puntajes/jurados/
  puntaje_final) devuelven los bytes cacheados sin reconstruir el PDF.
- **Selector de categoria no se resetea al cambiar de evento**: los
  4 `st.selectbox` de categoria (Cargar puntaje/Muestras/Progreso/
  Resultados) no tenian `index` atado al evento activo; Streamlit ya
  caia a la primera opcion en silencio cuando el id guardado dejaba de
  estar en las opciones (verificado por el review con
  `streamlit.testing.v1.AppTest`), pero de forma implicita. Fix:
  un chequeo explicito (`torneo_ultimo_evento_visto` en
  `session_state`) limpia esas 4 claves cuando el evento activo
  cambia, en vez de depender del fallback no documentado.
- **`Crear categoría` sin proteccion contra duplicados**: nada
  impedia crear dos `Categoria` con la misma
  `(evento_id, familia, submodalidad)` (doble submit, o el
  organizador repitiendo la combinacion por error), fragmentando
  muestras/progreso/ranking entre las dos filas en silencio. Fix:
  `CategoriaRepository.guardar()` ahora chequea esa terna (excluyendo
  el propio id, para permitir re-guardar/actualizar) y lanza
  `ValueError` - mismo patron de "fallar fuerte en el repositorio" que
  el resto del modulo (ver `MuestraRepository`'s UNIQUE de
  `codigo_ciego`).

## Hallazgos de /code-review high (sobre Fase 3 1/N) aplicados

- **Orden de `EventoRepository.listar()` no garantizado**: `app.py`
  usaba `eventos[-1]` para el default de "evento activo" (el mas
  reciente), pero el `SELECT * FROM eventos` sin `ORDER BY` no
  garantiza orden de insercion. Fix: `ORDER BY rowid` explicito en el
  repositorio (mismo patron que cualquier otra query - no hay
  columna de timestamp de creacion en `Evento`, `rowid` es la unica
  fuente de verdad de orden de insercion en SQLite).
- **N+1 en la tab de Progreso**: un `puntaje_repo.listar(muestra_id=..)`
  por muestra. Fix: una sola `puntaje_repo.listar()` (todos los
  Puntaje) filtrada en Python por el set de `muestra_id` de la
  categoria - mismo criterio ya aplicado en
  `evaluation/cierre_ronda.py`.
- **N+1 en la tab de Resultados**: un `ranking_repo.listar(c.id)` por
  categoria solo para saber cuales tienen ranking. Fix: se extendio
  `RankingRepository.listar()` para aceptar `categoria_id` opcional
  (mismo patron que `MuestraRepository`/`PuntajeRepository`/
  `CategoriaRepository`, que ya soportan filtro opcional) - sin
  argumento devuelve el Ranking de TODAS las categorias, una sola
  consulta.
- **Formulario de "crear evento" duplicado** entre la rama "todavia
  no hay eventos" y el expander "crear nuevo evento". Fix: extraido a
  `_form_crear_evento(key_suffix)` (funcion local del bloque
  `elif`), llamada desde ambas ramas con un `key_suffix` distinto
  para no colisionar los `key=` de los widgets de Streamlit.

## Decisiones tomadas por mi cuenta

- Bundleo (1/N) y (2/N) en un solo commit: (1/N) todavia no estaba
  commiteado cuando llegaron los hallazgos de su review, y (2/N)
  extiende el mismo bloque de codigo - separarlos en dos commits
  hubiera requerido staging manual linea por linea de un diff grande
  sin beneficio real (son cambios del mismo dia, mismo archivo, misma
  sesion de review).
- La tab de Panel de productor no filtra por evento activo (a
  diferencia de las otras 4 tabs) - es la unica forma consistente con
  el proposito de la pantalla, que es cruzar ediciones.
- Sin autocompletar de `receta_id_interna`/`productor_id`: son
  strings libres que el organizador ya tipea a mano al cargar una
  Muestra en la tab de Configuración; agregar un catalogo/autocomplete
  es una feature aparte, no pedida por el roadmap.

## Que NO hace (deferred)

- Exportar el historico a PDF/Excel.
- UI en `app.py` para revelar `receta_id_interna`/`productor_id` de
  forma masiva post-cierre (sigue siendo responsabilidad de quien
  carga la Muestra, ver Fase 2 (2/N)/(3/N)).

## Verificacion manual (navegador)

Mismo patron que Fase 3 (1/N): `streamlit run app.py` con working
directory en un scratch dir aislado (DB real no tocada, verificado
por mtime). Flujo: crear evento -> categoria -> jurado -> muestra con
`receta_id_interna="R-TEST-1"` y `productor_id="P-TEST-1"` -> tab
Panel de productor, buscar por "Receta interna" = "R-TEST-1" (resultado
con fila, tabla con toolbar de `st.dataframe` presente) -> buscar
"R-NO-EXISTE" (mensaje "Sin apariciones registradas para ese valor.")
-> cambiar a "Productor", buscar "P-TEST-1" (resultado con fila). Sin
errores de consola ni tracebacks en ningun paso.

## Verificacion

- `python -m pytest -q`: 218 passed (210 tras la primera tanda de
  hallazgos + 2 nuevos de la segunda: categoria duplicada lanza,
  re-guardar la misma categoria no lanza).
- Tres pasadas manuales en el navegador (DB aislada cada vez,
  verificado por mtime que no se toco la real): flujo completo
  original, rutas de los 4 hallazgos de la primera tanda, y
  finalmente el reset de categoria al cambiar de evento + el rechazo
  de categoria duplicada (mensaje "Ya existe una categoria 'fernet
  (puro)' para este evento" confirmado en pantalla). Sin errores de
  consola ni tracebacks en ninguna pasada.
