📚 MANUAL COMPLETO DE FERNETOS
Sistema de Formulación para Amari Competitivos
Bienvenido a FernetOS, un sistema profesional diseñado para ayudarte a crear, controlar y optimizar la producción de fernet y otros amari de manera precisa y repetible. Este manual te guiará paso a paso desde la instalación hasta la producción de tu primer lote competitivo.

📑 TABLA DE CONTENIDOS
Introducción

Requisitos del Sistema

Instalación Paso a Paso

Estructura del Proyecto

Conceptos Fundamentales

Flujo de Trabajo Completo

Módulo 1: Panel de Control

Módulo 2: Gestión de Tinturas

Módulo 3: Curvas de Extracción

Módulo 4: Ensamblaje

Módulo 5: Micromezclas

Módulo 6: Pruebas A/B

Módulo 7: Gestión de Stock

Módulo 8: Configuración

Recetas de Ejemplo

Solución de Problemas

Glosario de Términos

🎯 INTRODUCCIÓN
FernetOS es un sistema de gestión de formulación diseñado específicamente para la producción de fernet y otros amari. A diferencia de métodos artesanales tradicionales, este sistema te permite:

✅ Control preciso sobre cada variable del proceso

✅ Repetibilidad entre lotes (mismo resultado siempre)

✅ Trazabilidad completa de cada ingrediente

✅ Optimización basada en datos reales

✅ Escalabilidad desde 10L hasta 1000L

✅ Ventaja competitiva en catas a ciegas

El sistema está construido sobre tinturas modulares: en lugar de macerar todas las hierbas juntas, creamos extractos individuales (tinturas) que luego combinamos como si fueran ingredientes líquidos. Esto nos da un control milimétrico sobre el perfil final.

💻 REQUISITOS DEL SISTEMA
Hardware mínimo:
Procesador: Intel Core i3 o equivalente

RAM: 4 GB (recomendado 8 GB)

Almacenamiento: 1 GB libres

Resolución de pantalla: 1280x720 o superior

Software necesario:
Sistema operativo: Windows 10/11, macOS 12+, o Linux (Ubuntu 20.04+)

Python: Versión 3.9 o superior

Navegador: Chrome, Firefox, Edge o Safari (actualizado)

Conocimientos previos:
No se requiere experiencia en programación

Conocimientos básicos de manejo de archivos

Comprensión de conceptos básicos de maceración (deseable)

📥 INSTALACIÓN PASO A PASO
Paso 1: Verificar Python
Abre una terminal (PowerShell en Windows, Terminal en Mac/Linux) y ejecuta:

bash
python --version
Deberías ver algo como Python 3.9.13 o superior. Si no tienes Python, descárgalo de python.org.

Paso 2: Descargar el proyecto
Opción A - Si tienes Git:

bash
git clone https://github.com/tuusuario/fernetos.git
cd fernetos
Opción B - Descarga directa:

Ve a la página del proyecto

Haz clic en "Download ZIP"

Descomprime el archivo en una carpeta (ej: C:\Users\TuUsuario\Documents\fernetos)

Paso 3: Crear entorno virtual (recomendado)
En Windows:

bash
python -m venv venv
venv\Scripts\activate
En Mac/Linux:

bash
python3 -m venv venv
source venv/bin/activate
Verás que el prompt cambia a (venv) indicando que el entorno virtual está activo.

Paso 4: Instalar dependencias
bash
pip install -r requirements.txt
Esto instalará:

streamlit - La interfaz web

pandas - Manejo de datos

numpy - Cálculos numéricos

matplotlib - Gráficos estáticos de curvas de extracción

plotly - Gráficos interactivos

scipy - Análisis de curvas

pyyaml - Archivos de configuración

reportlab - Generación de manuales en PDF

Paso 5: Inicializar la base de datos
bash
python inicializar_bd_fernet.py
Verás una salida como esta:

text
======================================================================
🌿 FERNETOS - INICIALIZACIÓN DE BASE DE DATOS
======================================================================
📦 Creando tinturas para fernet competitivo...
✅ Amargos: T-20260221-8D2A - Amargos Estructurales Premium
✅ Aromática: T-20260221-F448 - Aromática Alta Premium
✅ 7 tinturas creadas correctamente
¡Felicidades! Ya tienes el sistema instalado con datos de ejemplo.

