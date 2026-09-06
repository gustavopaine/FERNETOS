Status: Approved (2026-09-05)

# Fase 1: Robustez de FernetOS (pre-Gancia)

## Review summary

Este spec arregla cinco problemas reales encontrados en el FernetOS actual (fernet
únicamente) antes de agregar Gancia como segundo producto en una Fase 2 separada:
`requirements.txt` roto, borrado de tinturas que deja registros huérfanos, tests que
no ejercitan el código de producción, la pestaña de Configuración que no persiste
nada, y el backup automático que nunca se dispara solo. El objetivo es que el
sistema no pierda datos ni se rompa durante las semanas de preparación de recetas
antes de la competencia (no se usa en vivo el día del evento — confirmado con el
usuario).

**Agregado más allá de lo pedido literalmente** (el usuario pidió "robustez", estos
son los elementos concretos que decidí incluir bajo ese paraguas):
- **[added] Arreglar persistencia de Configuración** (extender `FernetOSConfig` con
  una sección `backup`, y llamar a `load_settings()`/`save_settings()` desde
  `app.py`). Costo: toca `config/settings.py` y el módulo Configuración de `app.py`.
  Por qué: es el hallazgo de mayor impacto — sin esto, cualquier ajuste de rangos
  ABV/azúcar/pH o pesos de evaluación que hagas se pierde al reiniciar la app,
  justo el escenario de "afinar la receta durante semanas" que motiva este trabajo.
- **[added] Activar `PRAGMA foreign_keys = ON`** y arreglar `limpiar_duplicados.py`
  para que no deje filas huérfanas. Costo: bajo (una línea + una función).
  Por qué: el schema ya declara `ON DELETE CASCADE` — el código asume que
  funciona (hay un comentario que lo dice explícitamente en
  `repository_sql.py:eliminar()`) pero SQLite no lo aplica sin el PRAGMA.
- **[added] Backup automático real al iniciar la app** (si el último backup es más
  viejo que la frecuencia configurada). Costo: bajo, ~15 líneas.
  Por qué: la Fase 1 ya toca la persistencia de Configuración; dejar el checkbox de
  "auto backup" sin efecto real sería entregar el mismo espejismo con otro nombre.
- **[added] Suite de tests real (pytest, con asserts) contra `repository_sql.py`**
  en vez de los scripts de impresión actuales. Costo: medio — es el ítem más
  grande del spec. Por qué: fue decisión explícita tuya (TDD para lógica de
  negocio) y es la única forma de detectar si un cambio futuro (incluyendo Fase 2
  con Gancia) rompe el cálculo de blends o la integridad de la base de datos.
- **[added] Poblar `utils/validators.py`** (vacío hoy) con validaciones mínimas
  (porcentajes de composición suman ~100%, ABV/volúmenes no negativos), llamadas
  desde `Tintura.__post_init__`. Costo: bajo.
  Por qué: es la causa raíz de que datos inválidos puedan llegar a la base sin
  aviso — un solo lugar de validación que TDD requiere ejercitar igual.
- **[added] Eliminar código muerto**: `modules/tinturas/repository.py` (JSON
  legacy) y `modules/tinturas/repository_sql_simple.py`, más el archivo vacío
  `data/tinturas.db`. Costo: bajo, reversible vía git.
  Por qué: nada en producción los usa, y ya causaron el problema real de que los
  tests actuales validan el repositorio equivocado.
- **[added] Corregir 2 inconsistencias de documentación** en `README.md` (lista de
  dependencias de `requirements.txt`; rango de días de maceración de Amargos que
  no coincide con los manuales PDF) encontradas por el análisis de grafo de
  conocimiento (graphify). Costo: trivial.

**Esto NO hace**: no toca la arquitectura de `app.py` (sigue siendo un único
archivo Streamlit de ~4000 líneas — no se pidió refactor y sería scope creep);
no agrega soporte para Gancia (Fase 2, spec separado); no agrega resiliencia para
uso en vivo/concurrente (confirmado que la app no se usa el día de la competencia);
no persiste `notificaciones` ni `apariencia` (tema/idioma) de Configuración —
son cosméticos, se quedan en sesión (ver Deferred aspects).

## Contexto y hallazgos (research)

Investigación hecha directamente sobre el repo (lectura de código + grep), más el
grafo de conocimiento generado con `/graphify` sobre el proyecto completo
(`graphify-out/GRAPH_REPORT.md`, sección "Surprising Connections").

