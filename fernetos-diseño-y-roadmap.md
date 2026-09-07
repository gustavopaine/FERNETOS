# FERNETOS — Diseño Técnico y Roadmap
## De herramienta de fernet casero a plataforma de formulación y competencia de bitters artesanales (Fernet · Americano/Gancia · Campari)

---

## 1. Resumen ejecutivo

El objetivo es transformar FERNETOS de una herramienta enfocada solo en fernet a una plataforma que permita:

1. **Formular** las tres familias de bebidas (Fernet, Americano estilo Gancia, Campari estilo aperitivo) sin mezclar su lógica, cada una con su propio perfil sensorial y reglas.
2. **Evaluar** esas fórmulas en competencias de cata a ciegas, con jurado y puntajes trazables.
3. **Construir marca**: usar los datos de formulación + resultados de torneo como evidencia objetiva de calidad para posicionar un producto propio de nivel regional.

La clave de diseño es: **compartir lo que es genuinamente común (tinturas, curvas de extracción, motor de blending) y separar completamente lo que es específico de cada bebida (perfil objetivo, rangos legales de ABV, criterios de cata, recetas base)**, para que nunca se mezcle una fórmula de fernet con una de Campari por accidente.

---

## 2. Diferencias de familia (por qué no pueden compartir un solo módulo)

| | **Fernet** | **Americano (estilo Gancia)** | **Campari (estilo aperitivo)** |
|---|---|---|---|
| Base | Alcohol destilado + maceración de hierbas/raíces | Vino aromatizado (base vínica) | Alcohol + infusión de cortezas/cítricos |
| ABV típico | 39–45% | 14.8–16% | 20–28% (herbal-style casero suele ser menor que el comercial 25°) |
| Perfil dominante | Amargor profundo, mentolado, especiado | Dulce-amargo, vainillado, floral, vermú | Amargo-cítrico, rojo intenso, quina |
| Maduración | 3–6 meses típico en competencias | Más corta, no siempre requiere añejamiento | Corta a media |
| Ingredientes clave | Mirra, azafrán, genciana, ruibarbo, manzanilla, menta | Ajenjo, vainilla, cáscaras cítricas, vino base | Cáscara de naranja amarga, genciana, ruibarbo, a veces quina |
| Categorías de cata típicas | Fernet Puro / Fernet con Cola | Americano Puro / Americano con soda | Campari Puro / Campari con soda o tónica |

Esto confirma la decisión de diseño: **un motor común, tres perfiles y tres calculadoras independientes que lo usan**.

---

## 3. Arquitectura propuesta

```
FERNETOS/
├── core/
│   ├── db_manager.py              # conexión y esquema compartido
│   ├── tintura_repository.py      # catálogo maestro de tinturas/botánicos
│   └── curve_analyzer.py          # análisis de curvas de extracción (genérico)
│
├── families/                      # ⚠️ nunca se importan entre sí
│   ├── fernet/
│   │   ├── fernet_profile.py      # rangos ABV, perfil sensorial objetivo, reglas
│   │   └── fernet_calculator.py   # lógica de formulación específica de fernet
│   │
│   ├── americano/
│   │   ├── americano_profile.py   # incluye lógica de base vínica
│   │   └── americano_calculator.py
│   │
│   └── campari/
│       ├── campari_profile.py
│       └── campari_calculator.py
│
├── shared/
│   ├── composicion_botanica.py    # recibe un "profile" como parámetro, no hardcodea familia
│   ├── microblending/
│   │   └── ab_testing.py          # comparación de variantes, cualquier familia
│   └── recipe_engine_factory.py   # RecipeEngineFactory.create("fernet"|"americano"|"campari")
│
├── evaluation/                    # 🆕 módulo de torneo (sección 5)
│   ├── models.py
│   ├── blind_coding.py
│   ├── scoring.py
│   └── ranking.py
│
└── app.py / streamlit UI
```

### Regla de oro anti-confusión
- **Ninguna familia importa código de otra familia.** Todo lo compartido vive en `core/` o `shared/` y recibe la familia como parámetro (`profile`), nunca como lógica condicional interna (`if familia == "fernet"` desperdigado por el código).
- El `tintura_repository` es único, pero cada tintura tiene una etiqueta `compatible_families: ["fernet", "campari"]` — así buscás "genciana" una sola vez y el sistema te dice en qué familias tiene sentido usarla, con qué rango de dosificación por familia.
- Cada familia tiene su propia tabla de recetas (`fernet_recipes`, `americano_recipes`, `campari_recipes`) o, si usan una tabla única, un campo `familia` indexado y **obligatorio**, nunca nulo.

