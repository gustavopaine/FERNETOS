Status: Implementado, verificado en el navegador (DB aislada), `/code-review high` aplicado (2 hallazgos corregidos, 1 marcado como fuera de alcance - ver seccion abajo).

# Fase 4 (5/N): unificar Ensamblaje Gancia/Campari/Americano a tabs

## Review summary

Reemplaza el `st.expander("📋 Historial de Blends de X")` de Gancia,
Campari y Americano por `st.tabs(["🧪 Nuevo Blend", "📋 Historial"])`,
igualando el patron de layout que Ensamblaje Fernet ya usa desde Fase
4 (1/N). Decision del usuario tras terminar las 4 familias del
Historial de Blends.

Elementos que van mas alla de lo pedido explicitamente:
- **[added] `key=` explicito en los 4 `st.tabs()` del archivo**
  (Fernet incluido). Costo: una linea mas por llamada. Motivo: un bug
  real encontrado en la verificacion manual - Gancia/Campari/Americano
  llaman a `st.tabs()` con la misma lista de labels exacta
  (`["🧪 Nuevo Blend", "📋 Historial"]`); sin `key`, Streamlit deriva
  el id del widget de sus argumentos, así que las tres pantallas
  comparten el mismo estado de "tab seleccionado" - guardar un blend
  en Historial de Gancia y despues entrar a Campari abría directo en
  su tab "Historial" en vez de "Nuevo Blend". Confirmado en vivo
  (guardar en Gancia -> cambiar a tab Historial -> navegar a Campari
  -> abría en Historial) antes de agregar las keys. Fernet no
  colisionaba hoy (su lista de labels tiene 3 elementos, distinta), 
  pero se le agrego `key` igual por consistencia y para blindarlo
  contra el mismo bug si alguna vez otra pantalla usa exactamente las
  mismas 3 etiquetas.

Lo que este slice deliberadamente NO hace: agregar un tab
"📊 Análisis" a Gancia/Campari/Americano (el de Fernet es un
placeholder con datos hardcodeados falsos, no una funcionalidad real -
replicarlo en 3 pantallas mas seria multiplicar un wart existente, no
pedido); ningun cambio de comportamiento o contenido dentro de cada
tab (mismo contenido, misma logica, solo el contenedor visual cambia
de expander a tab).

## Contexto

Con las 4 familias conectadas al Historial de Blends (Fase 4, 1/N-4/N),
Gancia/Campari/Americano habían quedado con un `st.expander()` para el
historial (decision deliberada en 2/N para evitar restructurar esos
~300 lineas de un tirón, el mismo tipo de edicion donde aparecio un
bug de indentacion en el slice de Fernet). El usuario eligió ahora
unificar el layout a tabs para consistencia visual, con el riesgo ya
acotado porque cada bloque tiene una sola seccion "Nuevo Blend" +
"Historial" bien delimitada (a diferencia de cuando se tomó la
decision original, sin el codigo de guardado/historial todavía
escrito).

## Arquitectura

### Transformacion mecanica en `app.py`

Por cada familia (Gancia, Campari, Americano):
1. Despues de `blend_repo_X = BlendRepository(db)`: se agrega
   `tabs_X = st.tabs(["🧪 Nuevo Blend", "📋 Historial"], key="ensamblaje_X_tabs")`.
2. Todo el contenido que antes corría "suelto" (formulario + boton
   calcular + panel de resultados + boton guardar) pasa a vivir dentro
   de `with tabs_X[0]:` - un nivel de indentacion mas.
3. El bloque que antes era `with st.expander("📋 Historial de Blends
   de X"):` pasa a ser `with tabs_X[1]:` - su contenido interno no
   cambia de indentacion (ya estaba al nivel correcto).
4. Se elimina el `st.divider()` y el comentario que justificaba el
   expander (ya no aplica).

**Como se hizo la re-indentacion sin riesgo manual**: en vez de editar
~650 lineas a mano (el riesgo que motivó la decision original de usar
expanders), se escribio un script Python de un solo uso que localiza
cada bloque por texto ancla unico (la linea `blend_repo_X =
BlendRepository(db)` y la linea `with st.expander(...)` de cada
familia), y aplica un +4 de indentacion mecanico a cada linea no vacía
entre esos anclas. Verificado con `ast.parse` despues de cada
transformacion, mas lectura completa de las 3 secciones resultantes
antes de correr los tests.

## Hallazgo encontrado en la verificacion (no en el review - el review corre despues)

**`st.tabs()` sin `key` comparte estado entre pantallas con la misma
lista de labels.** Descubierto al verificar Campari despues de
guardar un blend en Gancia y cambiar a su tab "Historial": navegar a
Campari abría directo en su tab "Historial" en vez de "Nuevo Blend".
Causa: Streamlit deriva el id interno de un widget sin `key` de sus
argumentos posicionales/de contenido; como Gancia/Campari/Americano
llaman `st.tabs()` con la lista de labels *idéntica*, Streamlit los
trata como "el mismo widget" a los fines de persistencia de estado
entre reruns/pantallas. Fix: `key=` explicito y distinto por familia
en los 4 `st.tabs()` del archivo (incluido Fernet, preventivo).
Reverificado: guardar en Gancia, cambiar a Historial, navegar a
Campari -> abre en "Nuevo Blend" (independiente); mismo chequeo con
Americano.