Paso 6: Ejecutar la aplicación
bash
streamlit run app.py
Se abrirá automáticamente tu navegador en http://localhost:8501 mostrando el panel de control de FernetOS.

Paso 7: Detener la aplicación
Para salir, presiona Ctrl+C en la terminal donde se está ejecutando.

📁 ESTRUCTURA DEL PROYECTO
text
fernetos/
│
├── 📂 data/                          # Todos los datos persistentes
│   ├── fernetos.db                    # Base de datos SQLite
│   ├── 📂 curves/                      # Gráficos generados
│   ├── 📂 tests/                        # Resultados de pruebas
│   └── 📂 schema/                        # Esquemas de base de datos
│
├── 📂 modules/                        # Código del sistema
│   ├── 📂 core/                         # Módulos base
│   │   └── db_manager.py                 # Gestor de base de datos
│   │
│   ├── 📂 tinturas/                     # Gestión de tinturas
│   │   ├── models.py                      # Modelos de datos
│   │   ├── repository.py                   # Repositorio JSON (legacy)
│   │   └── repository_sql.py                # Repositorio SQL
│   │
│   ├── 📂 curvas/                        # Análisis de curvas
│   │   └── analyzer.py                     # Analizador de curvas
│   │
│   ├── 📂 ensamblaje/                    # Cálculos de blends
│   │   └── calculator.py                    # Calculadora
│   │
│   ├── 📂 microblending/                  # Microajustes
│   │   ├── pilot_batch.py                   # Lotes piloto
│   │   └── ab_testing.py                     # Pruebas A/B
│   │
│   └── 📂 sensory/                        # Evaluación sensorial
│       └── models.py                         # Modelos de cata
│
├── 📂 config/                          # Configuración
│   └── settings.py                       # Parámetros del sistema
│
├── 📂 tests/                            # Scripts de prueba
│   └── test_tinturas.py                   # Pruebas unitarias
│
├── app.py                              # Interfaz principal (Streamlit)
├── inicializar_bd_fernet.py             # Inicialización de BD
├── check_db.py                          # Verificador de BD
├── requirements.txt                     # Dependencias
└── README.md                            # Este manual
🧠 CONCEPTOS FUNDAMENTALES
¿Qué es una tintura?
Una tintura es un extracto líquido obtenido al macerar hierbas, raíces o especias en alcohol. En FernetOS, cada tintura es como un "ingrediente líquido" que contiene los compuestos de una sola planta o de un grupo funcional específico.

Ejemplo: Tintura de Genciana = raíz de genciana + alcohol al 70% macerado por 18 días.

¿Por qué trabajar con tinturas separadas?
Maceración Conjunta	Sistema Modular de Tinturas
Todas las hierbas juntas	Cada hierba por separado
Si una domina, arruina el lote	Control individual
Imposible ajustar	Se puede corregir
Resultado variable	Resultado repetible
Dependiente de la cosecha	Independiente de variaciones
Grupos funcionales de tinturas
Grupo	Función	Ejemplos
Amargos estructurales	Base de amargor	Genciana, Ruibarbo, Quina
Aromática alta	Perfil herbal fresco	Menta, Romero, Cardo, Azafrán
Especias cálidas	Profundidad y calidez	Canela, Cardamomo, Clavo, Nuez
Cítricos	Brillo y frescura	Naranja amarga, Limón
Correctivos	Ajustes finos	Regaliz, Clavo controlado
Parámetros clave de una tintura
ABV (%): Graduación alcohólica del alcohol utilizado

Ratio planta/alcohol: Proporción (ej: 1:5 = 200g por litro)

Tiempo de maceración: Días de extracción

Punto de corte: Momento óptimo para filtrar

🔄 FLUJO DE TRABAJO COMPLETO
text
┌─────────────────┐
│ 1. Crear tintura│
└────────┬────────┘
         ↓
┌─────────────────┐
│2. Registrar catas│ ← Cada 48h
└────────┬────────┘
         ↓
┌─────────────────┐
│3. Analizar curva│ ← Detectar punto óptimo
└────────┬────────┘
         ↓
┌─────────────────┐
│4. Filtrar y     │
│   estabilizar   │
└────────┬────────┘
         ↓
