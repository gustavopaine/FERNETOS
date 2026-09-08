Status: Implementado, verificado en el navegador, /code-review high aplicado (ver docs/specs/2026-09-08-fase3-panel-productor.md por los 4 hallazgos y su fix)

# Fase 3 (1/N): UI de torneo en Streamlit (loop central, MVP)

## Review summary

Agrega un nuevo modulo "🏆 Torneo" a `app.py` que hace usable de punta
a punta todo lo construido en Fase 2 (evaluacion/torneo): el
organizador crea evento/categorias/jurados/muestras, cada jurado carga
sus puntajes desde un dropdown de su nombre (sin login real), el
organizador ve el progreso en vivo, cierra la ronda, y descarga los
PDFs de resultados. Sin esto, el modulo de evaluacion entero (6
slices, 203 tests) es inaccesible salvo por Python/tests directos.

Elementos que van mas alla de lo pedido explicitamente:
- **[added] `evaluation/progreso.py` (nuevo, con tests)**: una funcion
  pura que calcula cuantos puntajes faltan por jurado/muestra en una
  categoria. Costo: ~30 lineas + tests. Sin esto, la "planilla en vivo"
  del roadmap no tiene forma de calcularse; hacerlo pura y testeada
  sigue el mismo patron que el resto del modulo en vez de meter esa
  logica inline en `app.py`.
- **[added] Toggle "revelar productor/receta" en la pestaña de
  configuracion**: el roadmap dice que eso se revela "cuando el
  organizador cierra oficialmente la ronda", pero el modelo nunca
  implemento un mecanismo real de ocultamiento (son campos `Optional`
  simples, ver docstring de `Muestra`). Un checkbox que oculta esas
  columnas por defecto en la UI es la unica interpretacion barata y
  consistente con "expuesto solo cuando el organizador elige" sin
  construir una capa de permisos real (fuera de alcance para una app
  local de un solo organizador).

Lo que este slice deliberadamente NO hace: exportar a Excel, panel de
productor (Fase 3 (2/N), ya tiene su backend listo en
`evaluation/historico.py`), ficha tecnica exportable de `Receta`
(subsistema distinto, no evaluacion), autenticacion real de jurados,
edicion/borrado de entidades ya cargadas (solo alta), y soporte
multi-organizador concurrente (un solo `DatabaseManager` SQLite local,
igual que el resto de la app).

## Contexto y decisiones ya acordadas

- TDD solo para la logica nueva extraible (`evaluation/progreso.py`);
  el shell de Streamlit se verifica corriendo la app en el navegador
  (decision del usuario para este work-stream, igual que toda la UI
  previa de `app.py` que nunca tuvo tests).
- Se trabaja directo en `main`, commits chicos por pieza (decision del
  usuario, igual que Fase 2).
- Revision: `/code-review high` al final de este slice, antes del
  commit (mismo mecanismo ya establecido en el proyecto).

## Alcance: por que este slice y no mas chico/mas grande

El roadmap agrupa "pantalla de carga de jurado, planilla de puntajes
en vivo, dashboard de resultados" en un solo bullet de Fase 3 porque
son un loop cerrado: no se puede demostrar la pantalla de jurado sin
datos de setup, ni la planilla en vivo sin jurados cargando, ni el
dashboard sin una ronda cerrada. Partirlo en slices mas chicos
generaria demos no verificables de punta a punta. "Panel de productor"
y "ficha tecnica de receta" si son separables (leen datos ya
existentes, no dependen de este loop) y quedan fuera.

## Arquitectura y ubicacion

- Nueva entrada en el `st.radio` del menu lateral (`app.py:166-181`):
  `"🏆 Torneo"`, agregada al final de la lista.
- Nuevo bloque `elif menu == "🏆 Torneo":` en `app.py`, con 4 sub-tabs
  via `st.tabs(...)` (mismo patron que "🧮 Ensamblaje" y las demas
  secciones existentes):
  1. `⚙️ Configuración`
  2. `📝 Cargar puntaje`
  3. `📊 Progreso en vivo`
  4. `🏅 Resultados`