1. **`requirements.txt` incompleto.** Grep de imports reales (excluyendo `venv/`)
   muestra que el código usa `streamlit`, `plotly`, `reportlab`, `matplotlib`,
   `numpy`, `pandas`, `scipy`, `pyyaml`. `requirements.txt` solo lista
   `numpy, pandas, matplotlib, scipy, pyyaml`. Una instalación limpia
   (`pip install -r requirements.txt && streamlit run app.py`) falla con
   `ModuleNotFoundError: No module named 'streamlit'`.

2. **Cascada de borrado rota.** `data/schema/schema.sql` declara
   `FOREIGN KEY (tintura_id) REFERENCES tinturas(id) ON DELETE CASCADE` en
   `composicion_botanica`, `parametros_extraccion`, `registros_curva`. SQLite
   requiere `PRAGMA foreign_keys = ON` por conexión para aplicar esto; nunca se
   ejecuta en `DatabaseManager.get_connection()`. Confirmado explotable:
   `TinturaSQLRepository.eliminar()` (repository_sql.py:361) tiene el comentario
   *"Las foreign keys con ON DELETE CASCADE se encargan del resto"* — falso en la
   práctica — y `limpiar_duplicados.py` ya hace `DELETE FROM tinturas` directo por
   sqlite3 sin el pragma. Cada corrida de ese script real, ya usado por el
   usuario, deja filas huérfanas.

3. **Los tests prueban el repositorio equivocado.** `app.py` importa
   `TinturaSQLRepository` de `repository_sql.py`. Pero `test_ferneth_completo.py`
   (673 líneas, flujo completo) y `tests/test_tinturas.py` importan
   `TinturaRepository` del `repository.py` legacy (JSON). El camino de producción
   real (`repository_sql.py` + `DatabaseManager`) tiene cero cobertura. Además
   ningún test tiene un `assert` — son scripts que imprimen "✅ completado" sin
   verificar nada, y `tests/test_curvas.py` / `tests/test_ensamblaje.py` son stubs
   vacíos ("Archivo en desarrollo").

4. **Configuración no persiste.** `app.py` inicializa
   `st.session_state.config_sistema` con valores hardcodeados en cada sesión.
   Nunca llama a `load_settings()` ni `save_settings()` de `config/settings.py`
   (que sí existen y sí saben leer/escribir `config/settings.yaml`). Cualquier
   cambio de ABV/azúcar/pH objetivo, pesos de evaluación sensorial, o backup
   automático se pierde al cerrar la app.