┌─────────────────┐
│5. Stock disponible│
└────────┬────────┘
         ↓
┌─────────────────┐
│6. Crear blend   │ ← Ensamblar tinturas
└────────┬────────┘
         ↓
┌─────────────────┐
│7. Microblending │ ← Ajustes de 0.1ml
└────────┬────────┘
         ↓
┌─────────────────┐
│8. Pruebas A/B   │ ← Vs referencias
└────────┬────────┘
         ↓
┌─────────────────┐
│9. Escalar a     │
│   producción    │
└─────────────────┘
📊 MÓDULO 1: PANEL DE CONTROL
El panel de control es tu vista principal. Aquí verás un resumen de todo el sistema.

📋 Qué muestra:
Métricas principales (arriba):

Tinturas en Maceración: Las que están extrayéndose

Tinturas Listas: Disponibles para usar

Ensayos Activos: Blends en desarrollo

Mezclas históricas: Total de blends creados

Gráfico de actividad: Muestra las catas registradas y nuevas tinturas en los últimos 14 días.

Estado del sistema (barra lateral):

Versión del sistema

Base de datos conectada

Último acceso

🎯 Para qué sirve:
Monitoreo rápido del estado general

Detectar actividad reciente

Verificar que todo funciona

🧪 MÓDULO 2: GESTIÓN DE TINTURAS
Este es el corazón del sistema. Aquí crearás y gestionarás todas tus tinturas.

📋 Pestaña "Listado"
Filtros disponibles:

Estado: en_maceracion, en_estabilizacion, lista, agotada

Grupo: amargos, aromática, especias, cítricos, correctivos

Búsqueda: por nombre o ID

Columnas de la tabla:

ID único de la tintura

Nombre

Grupo funcional

Estado actual

Días transcurridos

Volumen disponible

Fecha de inicio

Ver detalle: Selecciona una tintura para ver:

Composición botánica completa

Parámetros de extracción

Fechas clave

➕ Pestaña "Nueva Tintura"
Paso 1: Datos básicos

Nombre: Ej: "Amargos Estructurales Mar24"

Grupo funcional: Selecciona según función

ABV objetivo: Graduación alcohólica (ej: 70%)

Peso materia seca: Gramos de hierbas

Volumen alcohol: Mililitros de alcohol

Tiempo estimado: Días de maceración

Paso 2: Composición botánica

Número de especies: Cuántas hierbas diferentes

Para cada especie:

Especie: Nombre de la planta

%: Porcentaje en la mezcla

Parte utilizada: raíz, corteza, hoja, etc.

Paso 3: Observaciones

Notas sobre lote, procedencia, etc.

Ejemplo práctico - Tintura de Amargos:

text
Nombre: Amargos Estructurales Premium
Grupo: amargos_estructurales
ABV: 70%
Peso: 500g
Volumen: 2500ml
Tiempo: 18 días

Composición:
- Genciana: 55% (raíz)
- Ruibarbo: 35% (raíz)
- Quina: 5% (corteza)
- Angélica: 5% (raíz)
📊 Pestaña "Estadísticas"
Gráfico de torta: Distribución por grupo funcional

Gráfico de barras: Tinturas por estado

📈 MÓDULO 3: CURVAS DE EXTRACCIÓN
Este módulo te permite seguir la evolución de cada tintura durante la maceración y detectar el punto óptimo de corte.

🔍 Seleccionar tintura
Elige una tintura en maceración del desplegable. Verás:

Nombre y grupo

Estado actual

Días transcurridos

Corte estimado

📝 Registrar nueva cata (cada 48h)
Campos del formulario:

Día: Número de día de maceración

Intensidad: Percepción global (0-100)

Notas sensoriales: Descripción libre

Compuestos detectados: Selecciona múltiples

Color: Observación visual

Turbidez: claro, ligera, media, alta

Aroma: Descripción del olor

📌 IMPORTANTE: Registra catas cada 48h para tener una curva precisa. Sin datos, el sistema no puede sugerir el punto óptimo.

📊 Visualización de la curva
El gráfico muestra:

Puntos azules: Tus catas registradas

Línea azul: Tendencia de extracción

Línea verde punteada: Día óptimo sugerido

Gráfico inferior: Velocidad de extracción