- Los repositorios de evaluacion se instancian con el `db`
  (`DatabaseManager`) global ya existente, sin tocar `init_system()`:
  `evento_repo = EventoRepository(db)`, etc., al principio del bloque
  `elif`. Las tablas `eventos/categorias/muestras/jurados/puntajes/
  rankings` ya existen en el schema real (`modules/core/db_manager.py`)
  desde que se agregaron en Fase 2 (1/N)/(2/N) - no hace falta
  migracion.
- Nuevo `evaluation/progreso.py`:
  ```python
  @dataclass
  class ProgresoCategoria:
      puntajes_cargados: int
      puntajes_esperados: int
      pendientes: List[Tuple[str, str]]  # (muestra_id, jurado_id)

  def calcular_progreso_categoria(muestras, jurados, puntajes) -> ProgresoCategoria
  ```
  (dataclass en `evaluation/models.py`, funcion en `evaluation/
  progreso.py`, mismo split que el resto del modulo). `puntajes_
  esperados = len(muestras) * len(jurados)`; `pendientes` son los
  pares sin `Puntaje` correspondiente.

## Pantallas y flujo

### 1. Selector de evento (arriba de las 4 tabs)

- `st.selectbox("Evento", ...)` poblado con `EventoRepository.
  listar()`, mas una opcion "+ Crear nuevo evento" que abre un form
  inline (nombre, fecha via `st.date_input`, sede, numero de edicion).
  `st.date_input` siempre produce un `date` valido -> se formatea a
  `"%Y-%m-%d"` antes de pasarlo a `Evento(...)`, satisfaciendo la
  validacion de fecha agregada en Fase 2 (6/N).
- El evento elegido se guarda en `st.session_state["torneo_evento_id"]`
  para persistir entre tabs/reruns.
- Si no hay ningun evento todavia, se fuerza el form de creacion antes
  de mostrar las tabs.

### 2. Tab "⚙️ Configuración"

- **Categorias** del evento activo: form para crear una nueva
  (`familia` = selectbox sobre `core.validators.
  FAMILIAS_COMPATIBLES_VALIDAS` ordenado, `submodalidad` = selectbox
  sobre `SubModalidad`) + tabla de las ya creadas.
- **Jurados** (globales, no por evento): form para crear uno
  (nombre, rol = selectbox sobre `RolJurado`, peso_voto = number_input
  default 1.0) + tabla de los ya creados.
- **Muestras**: selectbox de categoria (del evento activo) + boton
  "Agregar muestra" que crea una `Muestra(categoria_id=...)` con
  `codigo_ciego` autogenerado (mostrado despues de crearla) y campos
  opcionales `receta_id_interna`/`productor_id` (text_input, vacios
  por default). Checkbox `"🔓 Revelar productor/receta en esta vista"`
  (default off) que gatea si esas dos columnas se muestran en la tabla
  de muestras de la categoria o aparecen como `"🔒 oculto"`.

### 3. Tab "📝 Cargar puntaje"

- Selectbox "Jurado" (nombre) y "Categoria" (del evento activo).
  Ambos se guardan en `session_state` para no tener que re-elegirlos
  despues de cada submit.
- Orden de cata: `blind_coding.orden_cata_para_jurado(muestras,
  jurado_id)` - las muestras se listan en ese orden, identificadas
  SOLO por `codigo_ciego` (nunca receta/productor, sea cual sea el
  estado del toggle de revelar de la tab 1 - esta pantalla es la que
  vería el jurado y debe quedar ciega siempre).
  Falta la validacion de "todos los jurados ya cargados en el
  arranque" (roadmap Fase 4, real evento) - se documenta como
  deferred, no bloquea este slice.
- Por cada muestra: si ese jurado ya tiene `Puntaje` para ella (via
  `PuntajeRepository.listar(muestra_id=..., jurado_id=...)`), se
  muestra "✅ Ya puntuada" con opcion de "Editar" (reabre el form
  pre-cargado; volver a guardar actualiza via el upsert existente de
  `PuntajeRepository.guardar`, ya soportado). Si no, un form con 3
  `st.slider(1, 10)` (visual/aroma/sabor_boca) + `st.text_area`
  (comentario_libre) + submit.

