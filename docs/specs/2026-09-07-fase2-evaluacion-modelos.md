Status: Approved (2026-09-07) — /code-review high aplicado

# Fase 2 (1/N): modelos de evaluacion/torneo

## Review summary

Primer slice de la Fase 2 del roadmap (`fernetos-diseño-y-roadmap.md`,
seccion 5): las entidades del modulo de evaluacion/cata a ciegas
(`Evento`, `Categoria`, `Muestra`, `Jurado`, `Puntaje`, `Ranking`) en
`evaluation/models.py`, con TDD por decision explicita del usuario para
esta logica (ver `tests/test_evaluation_models.py`, escritos antes que
la implementacion).

**Decisiones tomadas por mi cuenta** (arquitectura/naming, no hechos de
dominio):
- `Categoria.familia` reutiliza `core.validators.validar_familia_receta`
  en vez de duplicar el chequeo de nombre de familia una tercera vez.
- `Muestra.codigo_ciego` se genera random (`M-XXXX` hex), no secuencial:
  un codigo secuencial filtraria el orden de carga de las muestras, lo
  que debilitaria el anonimato que pide la seccion 5.3.
- `Puntaje.puntaje_ponderado()` vive en el propio dataclass (formula
  simple de 3 terminos con los pesos fijos de la rubrica 5.2), no en un
  modulo `scoring.py` aparte todavia — eso se justifica cuando aparezca
  la logica de agregar puntajes de varios jurados + media recortada
  (siguiente slice).
- `Muestra.receta_id_interna`/`productor_id` son `Optional[str] = None`
  por defecto; el modelo no implementa ocultamiento/encriptado real (eso
  es responsabilidad de la capa de persistencia + control de acceso,
  todavia no construida) — documentado como no-hecho, no simulado.

## Hallazgo de `/code-review high` aplicado

`Muestra.codigo_ciego` se generaba con 4 hex chars (65k combinaciones),
sin ninguna garantia de unicidad entre muestras de la misma categoria —
en una competencia real con decenas de muestras la probabilidad de
colision no es despreciable, y una colision rompe el anonimato que todo
el modulo existe para garantizar (seccion 5.3). Ampliado a 6 hex chars
(~16.7M combinaciones) como mitigacion barata en este slice. La garantia
real (UNIQUE a nivel de repositorio + regenerar en colision, mismo
patron que `UNIQUE(tintura_id, familia)` en `compatibilidad_familias`)
queda explicitamente para el slice de persistencia SQL de abajo — un
dataclass sin registro de instancias no tiene forma de chequear contra
otras `Muestra` ya creadas.

## Que NO hace (deferred, siguientes slices de Fase 2)

- Persistencia SQL (repositorio + tablas de schema) para estas
  entidades, incluyendo la restriccion UNIQUE real de `codigo_ciego` por
  categoria.
- Codificacion ciega real con aleatorizacion de orden de cata por
  jurado.
- Agregacion de puntajes de multiples jurados con media recortada
  (poda de outliers, seccion 5.3) y calculo de `Ranking`.
- Reportes exportables.
- UI en `app.py`.

## Verificacion

- `python -m pytest -q`: 151 passed (131 previos + 20 nuevos).
- `python -m py_compile evaluation/models.py tests/test_evaluation_models.py`: sin errores.