5. **"Backup automático" es solo un checkbox.** `auto_backup` /
   `backup_frecuencia` se guardan en `session_state` (ni siquiera en disco, ver
   #4) pero nada los lee para disparar un backup real; solo el botón manual
   "📥 Hacer Backup Ahora" (shutil.copy2) funciona.

6. **Inconsistencias de documentación** (graphify, `semantically_similar_to`
   AMBIGUOUS): README dice que Amargos macera 16-18 días; ambos manuales PDF
   dicen 16-21 días. README dice que `pip install -r requirements.txt` instala
   `streamlit`/`plotly`; el archivo real no los tiene.

## Arquitectura y cambios

### 1. `requirements.txt`
Agregar `streamlit`, `plotly`, `reportlab` (versión mínima acorde a lo usado).
Mantener `matplotlib` (lo usa `modules/curvas/analyzer.py` para gráficos
estáticos, distinto de los interactivos de `plotly` en `app.py`).

### 2. Integridad referencial
- `modules/core/db_manager.py`: en `get_connection()`, ejecutar
  `conn.execute("PRAGMA foreign_keys = ON")` antes de `yield conn`.
- `limpiar_duplicados.py`: usar el mismo mecanismo (activar el pragma en su
  conexión sqlite3 directa, ya que no pasa por `DatabaseManager`) o, más simple,
  reescribirlo para usar `DatabaseManager`/`TinturaSQLRepository.eliminar()` en
  vez de SQL crudo — se prefiere esto último para que haya un solo camino de
  borrado en todo el sistema (agent decision, bajo costo, reversible).

### 3. Validaciones (`utils/validators.py`)
Implementar:
- `validar_composicion_botanica(composicion: List[ComposicionBotanica]) -> None`:
  lanza `ValueError` si la suma de `porcentaje` no está en `[99.5, 100.5]` (margen
  por redondeo) o si algún porcentaje es negativo.
- `validar_parametros_extraccion(parametros: ParametrosExtraccion) -> None`:
  lanza `ValueError` si `abv_objetivo` no está en `(0, 100]` o
  `tiempo_estimado_dias <= 0`.
Se llaman desde `Tintura.__post_init__` en `modules/tinturas/models.py` (si existe
`__post_init__`; si no, se agrega uno) — así la validación aplica sin importar
qué repositorio persista la tintura, incluyendo el futuro repositorio de Gancia
en Fase 2.

### 4. Persistencia real de Configuración
- Extender `config/settings.py`: agregar `@dataclass BackupSettings` (
  `auto_backup: bool`, `frecuencia: str`, `ultimo_backup: Optional[str]`) como
  campo de `FernetOSConfig`, con su bloque correspondiente en
  `config/settings.yaml` (`backup:`).
- En `app.py`, módulo Configuración: reemplazar la inicialización hardcodeada de
  `st.session_state.config_sistema["parametros"]`,
  `["pesos_evaluacion"]` y `["base_datos"]` por valores leídos de
  `load_settings()`; al guardar cambios (botón existente de guardar, o agregar
  uno si no existe), llamar a `save_settings()`.
- `notificaciones` y `apariencia` (tema/idioma) quedan fuera de esta migración
  (ver Deferred aspects) — se confirma explícitamente con el usuario antes de
  implementar si deben moverse también o quedar en sesión.

### 5. Backup automático real
Al construir `DatabaseManager` (o al arrancar `app.py`, punto único de entrada):
leer `ultimo_backup` y `frecuencia` desde `FernetOSConfig`; si
`auto_backup` es `True` y ha pasado más tiempo que la frecuencia configurada
(diaria/semanal) desde `ultimo_backup`, copiar la BD a
`data/fernetos_backup_<timestamp>.db` (mismo mecanismo que el botón manual) y
actualizar `ultimo_backup` vía `save_settings()`.

### 6. Suite de tests (pytest)
Nueva carpeta `tests/` (reemplaza el uso de la actual, que se mantiene pero se
reescribe) con, como mínimo:
- `tests/test_calculator.py`: `calcular_base_alcohol_agua`, `calcular_abv_blend`
  — casos conocidos con `assert` (ej. 10L/40% ABV → valores exactos verificables
  a mano).
- `tests/test_db_manager.py`: creación de esquema desde cero, y — caso crítico —
  que borrar una tintura con `TinturaSQLRepository.eliminar()` deja 0 filas en
  `composicion_botanica`/`parametros_extraccion`/`registros_curva` para ese id
  (regresión directa del hallazgo #2).
- `tests/test_repository_sql.py`: roundtrip completo sobre `TinturaSQLRepository`
  (guardar → get_by_id → listar → eliminar) usando una BD SQLite temporal —
  reemplaza el rol que cumplía `test_ferneth_completo.py` pero contra el
  repositorio real.
- `tests/test_validators.py`: casos válidos e inválidos de las dos funciones
  nuevas.
Todos con `assert` real (no prints). Se corren con `pytest` desde la raíz.

### 7. Limpieza
- Borrar `modules/tinturas/repository.py`, `modules/tinturas/repository_sql_simple.py`,
  `data/tinturas.db` (0 bytes). Confirmar con `grep` que nada los importa antes
  de borrar.
- Los archivos de test actuales en la raíz (`test_calculator.py`,
  `test_ferneth_completo.py`, `test_rutas.py`) y los stubs en `tests/` se
  reemplazan por la nueva suite del punto 6; se eliminan tras confirmar que la
  nueva suite cubre lo mismo (agent decision, reversible vía git).

### 8. Correcciones de documentación
- `README.md` línea ~119-131: corregir la lista de paquetes que instala
  `requirements.txt` para que coincida con el archivo real (incluir streamlit,
  plotly, reportlab).
- `README.md` línea ~449: corregir el rango de maceración de Amargos a 16-21
  días (confirmado por el usuario como el valor correcto, igual al de los
  manuales PDF).

## Testing
TDD para: `calculator.py`, `db_manager.py`, `repository_sql.py`, `validators.py`
(orden sugerido: validators → db_manager (FK) → repository_sql → calculator, de
menor a mayor dependencia). Sin TDD para la UI de Streamlit (persistencia de
Configuración, wiring de backup automático) — se verifica manualmente corriendo
la app.

## No-goals / alternativas rechazadas
- **Refactorizar `app.py`** en múltiples archivos/páginas: no se pidió, y
  partir un archivo de 4000 líneas sin necesidad funcional es scope creep para
  esta fase.
- **Modelar base vínica de Gancia aquí**: pertenece a la Fase 2 (spec separado).
- **Resiliencia multi-usuario/concurrencia**: descartado porque el usuario
  confirmó que la app no se usa en vivo durante la competencia.
- **Migrar completamente a un ORM** (SQLAlchemy, etc.) en vez de arreglar
  `db_manager.py`: cambio de arquitectura no solicitado y de alto costo para el
  beneficio marginal sobre simplemente activar el PRAGMA correcto.

## Deferred aspects

- **Persistencia de `notificaciones` y `apariencia`** (tema/idioma) en
  Configuración: quedan en `session_state` únicamente. Por qué: son cosméticos,
  no afectan el resultado de una receta ni el riesgo de pérdida de datos.
  Vuelve a estar en alcance si el usuario reporta que le molesta reconfigurar
  tema/idioma cada sesión. Encaja en el mismo mecanismo de `FernetOSConfig` ya
  extendido en este spec (agregar `NotificacionSettings`/`AparienciaSettings`
  análogos a `BackupSettings`).
- **Soporte para Gancia**: Fase 2, spec independiente
  (`docs/specs/2026-09-05-gancia-fase2.md` o el nombre que corresponda al
  crearlo), que reutilizará `BackupSettings`/`validators.py`/la suite de tests de
  esta fase como base.
- **Tests de `modules/curvas/analyzer.py`** (ajuste de curva con scipy,
  detección de punto óptimo): fuera de esta fase — es lógica de apoyo visual, no
  de cálculo de receta/dinero, y su testeo requiere fixtures de curvas más
  elaboradas. Vuelve a estar en alcance si se reporta un bug concreto en la
  sugerencia de punto de corte.

## Implementation guidance
- TDD: activado para `calculator.py`, `db_manager.py`, `repository_sql.py`,
  `validators.py` (lógica de negocio). No aplica a cambios de UI en `app.py`
  (persistencia de Configuración, wiring de backup) — verificación manual.
- Isolation: checkout actual (`main`), sin worktree — repo recién inicializado,
  un solo desarrollador.
- Verify: `pytest` (suite nueva completa, exit 0) antes de dar cualquier tarea
  por terminada. No hay typecheck configurado en el proyecto (sin mypy.ini/
  pyproject con mypy activo pese al `.mypy_cache/` presente) — no se agrega uno
  nuevo en este spec por no haber sido pedido.
- Review: `/code-review high` sobre el diff completo de la fase, una sola vez,
  al terminar todas las tareas y con la suite de tests en verde. Requiere que el
  repo tenga commits (ya inicializado y con baseline commiteado).
- Scope: construir solo lo que este spec especifica; cualquier extra se propone,
  no se construye.
- Deferred aspects: ver ledger arriba. Sin sistema de tracking externo — este
  spec es el registro canónico; al iniciar la Fase 2 revisar esta lista.
- Build order (riesgo/dependencia primero):
  1. `requirements.txt` (trivial, desbloquea instalación limpia)
  2. `validators.py` + wiring en `models.py` (aislado, sin dependencias)
  3. `PRAGMA foreign_keys` en `db_manager.py` + fix `limpiar_duplicados.py`
  4. Suite de tests nueva (`tests/test_db_manager.py`,
     `tests/test_repository_sql.py`, `tests/test_calculator.py`,
     `tests/test_validators.py`) — valida los 3 puntos anteriores
  5. Borrado de código muerto (repository.py legacy, repository_sql_simple.py,
     tests viejos) una vez la suite nueva los reemplaza
  6. Persistencia de Configuración (`BackupSettings` + wiring en `app.py`)
  7. Backup automático real (depende del punto 6)
  8. Correcciones de README (independiente, puede ir en paralelo)
- Routing: todo el trabajo es secuencial y depende de contexto acumulado del
  repo (qué se decidió borrar, qué settings.yaml quedó); lo ejecuta el
  orquestador directamente, sin delegar a subagentes — el volumen de código por
  tarea es pequeño y delegar no ahorraría tokens frente a reconstruir contexto.
- Orchestrator: modelo/effort actual de esta sesión (Opus, alto esfuerzo) —
  suficiente para el ítem más difícil (diseñar los tests de cascada FK); no se
  requiere downgrade ni upgrade.