### 4. Tab "📊 Progreso en vivo"

- Selectbox "Categoria" (del evento activo).
- `calcular_progreso_categoria(...)` sobre las `Muestra`/`Jurado`/
  `Puntaje` de esa categoria -> metric "X/Y puntajes cargados" +
  tabla de pendientes (codigo de muestra, nombre de jurado).
- Boton **"Cerrar ronda y calcular ranking"**: llama a
  `cerrar_ronda_categoria(...)`. Si falta algun puntaje, propaga
  `ValueError` (Fase 2 (4/N) ya lo identifica por `muestra_id`) -> se
  muestra como `st.error(str(e))`, sin cerrar nada (mismo
  comportamiento de "todo o nada" que ya tiene la funcion). Si
  funciona, muestra el `Ranking` resultante en una tabla y sugiere ir
  a la tab de Resultados.

### 5. Tab "🏅 Resultados"

- Selectbox "Categoria" filtrado a las que ya tienen `Ranking`
  persistido (`RankingRepository.listar(categoria_id)` no vacio).
- Tabla de ranking (posicion, codigo, puntaje final).
- `st.download_button` para la planilla completa
  (`generar_planilla_resultados_categoria`) y, por cada muestra, un
  `st.download_button` para su ficha de cata
  (`generar_ficha_cata_muestra`, con `puntaje_final` tomado del
  `Ranking` ya calculado para esa muestra).

## Manejo de errores

- Toda operacion de escritura (`guardar`) queda en un
  `try/except Exception` con `st.error(...)` - mismo patron que el
  resto de `app.py` (ver `_verificar_backup_automatico` y otros
  bloques `elif menu == ...`), para que un dato invalido (ej. fecha
  mal formada, nombre de familia invalido) no tumbe la app completa,
  solo esa accion puntual.
- `cerrar_ronda_categoria` es la excepcion mencionada arriba: su
  `ValueError` es informativo y se muestra literal (ya identifica la
  muestra problematica).

## Testing

- `evaluation/progreso.py`: TDD, tests unitarios puros (sin DB) sobre
  `calcular_progreso_categoria` - caso sin puntajes, caso completo,
  caso parcial, categoria sin muestras/jurados.
- `app.py`: sin tests automatizados (decision del usuario). Verificacion
  manual: `streamlit run app.py`, recorrer el flujo completo (crear
  evento -> categoria -> jurados -> muestras -> cargar puntajes de 2+
  jurados -> ver progreso -> cerrar ronda -> ver y descargar
  resultados) contra una copia de la DB, no la real
  (`data/fernetos.db`).
- Suite completa (`python -m pytest -q`) debe seguir en verde (no debe
  bajar de 203 passed + los nuevos de `progreso.py`).

## Verificacion manual (navegador)

`streamlit run app.py` lanzado con el directorio de trabajo en un
scratch dir aislado (NO `data/fernetos.db` real - se confirmo por
mtime que el archivo real no se toco). Recorrido completo con
automatizacion de navegador: crear evento -> crear categoria (fernet/
puro) -> crear 2 jurados (Ana, Beto) -> crear 2 muestras -> cargar
puntaje de ambos jurados para ambas muestras -> Progreso en vivo
mostro "4/4, 0 pendientes" -> "Cerrar ronda y calcular ranking" sin
error -> tab Resultados mostro el ranking y los botones de descarga
produjeron PDFs reales (`resultados_fernet_puro.pdf`, 1951 bytes,
`%PDF-`; `ficha_M-0D30E0.pdf`, 2062 bytes, `%PDF-`).