⚠️ Alertas
El sistema te avisará si:

Hay riesgo de sobreextracción

Aparecen compuestos no deseados

Se acerca el punto de corte

🏁 Cuándo cortar
El sistema sugiere un día óptimo basado en:

La curva de extracción

La aparición de compuestos

El grupo funcional de la tintura

Regla general por grupo:

Amargos: 16-21 días

Aromática alta: 5-7 días

Especias: 10-14 días

Cítricos: 3-4 días

Clavo: 48h máximo

🧮 MÓDULO 4: ENSAMBLAJE
Aquí combinarás tus tinturas para crear blends (mezclas) de fernet.

⚙️ Parámetros del blend
Volumen objetivo: Litros totales a producir

ABV objetivo: Graduación alcohólica deseada

Azúcar (g/L): Gramos de azúcar por litro

🧪 Selección de tinturas
El sistema muestra todas las tinturas disponibles en stock. Para cada una:

Nombre

Stock disponible (ml)

Grupo funcional

Campo para ingresar ml a usar

📋 Resumen de selección
Antes de calcular, verás:

Tabla con tinturas seleccionadas

Volumen total de tinturas

🧮 Cálculo del blend
Al hacer clic en "Calcular Blend", el sistema:

Calcula el ABV resultante

Determina alcohol base y agua necesarios

Calcula el azúcar requerido

Muestra la receta completa

Resultados:

ABV calculado: Debe coincidir con el objetivo

Volumen total: Con aporte del azúcar

Alcohol base: Alcohol 96% necesario

Agua base: Agua para dilución

Distribución porcentual: % de cada componente

📝 Receta generada
Ejemplo para 10L:

text
=== RECETA PARA 10L DE FERNET ===

ALCOHOL BASE:
- Alcohol 96%: 3750 ml
- Agua: 5750 ml

TINTURAS:
- Amargos Estructurales Premium: 250 ml
- Aromática Alta Premium: 180 ml
- Especias Cálidas Premium: 120 ml
- Cítricos Premium: 80 ml

AZÚCAR:
- Azúcar: 1950 g

--- VOLUMEN FINAL: 10.2 L ---
🎯 MÓDULO 5: MICROMEZCLAS
Este es el módulo de ajuste fino. Permite hacer iteraciones de 0.1ml para optimizar un blend.

⚙️ Configuración inicial
Crear blend base:

Define volumen, ABV y azúcar

Selecciona tinturas y cantidades

Haz clic en "Iniciar Microblending"

🔧 Aplicar ajustes
Por cada iteración:

Selecciona tintura a ajustar

Incremento: +0.1ml, -0.2ml, etc.

Razón: por qué haces el ajuste

Observación: nota descriptiva

Ejemplo de iteraciones:

text
Iteración 1: +0.3ml cítricos (buscar más ataque)
Iteración 2: +0.1ml clavo controlado (más complejidad)
Iteración 3: -0.2ml amargos (suavizar)
📊 Evaluación sensorial
Por cada iteración, puedes registrar una evaluación:

Ataque (1-10)

Complejidad (1-10)

Equilibrio (1-10)

Persistencia (1-10)

Notas de cata

📈 Resultados
El sistema muestra:

Evolución del puntaje por iteración

Mejor iteración encontrada

Perfil sensorial en gráfico radar

📏 Escalar a producción
Cuando encuentres la iteración óptima:

Selecciona volumen de producción (ej: 40L)

El sistema escala automáticamente

Genera receta para producción

⚖️ MÓDULO 6: PRUEBAS A/B
Este módulo te permite comparar tus blends contra referencias de mercado (Branca, Vittone, etc.) mediante pruebas a ciegas.

🎯 Tipos de prueba
A/B Simple:

Dos muestras: nuestra fórmula vs referencia

Catador elige cuál prefiere

Triangular:

Tres muestras: dos iguales, una diferente

Catador identifica la diferente

Útil para detectar si hay diferencia perceptible

⚙️ Configurar prueba
Nuestra fórmula:

Seleccionar de iteraciones de microblending

O crear blend personalizado

Referencia:

Branca, Vittone, 1882, etc.

O personalizar

Parámetros:

Número de catadores

Prueba a ciegas (recomendado)

Atributos a evaluar