### Modelo de datos simplificado

**Tintura (compartida)**
```
Tintura {
  id, nombre, categoria_botanica,
  indice_amargor, notas_aromaticas[],
  parametros_curva_extraccion,
  compatible_families: {fernet: {dosis_min, dosis_max}, 
                         americano: {...}, 
                         campari: {...}},
  costo_unitario, proveedor
}
```

**Receta (una tabla por familia, mismo esqueleto)**
```
FernetRecipe / AmericanoRecipe / CampariRecipe {
  id, nombre, version, estado (borrador/testing/lista_para_torneo),
  ingredientes: [{tintura_id, porcentaje}],
  abv_objetivo, tiempo_maceracion,
  perfil_sensorial_objetivo (json: amargor, dulzor, aromaticidad, cuerpo),
  notas_batch, fecha_creacion
}
```

---

## 4. Motor de cálculo generalizado

`RecipeEngineFactory` es el único punto de entrada:

```python
engine = RecipeEngineFactory.create("americano")
engine.buscar_tinturas(compatible_con="americano")
engine.calcular_curva(receta)
engine.comparar_variantes(receta_a, receta_b)  # usa ABTesting compartido
```

Cada `*_profile.py` define:
- Rango legal/técnico de ABV
- Perfil sensorial objetivo (vector: amargor, dulzor, herbáceo, cítrico, especiado, cuerpo)
- Reglas de validación específicas (ej: Americano requiere `base_vinica_pct >= X`)

Esto permite que **busques y diseñes cada bebida por separado**, sin que el sistema te deje, por ejemplo, guardar una "receta de Campari" con parámetros de maceración pensados para fernet.

---

## 5. Módulo de evaluación y torneo (cata a ciegas)

### 5.1 Entidades principales

```
Evento (Torneo) {
  id, nombre, fecha, sede, edicion_numero
}

Categoria {
  id, evento_id, familia (fernet/americano/campari),
  submodalidad ("puro" | "con_cola" | "con_soda" | "con_tonica")
}

Muestra {
  id, categoria_id, codigo_ciego,      # ej: "M-014" — NO se ve productor ni receta
  receta_id_interna (oculto hasta el cierre de la cata),
  productor_id (oculto hasta el cierre de la cata)
}

Jurado {
  id, nombre, rol (sommelier/bartender/productor/publico),
  peso_voto  # opcional: un sommelier puede pesar más que "experto popular"
}

Puntaje {
  id, muestra_id, jurado_id,
  visual, aroma, sabor_boca,   # ver rúbrica 5.2
  comentario_libre,
  timestamp
}

Ranking {
  categoria_id, muestra_id, puntaje_final, posicion
}
```

### 5.2 Rúbrica de puntaje (basada en los criterios reales del certamen)

| Criterio | Peso sugerido | Sub-aspectos |
|---|---|---|
| **Aspecto visual** | 15% | Color (marrón/rojo profundo según familia), limpieza, ausencia de sedimento |
| **Aroma** | 30% | Complejidad, equilibrio, ausencia de notas "medicinales" puras, presencia de notas herbáceas/especiadas/mentoladas |
| **Sabor y boca** | 55% | Balance amargor-dulzor, textura (denso/acuoso), persistencia post-trago |

Cada sub-aspecto se puntúa 1–10; el sistema calcula el puntaje ponderado por muestra y por jurado.

### 5.3 Anonimato y anti-sesgo
- **Codificación ciega**: al cargar una muestra, el sistema genera un `codigo_ciego` aleatorio. El vínculo receta↔código↔productor queda encriptado/oculto y solo se revela cuando el organizador cierra oficialmente la ronda.
- **Orden aleatorio de cata**: cada jurado recibe las muestras en un orden distinto (evita sesgo de "la primera siempre puntúa más alto").
- **Poda de outliers (opcional)**: al promediar los puntajes de todos los jurados, se puede descartar el puntaje más alto y el más bajo (media recortada) para reducir el efecto de un jurado muy severo o muy indulgente.

### 5.4 Formato del torneo

Dado que catar no es como un bracket deportivo (no se puede "eliminar por partido"), se recomienda:

1. **Ronda clasificatoria**: todas las muestras de una categoría se catan y puntúan → se seleccionan las N mejores (ej: top 5).
2. **Ronda final**: esas N vuelven a catarse, con jurado ampliado o más riguroso, para desempatar y definir el podio.
3. **Categorías independientes**: Fernet Puro, Fernet con Cola, Americano Puro, Americano con Soda, Campari Puro, Campari con Soda/Tónica — cada una con su propio ranking y premiación.

### 5.5 Salidas del módulo
- Planilla de resultados por categoría (exportable)
- Ficha de cata por muestra (para devolver feedback al productor)
- Histórico por productor/receta a través de ediciones (para vos: trazabilidad de qué versión de tu receta ganó qué año)

---

## 6. Roadmap completo del proyecto

### Fase 0 — Fundación técnica (2–3 semanas)
- [ ] Refactor de `FernetCalculator` actual: separar lo genérico (curvas, DB) de lo específico de fernet
- [ ] Crear `core/tintura_repository.py` con el catálogo maestro y etiquetado `compatible_families`
- [ ] Definir `fernet_profile.py` formalizando lo que hoy está implícito en el código

**Entregable:** el sistema actual sigue funcionando igual, pero ya organizado para extenderse.

### Fase 1 — Multi-familia (3–4 semanas)
- [ ] Crear `americano_profile.py` y `americano_calculator.py`
- [ ] Crear `campari_profile.py` y `campari_calculator.py`
- [ ] Implementar `RecipeEngineFactory`
- [ ] Migrar/crear tablas `americano_recipes` y `campari_recipes`
- [ ] Cargar catálogo inicial de tinturas típicas de cada familia (con dosis min/max por familia)

**Entregable:** podés crear, buscar y comparar recetas de las 3 bebidas por separado, sin cruces.

### Fase 2 — Módulo de evaluación y torneo (3–4 semanas)
- [ ] Modelos `Evento`, `Categoria`, `Muestra`, `Jurado`, `Puntaje`, `Ranking`
- [ ] Lógica de codificación ciega y aleatorización de orden de cata
- [ ] Cálculo de puntaje ponderado + media recortada
- [ ] Reportes exportables (PDF/Excel) por categoría y por muestra

**Entregable:** podés correr una cata a ciegas interna (con amigos/testers) de punta a punta.

### Fase 3 — Interfaz y experiencia (2–3 semanas)
- [ ] UI en Streamlit (ya insinuada en tu grafo de dependencias): pantalla de carga de jurado, planilla de puntajes en vivo, dashboard de resultados
- [ ] Panel de productor: ver histórico de tus propias recetas, versiones y cómo puntuaron
- [ ] Exportación de "ficha técnica" de receta (para eventual registro de marca o proveedor)

**Entregable:** herramienta usable en un evento real por jurados no técnicos.

### Fase 4 — Piloto en competencia real (según calendario de eventos regionales)
- [ ] Correr el sistema en una competencia chica/mediana (interna, de club o barrio)
- [ ] Recolectar feedback de jurados y productores
- [ ] Ajustar rúbrica de puntaje según fricciones detectadas

**Entregable:** validación real del sistema + primeros datos objetivos sobre tus propias recetas.

### Fase 5 — Marca y escalamiento
- [ ] Usar los datos históricos de torneo (puntajes, consistencia entre ediciones) como respaldo objetivo de calidad
- [ ] Definir identidad de marca para cada línea (Fernet / Americano / Campari) — pueden compartir "casa madre" pero con identidad visual y narrativa propia, igual que las familias de recetas están separadas en el código
- [ ] Evaluar registro de marca, packaging, y aspectos legales/habilitación para producción y venta (esto excede lo técnico, pero el sistema te da el respaldo de calidad para negociarlo)

---

## 7. Próximos pasos inmediatos (para pegar en Claude Code)

1. Pedile a Claude Code que audite `modules/ensamblaje/fernet_calculator.py` y `modules/curvas/analyzer.py` para identificar qué es genuinamente específico de fernet vs. qué es genérico — esa auditoría define el corte exacto de la Fase 0.
2. Empezá por `core/tintura_repository.py`: es la pieza que más rápido te da valor (poder buscar y filtrar tinturas por familia) y no rompe nada del sistema actual.
3. Recién después de tener el repositorio de tinturas generalizado, avanzá con `americano_calculator.py` y `campari_calculator.py` en paralelo.