**Bug real encontrado y corregido durante esta verificacion**: al
reabrir el form de una muestra ya puntuada (para editarla), `st.
slider(..., 1, 10, value=puntaje_previo.visual)` lanzaba
`StreamlitInvalidParameterTypeError` - `Puntaje.visual/aroma/
sabor_boca` son `float` (para la matematica de `puntaje_ponderado()`)
pero `st.slider` exige que `value` tenga el mismo tipo numerico que
`min_value`/`max_value` (`int` acá). Fix: castear a `int(...)` esos 3
valores al pre-cargar el slider - son siempre enteros 1-10 segun la
rubrica, el campo es `float` solo por la matematica de puntaje
ponderado, no porque el usuario pueda ingresar decimales. Sin esta
verificacion manual el bug hubiera llegado sin detectarse (no hay
tests automatizados de `app.py`, por decision del work-stream).

## Deferred aspects

- **Panel de productor** (Fase 3 (2/N)): UI de lectura sobre
  `evaluation/historico.py`, ya construido. Se hace como slice
  separado inmediatamente despues de este.
- **Exportacion a Excel/CSV**: PDF cubre la necesidad real por ahora
  (decision de Fase 2 (5/N)); se agrega si hace falta.
- **Ficha tecnica exportable de `Receta`**: subsistema distinto
  (`core`/`Receta`, no `evaluation`), no forma parte de esta fase de
  trabajo.
- **Edicion/borrado de Evento/Categoria/Jurado/Muestra desde la UI**:
  los repositorios ya soportan `eliminar()`, pero exponerlo en la UI
  no es necesario para el loop de un evento y se puede agregar despues
  si el organizador lo pide.
- **Autenticacion real de jurados / multi-organizador concurrente**:
  fuera de alcance para una app Streamlit local de un solo organizador
  (ver Fase 4 del roadmap - "piloto en competencia real" es el momento
  de revisitar esto si hace falta).
- **Validar que todos los jurados cargaron antes de permitir cerrar la
  ronda** (UI-side, antes de intentarlo): `cerrar_ronda_categoria` ya
  rechaza el cierre con un error claro; agregar una advertencia previa
  en la tab de Progreso es una mejora de UX, no de correctitud - se
  puede sumar en una iteracion si molesta en el uso real.

## Implementation guidance
- TDD: solo para `evaluation/progreso.py` (logica pura nueva); el
  shell de Streamlit en `app.py` no lleva tests automatizados,
  verificar corriendo `streamlit run app.py` en el navegador.
- Isolation: checkout actual (`main`), sin branch aislado.
- Verify: `python -m pytest -q` en verde antes de cerrar el slice;
  recorrido manual completo del flujo en el navegador (ver Testing).
- Review: `/code-review high` al terminar el slice, antes del commit
  (mecanismo ya establecido en el proyecto).
- Scope: construir solo lo que este spec especifica: 4 tabs dentro de
  "🏆 Torneo" + `evaluation/progreso.py`. Nada de Excel, panel de
  productor, ficha tecnica, ni edicion/borrado desde la UI - proponer,
  no construir.
- Deferred aspects: ver ledger arriba: panel de productor es el
  siguiente slice (Fase 3 (2/N)); el resto queda documentado ahi sin
  tracker externo (el proyecto no usa uno).
- Build order: `evaluation/progreso.py` + tests primero (pieza
  aislada, testeable, sin UI). Despues el bloque de `app.py` en el
  orden de las tabs (Configuración habilita datos para probar Cargar
  puntaje, que a su vez habilita Progreso y Resultados) - cada tab
  se prueba a mano en el navegador apenas esta armada, no al final.
- Routing: todo en el orquestador (este mismo). Es un cambio
  concentrado en un solo archivo grande (`app.py`) que requiere el
  contexto acumulado de convenciones ya vistas (estilo de tabs,
  manejo de errores, `session_state`); delegar a un subagente sin ese
  contexto lo obligaria a re-descubrirlo, sin ahorro real de tokens.
- Orchestrator: mismo modelo/effort de esta sesion (Sonnet 5, alto) -
  el trabajo es mecanico pero de volumen medio-alto en un archivo
  grande y sensible (no romper las 10 secciones existentes de
  `app.py`).