📝 Registrar resultados
Por cada catador:

Preferencia (en A/B Simple)

Muestra diferente (en Triangular)

Puntajes por atributo (1-10)

Comentarios

📊 Análisis estadístico
El sistema calcula:

Preferencia neta: % que prefiere nuestra fórmula

Tasa de aciertos: En prueba triangular

Significancia: Si la diferencia es estadísticamente significativa

Gráfico radar: Comparativa de perfiles

📋 Interpretación de resultados
Si nuestra fórmula gana:

✅ Lista para escalar

✅ Ventaja competitiva confirmada

Si hay empate:

⚠️ Seguir ajustando

Probar con más catadores

Si gana la referencia:

🔄 Revisar formulación

Identificar atributos débiles

📦 MÓDULO 7: GESTIÓN DE STOCK
Controla el inventario de todas tus tinturas.

📋 Inventario
Columnas:

ID y nombre de tintura

Grupo funcional

Estado actual

Volumen disponible

Estado de stock: 🟢 Normal, 🟠 Bajo, 🟡 Crítico, 🔴 Agotado

Ubicación en almacén

Días restantes (si aplica)

Filtros:

Por estado

Por grupo

Búsqueda por nombre

📊 Análisis de stock
Gráficos:

Distribución por estado

Distribución por grupo

Volumen por grupo

Proyección de consumo:

Define consumo diario estimado (ml/día)

Selecciona horizonte (7, 15, 30, 60, 90 días)

El sistema muestra días disponibles por tintura

Alertas de stock bajo

📝 Movimientos
Registra cada entrada o salida de stock:

Tipo: Entrada, Salida, Ajuste, Pérdida

Volumen

Motivo: Ensamblaje #123, Nuevo lote, etc.

Observaciones

Historial: Últimos 50 movimientos con trazabilidad completa.

⚡ Acciones rápidas
Actualizar ubicación: Cambiar estante

Ajustar volumen: Corrección manual

Marcar agotada: Cambiar estado

⚙️ MÓDULO 8: CONFIGURACIÓN
Personaliza el sistema según tus preferencias.

🎯 Parámetros técnicos
Define valores por defecto:

ABV: mínimo, máximo y por defecto

Azúcar: rangos y valor por defecto

pH: rangos y valor por defecto

⚖️ Pesos de evaluación
Define la importancia relativa de cada atributo en el puntaje total:

Ataque

Complejidad

Equilibrio

Persistencia

Amargor

La suma debe ser 1.0

🔔 Notificaciones
Configura qué alertas quieres recibir:

Sobreextracción

Recordatorio de catas

Stock bajo

Corte próximo

Frecuencia: inmediata, diaria, semanal

🎨 Apariencia
Tema: Claro, Oscuro, Sistema

Idioma: Español, English, Português

Configuración de gráficos

💾 Base de datos
Información:

Ubicación de la BD

Tamaño

Número de registros

Acciones:

Backup manual: Guardar copia

Verificar integridad: Comprobar BD

Optimizar: Reducir tamaño (VACUUM)

Restaurar backup: Volver a versión anterior

👤 Usuario
Datos personales

Cambio de contraseña

Preferencias del dashboard

Exportar configuración

🍸 RECETAS DE EJEMPLO
Receta 1: Fernet Competitivo (Perfil Equilibrado)
Para 10L finales:

Componente	Volumen	Función
Alcohol 96%	3750 ml	Base alcohólica
Agua	5750 ml	Dilución
Azúcar	1950 g	Dulzor
Tinturas:

Tintura	Volumen	% del blend
Amargos Estructurales	250 ml	2.5%
Aromática Alta	180 ml	1.8%
Especias Cálidas	120 ml	1.2%
Cítricos	80 ml	0.8%
Clavo Controlado	2 ml	0.02%
Perfil esperado:

ABV: 40%

Azúcar: 195 g/L

Amargor: 8/10

Ataque: Cítrico-herbal

Persistencia: Media-alta

Receta 2: Fernet Intenso (Alto Amargor)
Tinturas:

Tintura	Volumen
Amargos Estructurales	350 ml
Aromática Alta	150 ml
Especias Cálidas	100 ml
Cítricos	50 ml
Regaliz Correctivo	30 ml
Receta 3: Fernet Suave (Perfil Comercial)
Tinturas:

Tintura	Volumen
Amargos Estructurales	180 ml
Aromática Alta	220 ml
Especias Cálidas	80 ml
Cítricos	120 ml
Regaliz Correctivo	50 ml
Azúcar	210 g/L
🔧 SOLUCIÓN DE PROBLEMAS
Error: "No module named 'modules'"
Causa: Python no encuentra los módulos del sistema.

Solución: Ejecuta desde la raíz del proyecto:

bash
cd C:\Users\TuUsuario\Documents\fernetos
python app.py
Error: "Base de datos no encontrada"
Causa: No se ha inicializado la BD.

Solución:

bash
python inicializar_bd_fernet.py
Error: "Port 8501 is already in use"
Causa: Ya hay una instancia de Streamlit ejecutándose.

Solución:

Cierra la terminal anterior

O mata el proceso:

Windows: taskkill /f /im streamlit.exe

Mac/Linux: pkill -f streamlit

Error: "Value below min_value" en Curvas
Causa: Días transcurridos negativo.

Solución: El sistema ya maneja esto automáticamente. Si persiste, reinicia la app.

Las tinturas no aparecen en stock
Causa: Las tinturas no están en estado "lista".

Solución: En el módulo de tinturas, finaliza la maceración y estabiliza.

Los gráficos no se muestran
Causa: Falta instalar plotly.

Solución:

bash
pip install plotly
La app está muy lenta
Causa: Muchos registros en la BD.

Solución: Optimizar base de datos (Configuración → Base de Datos → Optimizar)

📖 GLOSARIO DE TÉRMINOS
Término	Definición
ABV	Alcohol By Volume - Graduación alcohólica
Blend	Mezcla de tinturas para crear fernet
Cata	Evaluación sensorial de una muestra
Cold crash	Enfriamiento para precipitar ceras
Compuestos	Moléculas extraídas (taninos, glucósidos, etc.)
Curva de extracción	Evolución de la intensidad durante la maceración
Ensamblaje	Proceso de mezclar tinturas
Eugenol	Compuesto del clavo (muy potente)
Genciana	Raíz amarga base del fernet
Glucósidos	Compuestos responsables del amargor
Grupo funcional	Clasificación por función (amargos, aromáticos, etc.)
Iteración	Versión de un blend con ajustes
Limoneno	Compuesto cítrico
Louching	Enturbiamiento por aceites esenciales
Maceración	Extracción de compuestos en alcohol
Microblending	Ajustes finos de 0.1ml
pH	Acidez (menor pH = más ácido)
Punto de corte	Momento óptimo para filtrar
Quina	Corteza amarga
Ratio	Proporción planta/alcohol
Referencia	Producto del mercado (Branca, Vittone)
Regaliz	Raíz dulce que suaviza el amargor
Ruibarbo	Raíz que aporta persistencia
Sobreextracción	Macerar más allá del punto óptimo
Taninos	Compuestos que dan astringencia
Terpenos	Compuestos aromáticos volátiles
Tintura	Extracto alcohólico de una planta
Trazabilidad	Capacidad de seguir el historial
🏁 CONCLUSIÓN
¡Felicidades! Ahora tienes todo lo necesario para usar FernetOS como un profesional. Recuerda:

Siempre registra catas cada 48h - sin datos no hay control

Confía en el punto óptimo sugerido por el sistema

Microblending es la clave para ganar catas

Pruebas A/B validan tu trabajo

El stock es tu dinero - mantenlo controlado

Flujo de trabajo recomendado para principiantes:
Semana 1-2:

Crear tinturas de ejemplo

Practicar registro de catas

Familiarizarse con la interfaz

Semana 3-4:

Crear primeros blends

Probar microblending básico

Registrar evaluaciones

Semana 5-6:

Pruebas A/B contra referencias

Optimizar según resultados

Escalar a producción

Producción regular:

Mantener stock de tinturas base

Microblending para nuevas variantes

Validación continua

📞 SOPORTE
Si encuentras algún problema o tienes dudas:

📧 Email: soporte@fernetos.com

💬 Discord: FernetOS Community

📚 Wiki: docs.fernetos.com

🐛 Reportar bugs: GitHub Issues

¡A producir fernet de clase mundial! 🍸🏆