## Hallazgos de /code-review high

- **Texto obsoleto en el estado vacio del historial**: los 3 nuevos
  tabs de Historial (Gancia/Campari/Americano) heredaron el texto del
  expander ("Calculá uno arriba...") - correcto cuando el historial
  vivia debajo del formulario en el mismo contenedor, pero ya no
  cuando es una tab separada. Fernet ya tenia la redaccion correcta
  ("Calculá uno en 'Nuevo Blend'..."). Fix: mismo texto que Fernet en
  las 3 familias.
- **`requirements.txt` no reflejaba el piso real de Streamlit
  necesario**: `st.tabs(key=...)` (agregado en este mismo slice, ver
  seccion de hallazgo de verificacion arriba) requiere una version de
  Streamlit mas nueva que el piso declarado (`>=1.28.0`) - un install
  limpio con esa version minima crashearia con `TypeError` al abrir
  cualquier pantalla de Ensamblaje. Fix: piso subido a `>=1.36.0`
  (version en la que `st.tabs` gano el parametro `key`).
- **Marcado como fuera de alcance, no corregido en este commit**: el
  mismo defecto de `st.tabs()` sin `key` compartiendo estado entre
  pantallas con la misma lista de labels existe tambien en
  Micromezclas Fernet/Gancia (`["⚙️ Configuración", "📊 Iteraciones",
  "📈 Resultados"]`) y en Pruebas A/B Fernet/Gancia (`["🎯 Nueva
  Prueba", "📊 Resultados", "📈 Análisis Competitivo", "📋
  Historial"]`) - detectado por el review al buscar la misma clase de
  bug en el resto del archivo. Es un hallazgo real y de la misma
  familia que el que este slice ya solucionó para Ensamblaje, pero
  esas dos pantallas son features completamente distintas, fuera del
  alcance de "unificar Ensamblaje a tabs" - se documenta acá como
  candidato a un slice futuro en vez de expandir este commit.

## Verificacion

- `python -m pytest -q`: 288 passed (sin cambios de logica, solo UI -
  la suite no toca `app.py`; confirma que nada mas se rompio).
- Verificacion manual en navegador (DB aislada, mtime de la DB real
  confirmado sin cambios antes/despues): para cada una de las 3
  familias (Gancia, Campari, Americano) - calcular un blend, guardar
  en el historial, cambiar al tab "📋 Historial" (tab real, no
  expander), ver el detalle real, eliminarlo, confirmar que el tab
  vuelve al estado vacío sin loop infinito ni errores de consola. Mas
  el hallazgo de arriba (colision de estado entre pantallas) y su
  fix, re-verificado. Fernet (ya con `key=` agregado) revisado
  brevemente para confirmar que sus 3 tabs siguen funcionando.

## Testing

- Sin tests automatizados nuevos (cambio puramente de `app.py`/UI,
  mismo criterio ya acordado para todo el trabajo de UI de esta
  fase) - verificacion manual en el navegador contra una DB aislada.

## Deferred aspects
- Tab "📊 Análisis" para Gancia/Campari/Americano: no se replica el
  placeholder de Fernet (son datos falsos hardcodeados, no una
  funcionalidad real) - si algún día se construye un análisis real,
  ahí sí tiene sentido agregarlo a las 4 pantallas a la vez.
- **Mismo bug de `st.tabs()` sin `key` en Micromezclas Fernet/Gancia y
  Pruebas A/B Fernet/Gancia** (hallazgo de /code-review high, ver
  seccion de hallazgos arriba): mismo fix (agregar `key=` distinto por
  pantalla), fuera de alcance de este slice. Vuelve a estar en alcance
  como slice propio si se retoma esa parte de la UI.

## Implementation guidance
- TDD: no aplica (cambio puro de estructura de UI, sin logica nueva
  extraíble).
- Isolation: checkout actual (`main`).
- Verify: `python -m pytest -q` en verde; recorrido manual en el
  navegador con DB aislada para las 3 familias.
- Review: `/code-review high` al terminar, antes del commit.
- Scope: solo el cambio de layout (expander -> tabs) + el fix de
  `key=` que salió de la propia verificacion de este slice.
- Deferred aspects: ver ledger arriba.
- Build order: script de reindentacion mecanica -> lectura completa
  del resultado -> tests -> verificacion en navegador (que encontró el
  bug de `key=`) -> fix -> reverificacion.
- Routing: todo en el orquestador (cambio concentrado en `app.py`,
  requiere el contexto ya acumulado de convenciones de esta sesion).
- Orchestrator: mismo modelo/effort de esta sesion (Sonnet 5, alto).
