"""
Interfaz gráfica FernetOS con Streamlit.
Panel de control para operación diaria de formulación de fernet competitivo.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import sys
import os
from datetime import datetime, timedelta
import time

# Configurar página ANTES de cualquier otro comando de Streamlit
st.set_page_config(
    page_title="FernetOS",
    page_icon="🍸",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Asegurar que Python encuentra los módulos
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


# =========================================================
# INICIALIZACIÓN DEL SISTEMA
# =========================================================
def _verificar_backup_automatico(db):
    """Hace un backup real si corresponde según la configuración guardada.

    Se llama una sola vez por arranque (init_system está cacheado con
    @st.cache_resource). No falla el arranque de la app si el backup no se
    puede hacer: solo se registra el error.
    """
    from config.settings import load_settings, save_settings, backup_es_necesario

    try:
        # DatabaseManager() ya crea el archivo .db si no existía (con las
        # tablas vacías) antes de llegar acá, así que comprobar sólo la
        # existencia del archivo nunca evita el backup en una instalación
        # nueva. Lo que realmente queremos evitar es respaldar una BD vacía.
        conteo = db.ejecutar("SELECT COUNT(*) as total FROM tinturas")
        if not conteo or conteo[0]["total"] == 0:
            return

        cfg = load_settings()
        ahora = datetime.now()
        if backup_es_necesario(cfg.backup, ahora):
            import shutil

            backup_path = db.db_path.replace(
                ".db", f'_backup_{ahora.strftime("%Y%m%d_%H%M%S")}.db'
            )
            shutil.copy2(db.db_path, backup_path)
            cfg.backup.ultimo_backup = ahora.strftime("%d/%m/%Y %H:%M")
            save_settings(cfg)
    except Exception as e:
        # No debe impedir que la app arranque, pero tampoco fallar en silencio
        st.warning(f"⚠️ No se pudo hacer el backup automático: {e}")


@st.cache_resource
def init_system():
    """Inicializa los componentes del sistema (cacheado)"""
    try:
        from modules.core.db_manager import DatabaseManager
        from core.tintura_repository import TinturaSQLRepository
        from families.fernet.calculator import FernetCalculator
        from core.curve_visualizer import CurveVisualizer
        from modules.microblending.ab_testing import ABTesting

        # Crear directorios necesarios
        os.makedirs("data", exist_ok=True)
        os.makedirs("data/curves", exist_ok=True)
        os.makedirs("data/tests", exist_ok=True)
        os.makedirs("data/schema", exist_ok=True)

        db = DatabaseManager()
        _verificar_backup_automatico(db)
        repo = TinturaSQLRepository(db)
        calculator = FernetCalculator()
        visualizer = CurveVisualizer(output_dir="data/curves")
        ab_testing = ABTesting(output_dir="data/tests")

        return db, repo, calculator, visualizer, ab_testing
    except Exception as e:
        st.error(f"❌ Error inicializando sistema: {e}")
        import traceback

        st.error(traceback.format_exc())
        return None, None, None, None, None


# Inicializar
db, repo, calculator, visualizer, ab_testing = init_system()

# Verificar inicialización
if repo is None:
    st.error(
        """
    ⚠️ **Error crítico: No se pudo inicializar el sistema**
    
    Posibles causas:
    - Error en la base de datos
    - Problemas de importación
    - Clases no definidas correctamente
    
    Revisa la consola para más detalles.
    """
    )
    st.stop()


# =========================================================
# FUNCIONES AUXILIARES
# =========================================================
def formato_fecha(fecha):
    """Formatea fecha para mostrar"""
    if fecha:
        return fecha.strftime("%d/%m/%Y %H:%M")
    return "N/A"


def get_grupo_color(grupo):
    """Retorna color para cada grupo funcional"""
    colores = {
        "amargos_estructurales": "#1f77b4",  # azul
        "aromatica_alta": "#ff7f0e",  # naranja
        "especias_calidas": "#2ca02c",  # verde
        "citricos": "#d62728",  # rojo
        "correctivos": "#9467bd",  # púrpura
        "quinados": "#17becf",  # celeste
        "botanicos_aromaticos": "#bcbd22",  # oliva
        "citricos_amargos": "#e377c2",  # rosa
        "especiado_suave": "#8c9eff",  # lavanda
        "raices_aromaticas": "#556b2f",  # verde oliva oscuro
        "amaderados": "#a0522d",  # marrón madera
        "colorantes_naturales": "#c71585",  # magenta (hibisco)
        "experimental": "#8c564b",  # marrón
    }
    return colores.get(grupo, "#7f7f7f")


# =========================================================
# BARRA LATERAL
# =========================================================
with st.sidebar:
    st.markdown(
        """
    <div style='text-align: center; padding: 10px;'>
        <h1 style='color: #FF4B4B;'>🍸 FernetOS</h1>
    </div>
    """,
        unsafe_allow_html=True,
    )

    st.caption("Sistema de Formulación para Amari Competitivos")

    st.divider()

    # Menú principal
    menu = st.radio(
        "Módulo",
        [
            "📊 Panel de control",
            "🧪 Tinturas",
            "📈 Curvas de Extracción",
            "🧮 Ensamblaje",
            "🍷 Ensamblaje Gancia",
            "🎯 Micromezclas",
            "🎯 Micromezclas Gancia",
            "⚖️ Pruebas A/B",
            "⚖️ Pruebas A/B Gancia",
            "📦 Stock",
            "⚙️ Configuración",
            "🏆 Torneo",
        ],
    )

    st.divider()

    # Estado del sistema
    st.subheader("📡 Estado del Sistema")

    if repo:
        try:
            tinturas_activas = len(repo.listar(estado="en_maceracion"))
            tinturas_listas = len(repo.listar(estado="lista"))

            col1, col2 = st.columns(2)
            with col1:
                st.metric("Activas", tinturas_activas)
            with col2:
                st.metric("Listas", tinturas_listas)
        except Exception as e:
            st.warning("No hay datos")
    else:
        st.warning("Repositorio no disponible")

    st.divider()
    st.caption(f"**Versión:** 2.0.0")
    st.caption(f"**Base de datos:** SQLite")
    st.caption(f"**Último acceso:** {datetime.now().strftime('%H:%M:%S')}")


# =========================================================
# PANEL DE CONTROL
# =========================================================
if menu == "📊 Panel de control":
    st.title("📊 Panel de Control FernetOS")

    # Métricas principales en tarjetas
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        with st.container(border=True):
            activas = len(repo.listar(estado="en_maceracion")) if repo else 0
            st.metric("Tinturas en Maceración", activas, delta=None)

    with col2:
        with st.container(border=True):
            listas = len(repo.listar(estado="lista")) if repo else 0
            st.metric("Tinturas Listas", listas, delta=None)

    with col3:
        with st.container(border=True):
            st.metric("Ensayos Activos", 3, delta=None)  # TODO: Implementar

    with col4:
        with st.container(border=True):
            st.metric("Mezclas históricas", 12, delta=None)  # TODO: Implementar

    st.divider()

    # Gráfico de actividad
    st.subheader("📈 Actividad Reciente")

    # Datos de ejemplo - reemplazar con datos reales
    fechas = pd.date_range(
        start=datetime.now() - timedelta(days=14), end=datetime.now(), freq="D"
    )
    df_actividad = pd.DataFrame(
        {
            "fecha": fechas,
            "catas": np.random.randint(0, 5, len(fechas)),
            "nuevas_tinturas": np.random.randint(0, 2, len(fechas)),
        }
    )

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(
        go.Bar(
            x=df_actividad["fecha"],
            y=df_actividad["nuevas_tinturas"],
            name="Nuevas Tinturas",
            marker_color="#1f77b4",
        ),
        secondary_y=False,
    )

    fig.add_trace(
        go.Scatter(
            x=df_actividad["fecha"],
            y=df_actividad["catas"],
            name="Catas Registradas",
            line=dict(color="#ff7f0e", width=3),
            mode="lines+markers",
        ),
        secondary_y=True,
    )

    fig.update_layout(
        height=400, title_text="Actividad Últimos 14 Días", hovermode="x unified"
    )

    fig.update_xaxes(title_text="Fecha")
    fig.update_yaxes(title_text="Nuevas Tinturas", secondary_y=False)
    fig.update_yaxes(title_text="Catas Registradas", secondary_y=True)

    st.plotly_chart(fig, use_container_width=True)


# =========================================================
# MÓDULO DE TINTURAS
# =========================================================
elif menu == "🧪 Tinturas":
    st.title("🧪 Gestión de Tinturas")

    if not repo:
        st.error("Error: Repositorio no disponible")
        st.stop()

    tab1, tab2, tab3 = st.tabs(["📋 Listado", "➕ Nueva Tintura", "📊 Estadísticas"])

    # TAB 1: LISTADO
    with tab1:
        st.subheader("Tinturas Registradas")

        # Filtros
        from core.tintura_models import Producto, grupos_disponibles_para

        col0, col1, col2, col3 = st.columns(4)
        with col0:
            filtro_producto = st.selectbox(
                "Producto", ["Todos"] + [p.value for p in Producto], key="listado_producto"
            )
        with col1:
            filtro_estado = st.selectbox(
                "Estado",
                ["Todos", "en_maceracion", "en_estabilizacion", "lista", "agotada"],
            )
        with col2:
            # Sin key= a propósito: al cambiar filtro_producto, Streamlit
            # detecta que options cambió y regenera el widget con el valor
            # por defecto ("Todos") en vez de arrastrar una selección que ya
            # no es válida para el nuevo producto.
            filtro_grupo = st.selectbox(
                "Grupo", ["Todos"] + grupos_disponibles_para(filtro_producto)
            )
        with col3:
            busqueda = st.text_input("🔍 Buscar", placeholder="Nombre o ID")

        # Obtener tinturas
        filtro_producto_valor = None if filtro_producto == "Todos" else filtro_producto
        if filtro_estado == "Todos":
            tinturas = repo.listar(producto=filtro_producto_valor)
        else:
            tinturas = repo.listar(estado=filtro_estado, producto=filtro_producto_valor)

        if filtro_grupo != "Todos":
            tinturas = [
                t
                for t in tinturas
                if t.grupo_funcional and t.grupo_funcional.value == filtro_grupo
            ]

        if busqueda:
            tinturas = [
                t
                for t in tinturas
                if busqueda.lower() in (t.nombre or "").lower()
                or busqueda in (t.id or "")
            ]

        # Mostrar tabla
        if tinturas:
            data = []
            for t in tinturas:
                data.append(
                    {
                        "ID": t.id,
                        "Nombre": t.nombre,
                        "Producto": t.producto.value if t.producto else "N/A",
                        "Grupo": (
                            t.grupo_funcional.value if t.grupo_funcional else "N/A"
                        ),
                        "Estado": t.estado.value if t.estado else "N/A",
                        "Días": max(0, t.dias_transcurridos),
                        "Volumen (ml)": t.volumen_disponible_ml,
                        "Fecha Inicio": (
                            t.fecha_inicio.strftime("%d/%m/%Y")
                            if t.fecha_inicio
                            else ""
                        ),
                    }
                )

            df = pd.DataFrame(data)
            st.dataframe(df, use_container_width=True, hide_index=True)

            # Detalle de tintura seleccionada
            st.divider()
            st.subheader("🔍 Detalle de Tintura")

            if data:
                selected_id = st.selectbox(
                    "Seleccionar tintura para ver detalle",
                    options=[t.id for t in tinturas if t.id],
                    format_func=lambda x: (
                        next((t.nombre for t in tinturas if t.id == x), x)
                        if x
                        else "Ninguna"
                    ),
                )

                if selected_id:
                    t = repo.get_by_id(selected_id)
                    if t:
                        col1, col2 = st.columns(2)

                        with col1:
                            with st.container(border=True):
                                st.write(f"**ID:** {t.id}")
                                st.write(f"**Nombre:** {t.nombre}")
                                st.write(
                                    f"**Grupo:** {t.grupo_funcional.value if t.grupo_funcional else 'N/A'}"
                                )
                                st.write(
                                    f"**Estado:** {t.estado.value if t.estado else 'N/A'}"
                                )
                                st.write(f"**Versión:** {t.version}")

                        with col2:
                            with st.container(border=True):
                                st.write(
                                    f"**Fecha inicio:** {formato_fecha(t.fecha_inicio)}"
                                )
                                st.write(
                                    f"**Corte estimado:** {formato_fecha(t.fecha_corte_estimada)}"
                                )
                                st.write(
                                    f"**Volumen inicial:** {t.volumen_alcohol_ml} ml"
                                )
                                st.write(
                                    f"**Volumen disponible:** {t.volumen_disponible_ml} ml"
                                )

                        # Composición
                        if t.composicion:
                            st.write("**Composición:**")
                            for c in t.composicion:
                                st.write(
                                    f"- {c.especie}: {c.porcentaje}% ({c.parte_utilizada})"
                                )
        else:
            st.info("No hay tinturas que coincidan con los filtros")

    # TAB 2: NUEVA TINTURA
    with tab2:
        st.subheader("Crear Nueva Tintura")

        from core.tintura_models import (
            Tintura,
            GrupoFuncional,
            ComposicionBotanica,
            ParametrosExtraccion,
            GRUPOS_POR_PRODUCTO,
            Producto,
        )

        # Fuera del form: un st.form no re-renderiza sus propios widgets al
        # cambiar uno de ellos, así que el selector de Producto (que decide
        # qué grupos funcionales mostrar) tiene que vivir afuera.
        producto_nueva_tintura = st.selectbox(
            "Producto*",
            options=[p.value for p in Producto],
            key="nueva_tintura_producto",
        )
        grupos_para_producto = GRUPOS_POR_PRODUCTO[Producto(producto_nueva_tintura)]

        with st.form("form_nueva_tintura", border=True):
            col1, col2 = st.columns(2)

            with col1:
                nombre = st.text_input(
                    "Nombre de la tintura*",
                    placeholder="Ej: Amargos Estructurales Mar24",
                )
                grupo = st.selectbox(
                    "Grupo funcional*",
                    options=[g.value for g in grupos_para_producto],
                    index=0,
                )
                abv = st.number_input(
                    "ABV objetivo (%)*",
                    min_value=40.0,
                    max_value=95.0,
                    value=70.0,
                    step=0.5,
                )

            with col2:
                peso = st.number_input(
                    "Peso materia seca (g)*", min_value=10.0, value=200.0, step=10.0
                )
                volumen = st.number_input(
                    "Volumen alcohol (ml)*", min_value=100.0, value=1000.0, step=50.0
                )
                tiempo = st.number_input(
                    "Tiempo estimado (días)*", min_value=1, value=21, step=1
                )

            st.divider()
            st.write("**Composición botánica**")

            # Composición dinámica
            num_especies = st.number_input(
                "Número de especies", min_value=1, max_value=10, value=1, step=1
            )

            composicion = []
            total_pct = 0
            especies_validas = True

            for i in range(int(num_especies)):
                cols = st.columns([3, 1, 2])
                with cols[0]:
                    especie = st.text_input(f"Especie {i+1}", key=f"esp_{i}")
                with cols[1]:
                    pct = st.number_input(
                        f"%",
                        min_value=0.0,
                        max_value=100.0,
                        value=0.0,
                        key=f"pct_{i}",
                        step=5.0,
                    )
                with cols[2]:
                    parte = st.selectbox(
                        f"Parte",
                        ["raiz", "corteza", "hoja", "flor", "semilla", "cascara"],
                        key=f"parte_{i}",
                    )

                if especie and pct > 0:
                    composicion.append(
                        {"especie": especie, "porcentaje": pct, "parte": parte}
                    )
                    total_pct += pct
                elif especie:
                    especies_validas = False

            if total_pct > 0 and total_pct != 100:
                st.warning(
                    f"⚠️ Los porcentajes suman {total_pct}%. Debe sumar exactamente 100%"
                )

            st.divider()
            observaciones = st.text_area(
                "Observaciones iniciales",
                placeholder="Notas sobre lote, procedencia, etc.",
            )

            submitted = st.form_submit_button(
                "✅ Crear Tintura", use_container_width=True
            )

            if submitted:
                if not nombre:
                    st.error("El nombre es obligatorio")
                elif not especies_validas:
                    st.error("Completa los nombres de las especies")
                elif total_pct != 100:
                    st.error(f"La composición debe sumar 100% (actual: {total_pct}%)")
                else:
                    # Crear objetos
                    comps = []
                    for c in composicion:
                        comps.append(
                            ComposicionBotanica(
                                especie=c["especie"],
                                porcentaje=c["porcentaje"],
                                parte_utilizada=c["parte"],
                            )
                        )

                    params = ParametrosExtraccion(
                        abv_objetivo=abv,
                        ratio_planta_alcohol=peso / volumen,
                        tiempo_estimado_dias=tiempo,
                    )

                    # Mapear grupo
                    grupo_map = {g.value: g for g in GrupoFuncional}

                    tintura = Tintura(
                        nombre=nombre,
                        producto=Producto(producto_nueva_tintura),
                        grupo_funcional=grupo_map[grupo],
                        composicion=comps,
                        peso_total_materia_seca_g=peso,
                        volumen_alcohol_ml=volumen,
                        parametros=params,
                        observaciones_iniciales=observaciones,
                    )

                    try:
                        repo.guardar(tintura)
                        st.success(f"✅ Tintura creada con ID: {tintura.id}")
                        st.balloons()
                        time.sleep(2)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error guardando tintura: {e}")

    # TAB 3: ESTADÍSTICAS
    with tab3:
        st.subheader("📊 Estadísticas de Tinturas")

        tinturas_totales = repo.listar()

        if tinturas_totales:
            # Distribución por grupo
            grupos = {}
            for t in tinturas_totales:
                if t.grupo_funcional:
                    grupo = t.grupo_funcional.value
                    grupos[grupo] = grupos.get(grupo, 0) + 1

            if grupos:
                df_grupos = pd.DataFrame(
                    {"Grupo": list(grupos.keys()), "Cantidad": list(grupos.values())}
                )

                col1, col2 = st.columns(2)

                with col1:
                    fig = px.pie(
                        df_grupos,
                        values="Cantidad",
                        names="Grupo",
                        title="Distribución por Grupo Funcional",
                        color_discrete_sequence=px.colors.qualitative.Set2,
                    )
                    st.plotly_chart(fig, use_container_width=True)

                with col2:
                    # Distribución por estado
                    estados = {}
                    for t in tinturas_totales:
                        if t.estado:
                            estado = t.estado.value
                            estados[estado] = estados.get(estado, 0) + 1

                    if estados:
                        df_estados = pd.DataFrame(
                            {
                                "Estado": list(estados.keys()),
                                "Cantidad": list(estados.values()),
                            }
                        )

                        fig = px.bar(
                            df_estados,
                            x="Estado",
                            y="Cantidad",
                            title="Tinturas por Estado",
                            color="Estado",
                            color_discrete_sequence=px.colors.qualitative.Set2,
                        )
                        st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No hay tinturas registradas")


# =========================================================
# MÓDULO DE CURVAS DE EXTRACCIÓN
# =========================================================
elif menu == "📈 Curvas de Extracción":
    st.title("📈 Curvas de Extracción")

    if not repo:
        st.error("Error: Repositorio no disponible")
        st.stop()

    # Obtener todas las tinturas
    todas_tinturas = repo.listar()

    if not todas_tinturas:
        st.warning("No hay tinturas registradas. Crea una tintura primero.")
        st.stop()

    # Crear opciones para el selector
    opciones_tinturas = {
        t.id: f"{t.nombre} ({t.grupo_funcional.value if t.grupo_funcional else 'Sin grupo'}) - Días: {max(0, t.dias_transcurridos)}"
        for t in todas_tinturas
    }

    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("Seleccionar Tintura")

        selected_id = st.selectbox(
            "Tintura",
            options=list(opciones_tinturas.keys()),
            format_func=lambda x: opciones_tinturas[x],
            key="selector_tintura",
        )

        if selected_id:
            t = repo.get_by_id(selected_id)

            if t:
                with st.container(border=True):
                    st.write(f"**Nombre:** {t.nombre}")
                    st.write(
                        f"**Grupo:** {t.grupo_funcional.value if t.grupo_funcional else 'N/A'}"
                    )
                    st.write(f"**Estado:** {t.estado.value if t.estado else 'N/A'}")
                    st.write(f"**Días transcurridos:** {max(0, t.dias_transcurridos)}")
                    if t.fecha_corte_estimada:
                        st.write(
                            f"**Corte estimado:** {t.fecha_corte_estimada.strftime('%d/%m/%Y')}"
                        )

                st.divider()
                st.subheader("Registrar Nueva Cata")

                with st.form("form_cata", border=True):
                    # Asegurar que el valor inicial sea >= min_value
                    dia_inicial = max(1, t.dias_transcurridos + 1)

                    dia = st.number_input("Día", min_value=1, value=dia_inicial, step=1)

                    intensidad = st.slider(
                        "Intensidad estimada (0-100)",
                        0,
                        100,
                        50,
                        help="Percepción global de la extracción",
                    )

                    notas = st.text_area(
                        "Notas sensoriales",
                        placeholder="Describe aroma, sabor, color, etc.",
                        height=100,
                    )

                    compuestos = st.multiselect(
                        "Compuestos detectados",
                        [
                            "glucosidos",
                            "taninos",
                            "taninos_astringentes",
                            "terpenos",
                            "terpenos_volatiles",
                            "eugenol",
                            "eugenol_ligero",
                            "clorofila",
                            "aceites_esenciales",
                            "resinas",
                            "leñoso",
                            "terroso",
                            "citrico",
                            "limoneno",
                            "mentol",
                            "saponinas",
                            "glucosidos_dulces",
                        ],
                        default=[],
                    )

                    col_a, col_b, col_c = st.columns(3)
                    with col_a:
                        color = st.text_input("Color", value="ambar")
                    with col_b:
                        turbidez = st.selectbox(
                            "Turbidez", ["claro", "ligera", "media", "alta", "muy alta"]
                        )
                    with col_c:
                        aroma = st.text_input("Aroma", value="")

                    submitted = st.form_submit_button(
                        "💾 Registrar Cata", use_container_width=True
                    )

                    if submitted:
                        from datetime import datetime
                        from core.tintura_models import RegistroExtraccion

                        registro = RegistroExtraccion(
                            dia=dia,
                            fecha=datetime.now(),
                            intensidad_estimada=intensidad,
                            notas_sensoriales=notas,
                            compuestos_detectados=compuestos,
                            color=color,
                            turbidez=turbidez,
                            aroma_descripcion=aroma,
                        )
                        t.agregar_registro_extraccion(registro)
                        repo.guardar(t)
                        st.success(f"✅ Registro día {dia} guardado")
                        st.balloons()
                        time.sleep(1)
                        st.rerun()

    with col2:
        if selected_id:
            t = repo.get_by_id(selected_id)

            if t and t.registros_extraccion:
                from core.curve_analysis import CurveAnalyzer

                analyzer = CurveAnalyzer(t)
                analisis = analyzer.analizar_completo()

                # Preparar datos para gráfico
                dias = [r.dia for r in t.registros_extraccion]
                intensidades = [r.intensidad_estimada for r in t.registros_extraccion]

                # Gráfico con Plotly
                fig = make_subplots(
                    rows=2,
                    cols=1,
                    subplot_titles=("Curva de Extracción", "Velocidad de Extracción"),
                    vertical_spacing=0.15,
                    row_heights=[0.7, 0.3],
                )

                # Curva principal
                fig.add_trace(
                    go.Scatter(
                        x=dias,
                        y=intensidades,
                        mode="markers+lines",
                        name="Intensidad",
                        marker=dict(size=10, color="blue", symbol="circle"),
                        line=dict(color="blue", width=2, dash="dot"),
                        hovertemplate="Día: %{x}<br>Intensidad: %{y}<extra></extra>",
                    ),
                    row=1,
                    col=1,
                )

                # Punto óptimo
                if analisis.dia_optimo_sugerido:
                    fig.add_vline(
                        x=analisis.dia_optimo_sugerido,
                        line_dash="dash",
                        line_color="green",
                        line_width=2,
                        opacity=0.7,
                        row=1,
                        col=1,
                    )

                    # Anotación
                    fig.add_annotation(
                        x=analisis.dia_optimo_sugerido,
                        y=max(intensidades) * 0.9 if intensidades else 90,
                        text=f"Óptimo: día {analisis.dia_optimo_sugerido}",
                        showarrow=True,
                        arrowhead=1,
                        row=1,
                        col=1,
                    )

                # Línea de tendencia suavizada
                if len(dias) >= 3:
                    try:
                        from scipy.interpolate import make_interp_spline

                        dias_suave = np.linspace(min(dias), max(dias), 100)
                        spline = make_interp_spline(
                            dias, intensidades, k=min(3, len(dias) - 1)
                        )
                        int_suave = spline(dias_suave)

                        fig.add_trace(
                            go.Scatter(
                                x=dias_suave,
                                y=int_suave,
                                mode="lines",
                                name="Tendencia",
                                line=dict(color="lightblue", width=2),
                                opacity=0.5,
                                hovertemplate="Día: %{x:.1f}<br>Tendencia: %{y:.1f}<extra></extra>",
                            ),
                            row=1,
                            col=1,
                        )
                    except Exception as e:
                        pass  # Si falla la interpolación, continuar sin ella

                # Pendientes
                dias_medios, pendientes = analyzer.calcular_pendientes()
                if len(pendientes) > 0:
                    colors = ["red" if p < 0 else "orange" for p in pendientes]
                    fig.add_trace(
                        go.Bar(
                            x=dias_medios,
                            y=pendientes,
                            name="Pendiente",
                            marker_color=colors,
                            opacity=0.7,
                            hovertemplate="Día: %{x:.1f}<br>Pendiente: %{y:.2f}<extra></extra>",
                        ),
                        row=2,
                        col=1,
                    )

                fig.update_layout(height=600, showlegend=False, hovermode="x unified")

                fig.update_xaxes(title_text="Días", row=2, col=1)
                fig.update_yaxes(
                    title_text="Intensidad (0-100)", row=1, col=1, range=[0, 105]
                )
                fig.update_yaxes(title_text="Pendiente", row=2, col=1)

                st.plotly_chart(fig, use_container_width=True)

                # Métricas
                st.subheader("📊 Análisis de la Curva")
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric(
                        "Día óptimo sugerido", analisis.dia_optimo_sugerido or "N/A"
                    )
                with col2:
                    st.metric("Área bajo curva", f"{analisis.area_bajo_curva:.0f}")
                with col3:
                    st.metric("Registros", len(t.registros_extraccion))
                with col4:
                    st.metric(
                        "Pendiente promedio",
                        (
                            f"{analisis.pendiente_promedio:.2f}"
                            if analisis.pendiente_promedio
                            else "N/A"
                        ),
                    )

                # Alertas
                if analisis.alertas:
                    with st.expander("⚠️ Alertas detectadas", expanded=True):
                        for alerta in analisis.alertas:
                            st.warning(alerta)

                # Tabla de registros
                with st.expander("📋 Ver todos los registros de cata"):
                    data_registros = []
                    for r in t.registros_extraccion:
                        data_registros.append(
                            {
                                "Día": r.dia,
                                "Intensidad": r.intensidad_estimada,
                                "Compuestos": (
                                    ", ".join(r.compuestos_detectados)
                                    if r.compuestos_detectados
                                    else "-"
                                ),
                                "Color": r.color,
                                "Turbidez": r.turbidez,
                                "Notas": (
                                    r.notas_sensoriales[:50] + "..."
                                    if len(r.notas_sensoriales) > 50
                                    else r.notas_sensoriales
                                ),
                            }
                        )

                    df_registros = pd.DataFrame(data_registros)
                    st.dataframe(
                        df_registros, use_container_width=True, hide_index=True
                    )

                # Botón para generar gráfico
                if st.button("📥 Descargar gráfico", use_container_width=True):
                    try:
                        from core.curve_visualizer import CurveVisualizer

                        visualizer = CurveVisualizer()
                        filepath = visualizer.generar_grafico(
                            analyzer, guardar=True, mostrar=False
                        )
                        st.success(f"✅ Gráfico guardado en: {filepath}")

                        # Ofrecer descarga
                        with open(filepath, "rb") as f:
                            st.download_button(
                                "📥 Descargar PNG",
                                f,
                                file_name=os.path.basename(filepath),
                                mime="image/png",
                            )
                    except Exception as e:
                        st.error(f"Error generando gráfico: {e}")

            elif t and not t.registros_extraccion:
                st.info(
                    "ℹ️ Esta tintura no tiene registros de curva. Usa el formulario para registrar tu primera cata."
                )

                # Mostrar parámetros de la tintura
                with st.container(border=True):
                    st.write("**Parámetros de la tintura:**")
                    st.write(
                        f"- ABV objetivo: {t.parametros.abv_objetivo if t.parametros else 'N/A'}%"
                    )
                    if t.parametros and t.parametros.ratio_planta_alcohol:
                        st.write(
                            f"- Ratio planta/alcohol: 1:{int(1/t.parametros.ratio_planta_alcohol)}"
                        )
                    st.write(
                        f"- Tiempo estimado: {t.parametros.tiempo_estimado_dias if t.parametros else 'N/A'} días"
                    )
                    if t.composicion:
                        st.write("**Composición:**")
                        for c in t.composicion:
                            st.write(f"  • {c.especie}: {c.porcentaje}%")
        else:
            st.info("👈 Selecciona una tintura para ver su curva de extracción")

# =========================================================
# MÓDULO DE ENSAMBLAJE
# =========================================================
elif menu == "🧮 Ensamblaje":
    st.title("🧮 Ensamblaje y Blending")

    if not repo or not calculator:
        st.error("Error: Componentes no disponibles")
        st.stop()

    from families.fernet.calculator import BlendParams
    from core.receta_reportes import generar_ficha_tecnica_blend_fernet

    tabs = st.tabs(["🧪 Nuevo Blend", "📋 Historial", "📊 Análisis"])

    with tabs[0]:
        st.subheader("Crear Nuevo Blend")

        # Parámetros del blend en la parte superior
        col_params1, col_params2, col_params3 = st.columns(3)

        with col_params1:
            volumen = st.number_input(
                "📊 Volumen objetivo (L)",
                min_value=0.5,
                max_value=100.0,
                value=10.0,
                step=0.5,
                help="Volumen total del blend en litros",
            )

        with col_params2:
            abv = st.number_input(
                "🥃 ABV objetivo (%)",
                min_value=30.0,
                max_value=50.0,
                value=40.0,
                step=0.5,
                help="Graduación alcohólica objetivo",
            )

        with col_params3:
            azucar = st.number_input(
                "🍬 Azúcar (g/L)",
                min_value=140,
                max_value=240,
                value=195,
                step=5,
                help="Gramos de azúcar por litro",
            )

        st.divider()

        # Tinturas disponibles
        st.subheader("🧪 Tinturas Disponibles en Stock")

        tinturas_stock = repo.listar(estado="lista")

        if not tinturas_stock:
            st.warning(
                "⚠️ No hay tinturas disponibles en stock. Crea y finaliza tinturas primero."
            )
        else:
            # Crear columnas para las tinturas (2 por fila)
            num_tinturas = len(tinturas_stock)
            filas = (num_tinturas + 1) // 2

            tinturas_seleccionadas = {}

            for i in range(0, num_tinturas, 2):
                cols = st.columns(2)

                # Primera tintura de la fila
                with cols[0]:
                    t = tinturas_stock[i]
                    with st.container(border=True):
                        st.write(f"**{t.nombre}**")
                        st.caption(
                            f"📦 Stock: {t.volumen_disponible_ml:.0f} ml | 🏷️ {t.grupo_funcional.value if t.grupo_funcional else 'N/A'}"
                        )

                        ml = st.number_input(
                            f"ml para {t.nombre[:15]}...",
                            min_value=0.0,
                            max_value=float(t.volumen_disponible_ml),
                            value=0.0,
                            step=5.0,
                            key=f"t_{t.id}",
                            format="%.0f",
                        )

                        if ml > 0:
                            tinturas_seleccionadas[t.id] = ml
                            st.caption(f"✅ Usando {ml:.0f} ml")

                # Segunda tintura de la fila (si existe)
                if i + 1 < num_tinturas:
                    with cols[1]:
                        t = tinturas_stock[i + 1]
                        with st.container(border=True):
                            st.write(f"**{t.nombre}**")
                            st.caption(
                                f"📦 Stock: {t.volumen_disponible_ml:.0f} ml | 🏷️ {t.grupo_funcional.value if t.grupo_funcional else 'N/A'}"
                            )

                            ml = st.number_input(
                                f"ml para {t.nombre[:15]}...",
                                min_value=0.0,
                                max_value=float(t.volumen_disponible_ml),
                                value=0.0,
                                step=5.0,
                                key=f"t_{t.id}",
                                format="%.0f",
                            )

                            if ml > 0:
                                tinturas_seleccionadas[t.id] = ml
                                st.caption(f"✅ Usando {ml:.0f} ml")

            st.divider()

            # Mostrar resumen de selección
            if tinturas_seleccionadas:
                st.subheader("📋 Resumen de Selección")

                # Crear DataFrame con las tinturas seleccionadas
                data_resumen = []
                total_ml_tinturas = 0

                for tid, ml in tinturas_seleccionadas.items():
                    t = next((t for t in tinturas_stock if t.id == tid), None)
                    if t:
                        data_resumen.append(
                            {
                                "Tintura": t.nombre,
                                "Grupo": (
                                    t.grupo_funcional.value
                                    if t.grupo_funcional
                                    else "N/A"
                                ),
                                "Volumen (ml)": ml,
                            }
                        )
                        total_ml_tinturas += ml

                df_resumen = pd.DataFrame(data_resumen)
                st.dataframe(df_resumen, use_container_width=True, hide_index=True)

                st.info(f"📊 Total tinturas: {total_ml_tinturas:.0f} ml")

                # Botón para calcular
                if st.button(
                    "🧪 Calcular Blend", type="primary", use_container_width=True
                ):
                    with st.spinner("Calculando blend..."):
                        try:
                            params = BlendParams(
                                volumen_objetivo_litros=volumen,
                                abv_objetivo=abv,
                                azucar_objetivo_gpl=azucar,
                            )

                            # Obtener datos completos de tinturas seleccionadas
                            tinturas_data = {}
                            for tid in tinturas_seleccionadas.keys():
                                t = repo.get_by_id(tid)
                                if t:
                                    tinturas_data[tid] = t

                            resultado = calculator.calcular_blend_completo(
                                params, tinturas_seleccionadas, tinturas_data
                            )

                            st.success("✅ Blend calculado exitosamente!")

                            # Mostrar resultados en columnas
                            col_r1, col_r2, col_r3, col_r4 = st.columns(4)

                            with col_r1:
                                with st.container(border=True):
                                    st.metric(
                                        "ABV Calculado",
                                        f"{resultado.abv_calculado:.2f}%",
                                    )

                            with col_r2:
                                with st.container(border=True):
                                    st.metric(
                                        "Volumen total",
                                        f"{resultado.volumen_real_ml/1000:.2f}L",
                                    )

                            with col_r3:
                                with st.container(border=True):
                                    st.metric(
                                        "Alcohol base",
                                        f"{resultado.composicion.alcohol_base_ml:.0f}ml",
                                    )

                            with col_r4:
                                with st.container(border=True):
                                    st.metric(
                                        "Agua base",
                                        f"{resultado.composicion.agua_base_ml:.0f}ml",
                                    )

                            st.divider()

                            # Mostrar composición completa
                            st.subheader("📝 Receta Completa")

                            col_receta1, col_receta2 = st.columns(2)

                            with col_receta1:
                                with st.container(border=True):
                                    st.write("**Base alcohólica:**")
                                    st.write(
                                        f"- Alcohol 96%: {resultado.composicion.alcohol_base_ml:.0f} ml"
                                    )
                                    st.write(
                                        f"- Agua: {resultado.composicion.agua_base_ml:.0f} ml"
                                    )
                                    st.write(
                                        f"- Azúcar: {resultado.composicion.azucar_g:.0f} g"
                                    )

                            with col_receta2:
                                with st.container(border=True):
                                    st.write("**Tinturas:**")
                                    for (
                                        tid,
                                        ml,
                                    ) in resultado.composicion.tinturas.items():
                                        t = tinturas_data.get(tid)
                                        if t:
                                            st.write(f"- {t.nombre}: {ml:.0f} ml")

                            # Tabla de porcentajes
                            st.subheader("📊 Distribución Porcentual")

                            data_porcentajes = []
                            for tid, ml in resultado.composicion.tinturas.items():
                                t = tinturas_data.get(tid)
                                if t:
                                    porcentaje = (
                                        ml / resultado.composicion.volumen_total_ml
                                    ) * 100
                                    data_porcentajes.append(
                                        {
                                            "Tintura": t.nombre,
                                            "Volumen (ml)": ml,
                                            "% del blend": f"{porcentaje:.1f}%",
                                        }
                                    )

                            # Añadir alcohol y agua
                            porcentaje_alcohol = (
                                resultado.composicion.alcohol_base_ml
                                / resultado.composicion.volumen_total_ml
                            ) * 100
                            porcentaje_agua = (
                                resultado.composicion.agua_base_ml
                                / resultado.composicion.volumen_total_ml
                            ) * 100

                            data_porcentajes.append(
                                {
                                    "Tintura": "Alcohol 96%",
                                    "Volumen (ml)": resultado.composicion.alcohol_base_ml,
                                    "% del blend": f"{porcentaje_alcohol:.1f}%",
                                }
                            )

                            data_porcentajes.append(
                                {
                                    "Tintura": "Agua",
                                    "Volumen (ml)": resultado.composicion.agua_base_ml,
                                    "% del blend": f"{porcentaje_agua:.1f}%",
                                }
                            )

                            df_porcentajes = pd.DataFrame(data_porcentajes)
                            st.dataframe(
                                df_porcentajes,
                                use_container_width=True,
                                hide_index=True,
                            )

                            # El blend no se persiste todavia (ver docs/specs/
                            # 2026-09-08-fase3-ficha-tecnica-blend.md), asi que
                            # la ficha tecnica se genera al vuelo a partir del
                            # calculo actual en vez de un blend guardado.
                            pdf_ficha_tecnica = generar_ficha_tecnica_blend_fernet(
                                resultado, tinturas_data
                            )
                            st.download_button(
                                "📄 Descargar ficha técnica (PDF)",
                                data=pdf_ficha_tecnica,
                                file_name=f"ficha_tecnica_{resultado.id}.pdf",
                                mime="application/pdf",
                                use_container_width=True,
                            )

                        except Exception as e:
                            st.error(f"Error calculando blend: {e}")
                            import traceback

                            st.error(traceback.format_exc())
            else:
                st.info("👆 Selecciona al menos una tintura para crear un blend")

    with tabs[1]:
        st.subheader("Historial de Blends")
        st.info("📋 Historial de blends guardados - Próximamente")

        # Placeholder para historial
        data_historial = pd.DataFrame(
            {
                "Fecha": ["21/02/2026", "20/02/2026", "19/02/2026"],
                "Blend ID": ["B-001", "B-002", "B-003"],
                "Volumen (L)": [10, 5, 20],
                "ABV": [40.2, 39.8, 41.0],
                "Tinturas": [4, 3, 5],
            }
        )

        st.dataframe(data_historial, use_container_width=True, hide_index=True)

    with tabs[2]:
        st.subheader("Análisis de Blends")
        st.info("📊 Análisis estadístico de blends - Próximamente")

        # Placeholder para análisis
        col_a1, col_a2 = st.columns(2)

        with col_a1:
            fig = go.Figure(
                data=[
                    go.Bar(
                        name="ABV",
                        x=["Blend 1", "Blend 2", "Blend 3"],
                        y=[40.2, 39.8, 41.0],
                    )
                ]
            )
            fig.update_layout(title="Comparativa de ABV", height=300)
            st.plotly_chart(fig, use_container_width=True)

        with col_a2:
            fig = go.Figure(
                data=[
                    go.Bar(
                        name="Tinturas",
                        x=["Blend 1", "Blend 2", "Blend 3"],
                        y=[4, 3, 5],
                    )
                ]
            )
            fig.update_layout(title="Número de Tinturas por Blend", height=300)
            st.plotly_chart(fig, use_container_width=True)

# =========================================================
# MÓDULO DE ENSAMBLAJE GANCIA - BASE VÍNICA
# =========================================================
elif menu == "🍷 Ensamblaje Gancia":
    st.title("🍷 Ensamblaje de Gancia")
    st.caption("Base vínica fortificada - motor de cálculo independiente del de Fernet")

    if not repo:
        st.error("Error: Repositorio no disponible")
        st.stop()

    from families.gancia.gancia_calculator import (
        ComposicionBlendGancia,
        GanciaBlendParams,
        GanciaCalculator,
    )
    from core.tintura_models import Producto

    gancia_calculator = GanciaCalculator()

    st.subheader("Crear Nuevo Blend de Gancia")

    col_p1, col_p2, col_p3 = st.columns(3)

    with col_p1:
        volumen_gancia = st.number_input(
            "📊 Volumen objetivo (L)",
            min_value=0.5,
            max_value=100.0,
            value=10.0,
            step=0.5,
            key="gancia_volumen",
        )
        abv_gancia = st.number_input(
            "🥃 ABV objetivo (%)",
            min_value=15.0,
            max_value=18.0,
            value=17.0,
            step=0.5,
            key="gancia_abv",
        )

    with col_p2:
        vino_pct_gancia = st.slider(
            "🍷 % Vino sobre el volumen",
            min_value=75.0,
            max_value=80.0,
            value=78.0,
            step=0.5,
            key="gancia_vino_pct",
        )
        vino_abv_gancia = st.number_input(
            "Grado del vino base (%)",
            min_value=8.0,
            max_value=15.0,
            value=12.0,
            step=0.5,
            key="gancia_vino_abv",
        )
        alcohol_fortificacion_abv_gancia = st.number_input(
            "Grado del alcohol de fortificación (%)",
            min_value=90.0,
            max_value=96.5,
            value=96.0,
            step=0.5,
            key="gancia_fortificacion_abv",
        )

    with col_p3:
        azucar_pct_gancia = st.slider(
            "🍬 Azúcar (% p/v)",
            min_value=8.0,
            max_value=12.0,
            value=10.0,
            step=0.5,
            key="gancia_azucar_pct",
            help="Gramos de azúcar seca por 100ml",
        )
        acido_citrico_gancia = st.number_input(
            "🍋 Ácido cítrico (g/L)",
            min_value=0.0,
            max_value=5.0,
            value=0.0,
            step=0.1,
            key="gancia_acido_citrico",
        )
        caramelo_gancia = st.number_input(
            "🎨 Caramelo E150 (ml)",
            min_value=0.0,
            max_value=50.0,
            value=0.0,
            step=1.0,
            key="gancia_caramelo",
        )

    st.divider()

    st.subheader("🧪 Tinturas de Gancia Disponibles en Stock")

    tinturas_gancia_stock = repo.listar(estado="lista", producto=Producto.GANCIA.value)

    tinturas_seleccionadas_gancia = {}

    if not tinturas_gancia_stock:
        st.warning(
            "⚠️ No hay tinturas de Gancia disponibles en stock. Creá y finalizá "
            "tinturas de producto Gancia en la sección 🧪 Tinturas."
        )
    else:
        num_tinturas_g = len(tinturas_gancia_stock)

        for i in range(0, num_tinturas_g, 2):
            cols = st.columns(2)
            for offset, col in enumerate(cols):
                idx = i + offset
                if idx >= num_tinturas_g:
                    continue
                t = tinturas_gancia_stock[idx]
                with col:
                    with st.container(border=True):
                        st.write(f"**{t.nombre}**")
                        st.caption(
                            f"📦 Stock: {t.volumen_disponible_ml:.0f} ml | 🏷️ {t.grupo_funcional.value if t.grupo_funcional else 'N/A'}"
                        )
                        ml = st.number_input(
                            f"ml para {t.nombre[:15]}...",
                            min_value=0.0,
                            max_value=float(t.volumen_disponible_ml),
                            value=0.0,
                            step=5.0,
                            key=f"gancia_t_{t.id}",
                            format="%.0f",
                        )
                        if ml > 0:
                            tinturas_seleccionadas_gancia[t.id] = ml
                            st.caption(f"✅ Usando {ml:.0f} ml")

    st.divider()

    if st.button("🍷 Calcular Blend de Gancia", type="primary", use_container_width=True):
        with st.spinner("Calculando blend..."):
            try:
                params_gancia = GanciaBlendParams(
                    volumen_objetivo_litros=volumen_gancia,
                    abv_objetivo=abv_gancia,
                    vino_pct=vino_pct_gancia / 100,
                    vino_abv=vino_abv_gancia,
                    alcohol_fortificacion_abv=alcohol_fortificacion_abv_gancia,
                    azucar_pct_wv=azucar_pct_gancia,
                    acido_citrico_g_l=acido_citrico_gancia,
                    caramelo_ml=caramelo_gancia,
                )

                tinturas_ml_total = sum(tinturas_seleccionadas_gancia.values())
                vino_ml, alcohol_fortificacion_ml, agua_ml = (
                    gancia_calculator.calcular_base_vino_alcohol(
                        params_gancia, tinturas_ml_total
                    )
                )

                tinturas_data_gancia = {}
                for tid in tinturas_seleccionadas_gancia.keys():
                    t = repo.get_by_id(tid)
                    if t:
                        tinturas_data_gancia[tid] = t

                azucar_g = GanciaCalculator.calcular_azucar(
                    azucar_pct_gancia, params_gancia.volumen_objetivo_ml
                )

                composicion_gancia = ComposicionBlendGancia(
                    vino_ml=vino_ml,
                    alcohol_fortificacion_ml=alcohol_fortificacion_ml,
                    tinturas=tinturas_seleccionadas_gancia,
                    agua_ml=agua_ml,
                    azucar_g=azucar_g,
                    acido_citrico_g=acido_citrico_gancia * volumen_gancia,
                    caramelo_ml=caramelo_gancia,
                )

                abv_calculado_gancia = GanciaCalculator.calcular_abv_blend(
                    composicion_gancia,
                    tinturas_data_gancia,
                    vino_abv=vino_abv_gancia,
                    alcohol_fortificacion_abv=alcohol_fortificacion_abv_gancia,
                )

                st.success("✅ Blend de Gancia calculado exitosamente!")

                if agua_ml < 0:
                    st.warning(
                        "⚠️ El agua remanente da negativo: el % de vino más las "
                        "tinturas ya superan el volumen objetivo. Bajá el % de "
                        "vino o el volumen de tinturas."
                    )

                col_r1, col_r2, col_r3, col_r4 = st.columns(4)

                with col_r1:
                    with st.container(border=True):
                        st.metric("ABV Calculado", f"{abv_calculado_gancia:.2f}%")

                volumen_real_gancia_ml = GanciaCalculator.calcular_volumen_con_azucar(
                    composicion_gancia.volumen_total_ml, composicion_gancia.azucar_g
                )

                with col_r2:
                    with st.container(border=True):
                        st.metric(
                            "Volumen total",
                            f"{volumen_real_gancia_ml/1000:.2f}L",
                        )

                with col_r3:
                    with st.container(border=True):
                        st.metric("Vino base", f"{vino_ml:.0f}ml")

                with col_r4:
                    with st.container(border=True):
                        st.metric(
                            "Alcohol fortificación", f"{alcohol_fortificacion_ml:.0f}ml"
                        )

                st.divider()

                st.subheader("📝 Receta Completa")

                col_receta1, col_receta2 = st.columns(2)

                with col_receta1:
                    with st.container(border=True):
                        st.write("**Base vínica:**")
                        st.write(f"- Vino base ({vino_abv_gancia}%): {vino_ml:.0f} ml")
                        st.write(
                            f"- Alcohol fortificación ({alcohol_fortificacion_abv_gancia}%): "
                            f"{alcohol_fortificacion_ml:.0f} ml"
                        )
                        st.write(f"- Agua: {agua_ml:.0f} ml")
                        st.write(f"- Azúcar: {azucar_g:.0f} g")
                        st.write(f"- Ácido cítrico: {composicion_gancia.acido_citrico_g:.1f} g")
                        st.write(f"- Caramelo E150: {caramelo_gancia:.1f} ml")

                with col_receta2:
                    with st.container(border=True):
                        st.write("**Tinturas:**")
                        if tinturas_seleccionadas_gancia:
                            for tid, ml in tinturas_seleccionadas_gancia.items():
                                t = tinturas_data_gancia.get(tid)
                                if t:
                                    st.write(f"- {t.nombre}: {ml:.0f} ml")
                        else:
                            st.caption("Sin tinturas en este blend")

            except Exception as e:
                st.error(f"Error calculando blend de Gancia: {e}")
                import traceback

                st.error(traceback.format_exc())

# =========================================================
# MÓDULO DE MICROMEZCLAS - VERSIÓN SIMPLIFICADA
# =========================================================
elif menu == "🎯 Micromezclas":
    st.title("🎯 Micromezclas Iterativas")
    st.caption("Ajustes de precisión de 0.1ml para optimización fina")

    if not repo:
        st.error("Error: Repositorio no disponible")
        st.stop()

    # Inicializar estado de sesión si no existe
    if "micro_iteraciones" not in st.session_state:
        st.session_state.micro_iteraciones = []
        st.session_state.micro_blend_actual = None

    tabs = st.tabs(["⚙️ Configuración", "📊 Iteraciones", "📈 Resultados"])

    # =========================================================
    # TAB 1: CONFIGURACIÓN INICIAL
    # =========================================================
    with tabs[0]:
        st.subheader("Configuración del Lote Piloto")

        col1, col2 = st.columns(2)

        with col1:
            with st.container(border=True):
                st.write("**📋 Parámetros del Blend Base**")

                volumen_base = st.number_input(
                    "Volumen objetivo (L)",
                    min_value=1.0,
                    max_value=20.0,
                    value=10.0,
                    step=1.0,
                    key="micro_volumen",
                )

                abv_base = st.number_input(
                    "ABV objetivo (%)",
                    min_value=35.0,
                    max_value=45.0,
                    value=40.0,
                    step=0.5,
                    key="micro_abv",
                )

                azucar_base = st.number_input(
                    "Azúcar (g/L)",
                    min_value=160,
                    max_value=220,
                    value=195,
                    step=5,
                    key="micro_azucar",
                )

        with col2:
            with st.container(border=True):
                st.write("**🧪 Tinturas Disponibles**")

                tinturas_stock = repo.listar(estado="lista")

                if not tinturas_stock:
                    st.warning("No hay tinturas disponibles en stock")
                else:
                    # Mostrar selector simple de tinturas
                    opciones_tinturas = {}
                    for t in tinturas_stock[:5]:  # Limitar a 5 para simplicidad
                        opciones_tinturas[t.id] = (
                            f"{t.nombre} ({t.volumen_disponible_ml} ml)"
                        )

                    tintura1_id = st.selectbox(
                        "Tintura 1",
                        options=list(opciones_tinturas.keys()),
                        format_func=lambda x: opciones_tinturas[x],
                        key="micro_t1",
                    )

                    ml1 = st.number_input(
                        "Volumen (ml)",
                        min_value=0,
                        max_value=500,
                        value=50,
                        step=10,
                        key="micro_ml1",
                    )

                    tintura2_id = st.selectbox(
                        "Tintura 2",
                        options=list(opciones_tinturas.keys()),
                        format_func=lambda x: opciones_tinturas[x],
                        key="micro_t2",
                    )

                    ml2 = st.number_input(
                        "Volumen (ml)",
                        min_value=0,
                        max_value=500,
                        value=30,
                        step=10,
                        key="micro_ml2",
                    )

        st.divider()

        # Botón para iniciar
        if st.button(
            "🚀 Iniciar Microblending", type="primary", use_container_width=True
        ):
            # Crear blend base simplificado
            from families.fernet.calculator import BlendParams

            params = BlendParams(
                volumen_objetivo_litros=volumen_base,
                abv_objetivo=abv_base,
                azucar_objetivo_gpl=azucar_base,
            )

            # Preparar tinturas seleccionadas (tintura1_id/ml1/etc. solo
            # existen si tinturas_stock no estaba vacío - ver el selector
            # más arriba)
            tinturas_dict = {}
            if tinturas_stock:
                if ml1 > 0 and tintura1_id:
                    tinturas_dict[tintura1_id] = float(ml1)
                if ml2 > 0 and tintura2_id and tintura2_id != tintura1_id:
                    tinturas_dict[tintura2_id] = float(ml2)
                elif ml2 > 0 and tintura2_id and tintura2_id == tintura1_id:
                    st.warning(
                        "⚠️ Tintura 2 es la misma que Tintura 1 - su volumen "
                        "no se sumó. Elegí una tintura distinta en el slot 2."
                    )

            if not tinturas_dict:
                st.error("Selecciona al menos una tintura")
            else:
                # Obtener datos de tinturas
                tinturas_data = {}
                for tid in tinturas_dict.keys():
                    t = repo.get_by_id(tid)
                    if t:
                        tinturas_data[tid] = t

                blend_result = calculator.calcular_blend_completo(
                    params, tinturas_dict, tinturas_data
                )

                # Guardar en sesión
                st.session_state.micro_blend_actual = blend_result
                st.session_state.micro_iteraciones = [
                    {
                        "numero": 0,
                        "blend": blend_result,
                        "ajustes": [],
                        "evaluacion": None,
                        "timestamp": datetime.now().strftime("%H:%M:%S"),
                    }
                ]

                st.success(f"✅ Blend base creado: {blend_result.id}")
                st.balloons()

    # =========================================================
    # TAB 2: ITERACIONES
    # =========================================================
    with tabs[1]:
        if not st.session_state.micro_iteraciones:
            st.info("👈 Configura un blend base en la pestaña 'Configuración'")
            st.stop()

        st.subheader("Iteraciones del Microblending")

        # Mostrar blend actual
        ultima_iter = st.session_state.micro_iteraciones[-1]

        col1, col2, col3 = st.columns(3)

        with col1:
            with st.container(border=True):
                st.metric("Iteración actual", f"#{ultima_iter['numero']}")

        with col2:
            with st.container(border=True):
                st.metric("ABV", f"{ultima_iter['blend'].abv_calculado:.2f}%")

        with col3:
            with st.container(border=True):
                st.metric(
                    "Total iteraciones", len(st.session_state.micro_iteraciones) - 1
                )

        st.divider()

        # Sección de ajustes
        st.subheader("🔧 Nuevo Ajuste")

        col_a1, col_a2, col_a3 = st.columns(3)

        with col_a1:
            # Tinturas disponibles en el blend actual
            opciones_ajuste = {}
            for tid in ultima_iter["blend"].composicion.tinturas.keys():
                t = repo.get_by_id(tid)
                if t:
                    opciones_ajuste[tid] = t.nombre

            # Añadir opción para nueva tintura
            opciones_ajuste["nueva"] = "➕ Añadir nueva tintura"

            tintura_ajuste = st.selectbox(
                "Tintura a ajustar",
                options=list(opciones_ajuste.keys()),
                format_func=lambda x: opciones_ajuste[x],
                key="ajuste_tintura",
            )

        with col_a2:
            incremento = st.number_input(
                "Incremento (ml)",
                min_value=-0.5,
                max_value=0.5,
                value=0.1,
                step=0.1,
                format="%.1f",
                key="ajuste_inc",
            )

        with col_a3:
            razon = st.selectbox(
                "Razón",
                ["ataque", "equilibrio", "amargor", "persistencia", "complejidad"],
                key="ajuste_razon",
            )

        if st.button("✅ Aplicar Ajuste", use_container_width=True):
            # Crear nueva iteración
            from copy import deepcopy

            nuevo_blend = deepcopy(ultima_iter["blend"])

            if tintura_ajuste == "nueva":
                # Para nueva tintura, usar valores por defecto
                st.info("Funcionalidad de nueva tintura en desarrollo")
            else:
                # Ajustar tintura existente
                if tintura_ajuste in nuevo_blend.composicion.tinturas:
                    nuevo_blend.composicion.tinturas[tintura_ajuste] += incremento
                else:
                    nuevo_blend.composicion.tinturas[tintura_ajuste] = incremento

                # Recalcular ABV: sin esto queda pegado al valor del blend
                # base y no refleja el ajuste que se acaba de aplicar.
                tinturas_data_ajuste = {}
                for tid in nuevo_blend.composicion.tinturas.keys():
                    t = repo.get_by_id(tid)
                    if t:
                        tinturas_data_ajuste[tid] = t
                nuevo_blend.abv_calculado = calculator.calcular_abv_blend(
                    nuevo_blend.composicion, tinturas_data_ajuste
                )

                # Actualizar versión
                version_parts = nuevo_blend.version.split(".")
                nuevo_blend.version = (
                    f"{version_parts[0]}.{version_parts[1]}.{int(version_parts[2]) + 1}"
                )
                nuevo_blend.id = f"{nuevo_blend.id.split('-')[0]}-IT{len(st.session_state.micro_iteraciones)}"

                # Guardar iteración
                st.session_state.micro_iteraciones.append(
                    {
                        "numero": len(st.session_state.micro_iteraciones),
                        "blend": nuevo_blend,
                        "ajustes": [
                            {
                                "tintura": tintura_ajuste,
                                "incremento": incremento,
                                "razon": razon,
                            }
                        ],
                        "evaluacion": None,
                        "timestamp": datetime.now().strftime("%H:%M:%S"),
                    }
                )

                st.success(
                    f"✅ Iteración {len(st.session_state.micro_iteraciones)-1} creada"
                )
                st.rerun()

        st.divider()

        # Tabla de iteraciones
        st.subheader("📋 Historial de Iteraciones")

        data_iter = []
        for i, it in enumerate(st.session_state.micro_iteraciones):
            if i == 0:
                continue  # Saltar iteración base

            ajustes_str = ", ".join(
                [f"{a['tintura'][-4:]}: {a['incremento']:+.1f}" for a in it["ajustes"]]
            )

            data_iter.append(
                {
                    "Iteración": it["numero"],
                    "Ajustes": ajustes_str,
                    "ABV": f"{it['blend'].abv_calculado:.2f}%",
                    "Hora": it["timestamp"],
                    "Evaluada": "✅" if it["evaluacion"] else "⏳",
                }
            )

        if data_iter:
            df_iter = pd.DataFrame(data_iter)
            st.dataframe(df_iter, use_container_width=True, hide_index=True)
        else:
            st.info("No hay iteraciones aún. Aplica tu primer ajuste.")

    # =========================================================
    # TAB 3: RESULTADOS
    # =========================================================
    with tabs[2]:
        if not st.session_state.micro_iteraciones:
            st.info("👈 No hay datos de microblending")
            st.stop()

        st.subheader("Resultados del Microblending")

        # Buscar la mejor iteración (la que tenga evaluación con mayor puntaje)
        mejor_iter = None
        mejor_puntaje = 0

        for it in st.session_state.micro_iteraciones:
            if it["evaluacion"] and it["evaluacion"].get("puntaje", 0) > mejor_puntaje:
                mejor_puntaje = it["evaluacion"]["puntaje"]
                mejor_iter = it

        col_r1, col_r2, col_r3 = st.columns(3)

        with col_r1:
            with st.container(border=True):
                st.metric(
                    "Total iteraciones", len(st.session_state.micro_iteraciones) - 1
                )

        with col_r2:
            with st.container(border=True):
                if mejor_iter:
                    st.metric("Mejor iteración", f"#{mejor_iter['numero']}")
                else:
                    st.metric("Mejor iteración", "Sin evaluaciones")

        with col_r3:
            with st.container(border=True):
                if mejor_iter:
                    st.metric("Puntaje máximo", f"{mejor_puntaje:.1f}")
                else:
                    st.metric("Puntaje máximo", "N/A")

        # Formulario para evaluar una iteración
        st.divider()
        st.subheader("📝 Evaluar Iteración")

        col_e1, col_e2 = st.columns(2)

        with col_e1:
            iter_evaluar = st.selectbox(
                "Seleccionar iteración",
                options=[
                    it["numero"]
                    for it in st.session_state.micro_iteraciones
                    if it["numero"] > 0
                ],
                key="eval_select",
            )

        with col_e2:
            if st.button("➕ Cargar formulario", use_container_width=True):
                st.session_state["eval_iter"] = iter_evaluar

        if "eval_iter" in st.session_state:
            iter_num = st.session_state["eval_iter"]
            iter_data = next(
                (
                    it
                    for it in st.session_state.micro_iteraciones
                    if it["numero"] == iter_num
                ),
                None,
            )

            if iter_data:
                with st.form(f"form_eval_{iter_num}", border=True):
                    st.write(f"**Evaluando Iteración {iter_num}**")

                    col_f1, col_f2 = st.columns(2)

                    with col_f1:
                        ataque = st.slider("Ataque (1-10)", 1, 10, 7)
                        complejidad = st.slider("Complejidad (1-10)", 1, 10, 7)

                    with col_f2:
                        equilibrio = st.slider("Equilibrio (1-10)", 1, 10, 7)
                        persistencia = st.slider("Persistencia (1-10)", 1, 10, 7)

                    notas = st.text_area("Notas de cata")

                    if st.form_submit_button("💾 Guardar Evaluación"):
                        # Calcular puntaje ponderado
                        puntaje = (ataque + complejidad + equilibrio + persistencia) / 4

                        # Guardar evaluación
                        iter_data["evaluacion"] = {
                            "ataque": ataque,
                            "complejidad": complejidad,
                            "equilibrio": equilibrio,
                            "persistencia": persistencia,
                            "puntaje": puntaje,
                            "notas": notas,
                        }

                        st.success(f"✅ Evaluación guardada para iteración {iter_num}")
                        del st.session_state["eval_iter"]
                        time.sleep(1)
                        st.rerun()

        # Gráfico de evolución (si hay evaluaciones)
        st.divider()

        iter_con_eval = [
            (it["numero"], it["evaluacion"]["puntaje"])
            for it in st.session_state.micro_iteraciones
            if it["evaluacion"]
        ]

        if iter_con_eval:
            st.subheader("📈 Evolución del Puntaje")

            nums, puntajes = zip(*iter_con_eval)

            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=list(nums),
                    y=list(puntajes),
                    mode="lines+markers",
                    name="Puntaje",
                    line=dict(color="green", width=3),
                    marker=dict(size=10),
                )
            )

            fig.update_layout(
                xaxis_title="Iteración", yaxis_title="Puntaje", height=400
            )

            st.plotly_chart(fig, use_container_width=True)

        # Botón para resetear
        st.divider()
        if st.button("🔄 Resetear Microblending", use_container_width=True):
            st.session_state.micro_iteraciones = []
            st.session_state.micro_blend_actual = None
            if "eval_iter" in st.session_state:
                del st.session_state["eval_iter"]
            st.success("Microblending reseteado")
            st.rerun()

# =========================================================
# MÓDULO DE MICROMEZCLAS GANCIA
# =========================================================
elif menu == "🎯 Micromezclas Gancia":
    st.title("🎯 Micromezclas Gancia")
    st.caption("Ajustes de precisión de 0.1ml para optimización fina - base vínica")

    if not repo:
        st.error("Error: Repositorio no disponible")
        st.stop()

    from families.gancia.gancia_calculator import (
        ComposicionBlendGancia,
        GanciaBlendParams,
        GanciaBlendResult,
        GanciaCalculator,
    )
    from core.tintura_models import Producto

    gancia_calculator_micro = GanciaCalculator()

    # Inicializar estado de sesión si no existe (namespace separado de Fernet)
    if "micro_gancia_iteraciones" not in st.session_state:
        st.session_state.micro_gancia_iteraciones = []
        st.session_state.micro_gancia_blend_actual = None

    tabs = st.tabs(["⚙️ Configuración", "📊 Iteraciones", "📈 Resultados"])

    # =========================================================
    # TAB 1: CONFIGURACIÓN INICIAL
    # =========================================================
    with tabs[0]:
        st.subheader("Configuración del Lote Piloto")

        col1, col2 = st.columns(2)

        with col1:
            with st.container(border=True):
                st.write("**📋 Parámetros del Blend Base**")

                volumen_base_g = st.number_input(
                    "Volumen objetivo (L)",
                    min_value=1.0,
                    max_value=20.0,
                    value=10.0,
                    step=1.0,
                    key="micro_gancia_volumen",
                )

                abv_base_g = st.number_input(
                    "ABV objetivo (%)",
                    min_value=15.0,
                    max_value=18.0,
                    value=17.0,
                    step=0.5,
                    key="micro_gancia_abv",
                )

                vino_pct_base_g = st.slider(
                    "% Vino sobre el volumen",
                    min_value=75.0,
                    max_value=80.0,
                    value=78.0,
                    step=0.5,
                    key="micro_gancia_vino_pct",
                )

                azucar_pct_base_g = st.slider(
                    "Azúcar (% p/v)",
                    min_value=8.0,
                    max_value=12.0,
                    value=10.0,
                    step=0.5,
                    key="micro_gancia_azucar",
                )

        with col2:
            with st.container(border=True):
                st.write("**🧪 Tinturas de Gancia Disponibles**")

                tinturas_stock_g = repo.listar(
                    estado="lista", producto=Producto.GANCIA.value
                )

                if not tinturas_stock_g:
                    st.warning(
                        "No hay tinturas de Gancia disponibles en stock. Creá y "
                        "finalizá tinturas de producto Gancia en 🧪 Tinturas."
                    )
                else:
                    # Mostrar selector simple de tinturas
                    opciones_tinturas_g = {}
                    for t in tinturas_stock_g[:5]:  # Limitar a 5 para simplicidad
                        opciones_tinturas_g[t.id] = (
                            f"{t.nombre} ({t.volumen_disponible_ml} ml)"
                        )

                    tintura1_id_g = st.selectbox(
                        "Tintura 1",
                        options=list(opciones_tinturas_g.keys()),
                        format_func=lambda x: opciones_tinturas_g[x],
                        key="micro_gancia_t1",
                    )

                    ml1_g = st.number_input(
                        "Volumen (ml)",
                        min_value=0,
                        max_value=500,
                        value=50,
                        step=10,
                        key="micro_gancia_ml1",
                    )

                    tintura2_id_g = st.selectbox(
                        "Tintura 2",
                        options=list(opciones_tinturas_g.keys()),
                        format_func=lambda x: opciones_tinturas_g[x],
                        key="micro_gancia_t2",
                    )

                    ml2_g = st.number_input(
                        "Volumen (ml)",
                        min_value=0,
                        max_value=500,
                        value=30,
                        step=10,
                        key="micro_gancia_ml2",
                    )

        st.divider()

        # Botón para iniciar
        if st.button(
            "🚀 Iniciar Microblending",
            type="primary",
            use_container_width=True,
            key="micro_gancia_iniciar",
        ):
            params_g = GanciaBlendParams(
                volumen_objetivo_litros=volumen_base_g,
                abv_objetivo=abv_base_g,
                vino_pct=vino_pct_base_g / 100,
                azucar_pct_wv=azucar_pct_base_g,
            )

            # Preparar tinturas seleccionadas
            tinturas_dict_g = {}
            if tinturas_stock_g:
                if ml1_g > 0 and tintura1_id_g:
                    tinturas_dict_g[tintura1_id_g] = float(ml1_g)
                if ml2_g > 0 and tintura2_id_g and tintura2_id_g != tintura1_id_g:
                    tinturas_dict_g[tintura2_id_g] = float(ml2_g)
                elif ml2_g > 0 and tintura2_id_g and tintura2_id_g == tintura1_id_g:
                    st.warning(
                        "⚠️ Tintura 2 es la misma que Tintura 1 - su volumen "
                        "no se sumó. Elegí una tintura distinta en el slot 2."
                    )

            if not tinturas_dict_g:
                st.error("Selecciona al menos una tintura")
            else:
                # Obtener datos de tinturas
                tinturas_data_g = {}
                for tid in tinturas_dict_g.keys():
                    t = repo.get_by_id(tid)
                    if t:
                        tinturas_data_g[tid] = t

                tinturas_ml_total_g = sum(tinturas_dict_g.values())
                vino_ml_g, alcohol_fortificacion_ml_g, agua_ml_g = (
                    gancia_calculator_micro.calcular_base_vino_alcohol(
                        params_g, tinturas_ml_total_g
                    )
                )
                azucar_g_g = GanciaCalculator.calcular_azucar(
                    params_g.azucar_pct_wv, params_g.volumen_objetivo_ml
                )

                composicion_g = ComposicionBlendGancia(
                    vino_ml=vino_ml_g,
                    alcohol_fortificacion_ml=alcohol_fortificacion_ml_g,
                    tinturas=tinturas_dict_g,
                    agua_ml=agua_ml_g,
                    azucar_g=azucar_g_g,
                )

                abv_calculado_g = GanciaCalculator.calcular_abv_blend(
                    composicion_g,
                    tinturas_data_g,
                    vino_abv=params_g.vino_abv,
                    alcohol_fortificacion_abv=params_g.alcohol_fortificacion_abv,
                )

                blend_result_g = GanciaBlendResult(
                    params=params_g,
                    composicion=composicion_g,
                    abv_calculado=abv_calculado_g,
                )

                # Guardar en sesión
                st.session_state.micro_gancia_blend_actual = blend_result_g
                st.session_state.micro_gancia_iteraciones = [
                    {
                        "numero": 0,
                        "blend": blend_result_g,
                        "ajustes": [],
                        "evaluacion": None,
                        "timestamp": datetime.now().strftime("%H:%M:%S"),
                    }
                ]

                st.success(f"✅ Blend base creado: {blend_result_g.id}")
                st.balloons()

    # =========================================================
    # TAB 2: ITERACIONES
    # =========================================================
    with tabs[1]:
        if not st.session_state.micro_gancia_iteraciones:
            st.info("👈 Configura un blend base en la pestaña 'Configuración'")
            st.stop()

        st.subheader("Iteraciones del Microblending")

        # Mostrar blend actual
        ultima_iter_g = st.session_state.micro_gancia_iteraciones[-1]

        col1, col2, col3 = st.columns(3)

        with col1:
            with st.container(border=True):
                st.metric("Iteración actual", f"#{ultima_iter_g['numero']}")

        with col2:
            with st.container(border=True):
                st.metric("ABV", f"{ultima_iter_g['blend'].abv_calculado:.2f}%")

        with col3:
            with st.container(border=True):
                st.metric(
                    "Total iteraciones",
                    len(st.session_state.micro_gancia_iteraciones) - 1,
                )

        st.divider()

        # Sección de ajustes
        st.subheader("🔧 Nuevo Ajuste")

        col_a1, col_a2, col_a3 = st.columns(3)

        with col_a1:
            # Tinturas disponibles en el blend actual
            opciones_ajuste_g = {}
            for tid in ultima_iter_g["blend"].composicion.tinturas.keys():
                t = repo.get_by_id(tid)
                if t:
                    opciones_ajuste_g[tid] = t.nombre

            # Añadir opción para nueva tintura (igual que Fernet)
            opciones_ajuste_g["nueva"] = "➕ Añadir nueva tintura"

            tintura_ajuste_g = st.selectbox(
                "Tintura a ajustar",
                options=list(opciones_ajuste_g.keys()),
                format_func=lambda x: opciones_ajuste_g[x],
                key="ajuste_gancia_tintura",
            )

        with col_a2:
            incremento_g = st.number_input(
                "Incremento (ml)",
                min_value=-0.5,
                max_value=0.5,
                value=0.1,
                step=0.1,
                format="%.1f",
                key="ajuste_gancia_inc",
            )

        with col_a3:
            razon_g = st.selectbox(
                "Razón",
                ["ataque", "equilibrio", "amargor", "persistencia", "complejidad"],
                key="ajuste_gancia_razon",
            )

        if st.button(
            "✅ Aplicar Ajuste", use_container_width=True, key="ajuste_gancia_aplicar"
        ):
            if tintura_ajuste_g == "nueva":
                st.info("Funcionalidad de nueva tintura en desarrollo")
            else:
                from copy import deepcopy

                nuevo_blend_g = deepcopy(ultima_iter_g["blend"])

                if tintura_ajuste_g in nuevo_blend_g.composicion.tinturas:
                    nuevo_blend_g.composicion.tinturas[tintura_ajuste_g] += incremento_g
                else:
                    nuevo_blend_g.composicion.tinturas[tintura_ajuste_g] = incremento_g

                # Recalcular ABV con los datos actuales de tinturas
                tinturas_data_ajuste_g = {}
                for tid in nuevo_blend_g.composicion.tinturas.keys():
                    t = repo.get_by_id(tid)
                    if t:
                        tinturas_data_ajuste_g[tid] = t
                nuevo_blend_g.abv_calculado = GanciaCalculator.calcular_abv_blend(
                    nuevo_blend_g.composicion,
                    tinturas_data_ajuste_g,
                    vino_abv=nuevo_blend_g.params.vino_abv,
                    alcohol_fortificacion_abv=nuevo_blend_g.params.alcohol_fortificacion_abv,
                )

                # Actualizar versión
                version_parts_g = nuevo_blend_g.version.split(".")
                nuevo_blend_g.version = (
                    f"{version_parts_g[0]}.{version_parts_g[1]}."
                    f"{int(version_parts_g[2]) + 1}"
                )
                nuevo_blend_g.id = (
                    f"{nuevo_blend_g.id.split('-')[0]}-"
                    f"IT{len(st.session_state.micro_gancia_iteraciones)}"
                )

                # Guardar iteración
                st.session_state.micro_gancia_iteraciones.append(
                    {
                        "numero": len(st.session_state.micro_gancia_iteraciones),
                        "blend": nuevo_blend_g,
                        "ajustes": [
                            {
                                "tintura": tintura_ajuste_g,
                                "incremento": incremento_g,
                                "razon": razon_g,
                            }
                        ],
                        "evaluacion": None,
                        "timestamp": datetime.now().strftime("%H:%M:%S"),
                    }
                )

                st.success(
                    f"✅ Iteración {len(st.session_state.micro_gancia_iteraciones)-1} creada"
                )
                st.rerun()

        st.divider()

        # Tabla de iteraciones
        st.subheader("📋 Historial de Iteraciones")

        data_iter_g = []
        for i, it in enumerate(st.session_state.micro_gancia_iteraciones):
            if i == 0:
                continue  # Saltar iteración base

            ajustes_str_g = ", ".join(
                [f"{a['tintura'][-4:]}: {a['incremento']:+.1f}" for a in it["ajustes"]]
            )

            data_iter_g.append(
                {
                    "Iteración": it["numero"],
                    "Ajustes": ajustes_str_g,
                    "ABV": f"{it['blend'].abv_calculado:.2f}%",
                    "Hora": it["timestamp"],
                    "Evaluada": "✅" if it["evaluacion"] else "⏳",
                }
            )

        if data_iter_g:
            df_iter_g = pd.DataFrame(data_iter_g)
            st.dataframe(df_iter_g, use_container_width=True, hide_index=True)
        else:
            st.info("No hay iteraciones aún. Aplica tu primer ajuste.")

    # =========================================================
    # TAB 3: RESULTADOS
    # =========================================================
    with tabs[2]:
        if not st.session_state.micro_gancia_iteraciones:
            st.info("👈 No hay datos de microblending")
            st.stop()

        st.subheader("Resultados del Microblending")

        # Buscar la mejor iteración (la que tenga evaluación con mayor puntaje)
        mejor_iter_g = None
        mejor_puntaje_g = 0

        for it in st.session_state.micro_gancia_iteraciones:
            if it["evaluacion"] and it["evaluacion"].get("puntaje", 0) > mejor_puntaje_g:
                mejor_puntaje_g = it["evaluacion"]["puntaje"]
                mejor_iter_g = it

        col_r1, col_r2, col_r3 = st.columns(3)

        with col_r1:
            with st.container(border=True):
                st.metric(
                    "Total iteraciones",
                    len(st.session_state.micro_gancia_iteraciones) - 1,
                )

        with col_r2:
            with st.container(border=True):
                if mejor_iter_g:
                    st.metric("Mejor iteración", f"#{mejor_iter_g['numero']}")
                else:
                    st.metric("Mejor iteración", "Sin evaluaciones")

        with col_r3:
            with st.container(border=True):
                if mejor_iter_g:
                    st.metric("Puntaje máximo", f"{mejor_puntaje_g:.1f}")
                else:
                    st.metric("Puntaje máximo", "N/A")

        # Formulario para evaluar una iteración
        st.divider()
        st.subheader("📝 Evaluar Iteración")

        col_e1, col_e2 = st.columns(2)

        with col_e1:
            iter_evaluar_g = st.selectbox(
                "Seleccionar iteración",
                options=[
                    it["numero"]
                    for it in st.session_state.micro_gancia_iteraciones
                    if it["numero"] > 0
                ],
                key="eval_gancia_select",
            )

        with col_e2:
            if st.button(
                "➕ Cargar formulario",
                use_container_width=True,
                key="eval_gancia_cargar",
            ):
                st.session_state["eval_gancia_iter"] = iter_evaluar_g

        if "eval_gancia_iter" in st.session_state:
            iter_num_g = st.session_state["eval_gancia_iter"]
            iter_data_g = next(
                (
                    it
                    for it in st.session_state.micro_gancia_iteraciones
                    if it["numero"] == iter_num_g
                ),
                None,
            )

            if iter_data_g:
                with st.form(f"form_eval_gancia_{iter_num_g}", border=True):
                    st.write(f"**Evaluando Iteración {iter_num_g}**")

                    col_f1, col_f2 = st.columns(2)

                    with col_f1:
                        ataque_g = st.slider("Ataque (1-10)", 1, 10, 7)
                        complejidad_g = st.slider("Complejidad (1-10)", 1, 10, 7)

                    with col_f2:
                        equilibrio_g = st.slider("Equilibrio (1-10)", 1, 10, 7)
                        persistencia_g = st.slider("Persistencia (1-10)", 1, 10, 7)

                    notas_g = st.text_area("Notas de cata")

                    if st.form_submit_button("💾 Guardar Evaluación"):
                        puntaje_g = (
                            ataque_g + complejidad_g + equilibrio_g + persistencia_g
                        ) / 4

                        iter_data_g["evaluacion"] = {
                            "ataque": ataque_g,
                            "complejidad": complejidad_g,
                            "equilibrio": equilibrio_g,
                            "persistencia": persistencia_g,
                            "puntaje": puntaje_g,
                            "notas": notas_g,
                        }

                        st.success(f"✅ Evaluación guardada para iteración {iter_num_g}")
                        del st.session_state["eval_gancia_iter"]
                        time.sleep(1)
                        st.rerun()

        # Gráfico de evolución (si hay evaluaciones)
        st.divider()

        iter_con_eval_g = [
            (it["numero"], it["evaluacion"]["puntaje"])
            for it in st.session_state.micro_gancia_iteraciones
            if it["evaluacion"]
        ]

        if iter_con_eval_g:
            st.subheader("📈 Evolución del Puntaje")

            nums_g, puntajes_g = zip(*iter_con_eval_g)

            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=list(nums_g),
                    y=list(puntajes_g),
                    mode="lines+markers",
                    name="Puntaje",
                    line=dict(color="green", width=3),
                    marker=dict(size=10),
                )
            )

            fig.update_layout(
                xaxis_title="Iteración", yaxis_title="Puntaje", height=400
            )

            st.plotly_chart(fig, use_container_width=True)

        # Botón para resetear
        st.divider()
        if st.button(
            "🔄 Resetear Microblending",
            use_container_width=True,
            key="micro_gancia_resetear",
        ):
            st.session_state.micro_gancia_iteraciones = []
            st.session_state.micro_gancia_blend_actual = None
            if "eval_gancia_iter" in st.session_state:
                del st.session_state["eval_gancia_iter"]
            st.success("Microblending reseteado")
            st.rerun()


# =========================================================
# MÓDULO DE PRUEBAS A/B
# =========================================================
elif menu == "⚖️ Pruebas A/B":
    st.title("⚖️ Pruebas A/B y Análisis Competitivo")
    st.caption("Comparación ciega contra referencias de mercado")

    if not repo:
        st.error("Error: Repositorio no disponible")
        st.stop()

    # Inicializar estado de sesión
    if "pruebas_ab" not in st.session_state:
        st.session_state.pruebas_ab = []
    if "prueba_actual" not in st.session_state:
        st.session_state.prueba_actual = None

    tabs = st.tabs(
        ["🎯 Nueva Prueba", "📊 Resultados", "📈 Análisis Competitivo", "📋 Historial"]
    )

    # =========================================================
    # TAB 1: NUEVA PRUEBA
    # =========================================================
    with tabs[0]:
        st.subheader("Configurar Nueva Prueba A/B")

        col1, col2 = st.columns(2)

        with col1:
            with st.container(border=True):
                st.write("**🧪 Nuestra Fórmula**")

                # Obtener blends disponibles (de sesión o crear uno nuevo)
                opciones_blends = {}

                # Buscar en sesión si hay blends de microblending
                if (
                    "micro_iteraciones" in st.session_state
                    and st.session_state.micro_iteraciones
                ):
                    for it in st.session_state.micro_iteraciones:
                        if it["numero"] > 0 and it.get("blend"):
                            blend = it["blend"]
                            opciones_blends[f"BLEND-{it['numero']}"] = (
                                f"Iteración {it['numero']} (ABV: {blend.abv_calculado:.1f}%)"
                            )

                # Añadir opción para blend personalizado
                opciones_blends["custom"] = "✏️ Blend personalizado"

                blend_seleccionado = st.selectbox(
                    "Seleccionar blend",
                    options=list(opciones_blends.keys()),
                    format_func=lambda x: opciones_blends[x],
                    key="ab_blend",
                )

                if blend_seleccionado == "custom":
                    st.text_input(
                        "Nombre del blend",
                        value="Mi Blend Experimental",
                        key="ab_nombre_custom",
                    )

                    col_c1, col_c2 = st.columns(2)
                    with col_c1:
                        st.number_input(
                            "ABV (%)", value=40.0, step=0.5, key="ab_abv_custom"
                        )
                    with col_c2:
                        st.number_input(
                            "Azúcar (g/L)", value=195, step=5, key="ab_azucar_custom"
                        )

        with col2:
            with st.container(border=True):
                st.write("**🥇 Referencia de Mercado**")

                referencias = {
                    "branca": "Fernet Branca",
                    "vittone": "Fernet Vittone",
                    "1882": "Fernet 1882",
                    "cinzano": "Cinzano Fernet",
                    "capri": "Capri Fernet",
                    "otra": "Otra referencia",
                }

                ref_seleccionada = st.selectbox(
                    "Seleccionar referencia",
                    options=list(referencias.keys()),
                    format_func=lambda x: referencias[x],
                    key="ab_referencia",
                )

                if ref_seleccionada == "otra":
                    st.text_input("Nombre de la referencia", key="ab_ref_otra")

        st.divider()

        # Configuración de la prueba
        st.subheader("⚙️ Configuración de la Prueba")

        col_p1, col_p2, col_p3 = st.columns(3)

        with col_p1:
            tipo_prueba = st.radio(
                "Tipo de prueba",
                ["A/B Simple", "Triangular (2 iguales, 1 diferente)"],
                key="ab_tipo",
            )

        with col_p2:
            num_catadores = st.number_input(
                "Número de catadores",
                min_value=1,
                max_value=20,
                value=3,
                key="ab_catadores",
            )

        with col_p3:
            ciego = st.checkbox("Prueba a ciegas", value=True, key="ab_ciego")

        st.divider()

        # Atributos a evaluar
        st.subheader("📊 Atributos a Evaluar")

        col_a1, col_a2, col_a3 = st.columns(3)

        with col_a1:
            eval_ataque = st.checkbox("Ataque", value=True, key="ab_ataque")
            eval_complejidad = st.checkbox(
                "Complejidad", value=True, key="ab_complejidad"
            )

        with col_a2:
            eval_equilibrio = st.checkbox("Equilibrio", value=True, key="ab_equilibrio")
            eval_persistencia = st.checkbox(
                "Persistencia", value=True, key="ab_persistencia"
            )

        with col_a3:
            eval_amargor = st.checkbox("Amargor", value=True, key="ab_amargor")
            eval_aroma = st.checkbox("Aroma", value=False, key="ab_aroma")

        # Botón para iniciar prueba
        if st.button("🚀 Iniciar Prueba", type="primary", use_container_width=True):
            # Generar ID de prueba
            import uuid

            prueba_id = f"AB-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:4].upper()}"

            # Generar códigos para muestras ciegas
            import random

            codigos = [
                f"M{random.randint(100, 999)}"
                for _ in range(
                    3 if tipo_prueba == "Triangular (2 iguales, 1 diferente)" else 2
                )
            ]

            # Crear prueba
            nueva_prueba = {
                "id": prueba_id,
                "fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
                "tipo": tipo_prueba,
                "ciego": ciego,
                "num_catadores": num_catadores,
                "atributos": {
                    "ataque": eval_ataque,
                    "complejidad": eval_complejidad,
                    "equilibrio": eval_equilibrio,
                    "persistencia": eval_persistencia,
                    "amargor": eval_amargor,
                    "aroma": eval_aroma,
                },
                "blend": blend_seleccionado,
                "referencia": ref_seleccionada,
                "codigos": codigos,
                "resultados": [],
                "completada": False,
            }

            st.session_state.prueba_actual = nueva_prueba
            st.session_state.pruebas_ab.append(nueva_prueba)

            st.success(f"✅ Prueba creada: {prueba_id}")
            st.balloons()

    # =========================================================
    # TAB 2: RESULTADOS
    # =========================================================
    with tabs[1]:
        if not st.session_state.prueba_actual:
            st.info("👈 Crea una prueba primero en la pestaña 'Nueva Prueba'")
            st.stop()

        prueba = st.session_state.prueba_actual

        st.subheader(f"Prueba: {prueba['id']}")

        col_r1, col_r2 = st.columns(2)

        with col_r1:
            with st.container(border=True):
                st.write(f"**Tipo:** {prueba['tipo']}")
                st.write(f"**Fecha:** {prueba['fecha']}")
                st.write(f"**Catadores:** {prueba['num_catadores']}")

        with col_r2:
            with st.container(border=True):
                st.write(f"**Códigos de muestra:**")
                for i, codigo in enumerate(prueba["codigos"]):
                    st.write(f"  • {codigo}")

        st.divider()

        # Formulario para ingresar resultados
        st.subheader("📝 Ingresar Resultados")

        # Determinar qué muestra es nuestra y cuál es referencia
        if prueba["ciego"]:
            st.info("🔍 Prueba a ciegas - los códigos están aleatorizados")

            # En prueba ciega, el catador no sabe qué código corresponde a qué
            col_cod1, col_cod2 = st.columns(2)

            with col_cod1:
                st.write("**Muestras disponibles:**")
                for codigo in prueba["codigos"]:
                    st.write(f"• {codigo}")

            with col_cod2:
                st.write("**Instrucciones:**")
                st.write("1. Prueba las muestras en orden aleatorio")
                st.write("2. Identifica cuál prefieres")
                st.write("3. Registra los puntajes por atributo")
        else:
            st.info("🔓 Prueba abierta - las muestras están identificadas")

        # Formulario de resultados por catador
        with st.form("form_resultados", border=True):
            st.write("**Registrar evaluación de catador**")

            col_f1, col_f2 = st.columns(2)

            with col_f1:
                catador_nombre = st.text_input(
                    "Nombre del catador", value=f"Catador {len(prueba['resultados'])+1}"
                )

                if prueba["tipo"] == "A/B Simple":
                    preferencia = st.radio(
                        "¿Cuál prefieres?",
                        options=[prueba["codigos"][0], prueba["codigos"][1], "Empate"],
                        horizontal=True,
                    )
                else:  # Triangular
                    codigo_diferente = st.selectbox(
                        "¿Cuál es la muestra diferente?", options=prueba["codigos"]
                    )

            with col_f2:
                st.write("**Puntajes (1-10):**")

                puntajes = {}
                cols_p = st.columns(2)

                with cols_p[0]:
                    if prueba["atributos"]["ataque"]:
                        puntajes["ataque"] = st.slider(
                            "Ataque", 1, 10, 7, key="p_ataque"
                        )
                    if prueba["atributos"]["complejidad"]:
                        puntajes["complejidad"] = st.slider(
                            "Complejidad", 1, 10, 7, key="p_complejidad"
                        )
                    if prueba["atributos"]["equilibrio"]:
                        puntajes["equilibrio"] = st.slider(
                            "Equilibrio", 1, 10, 7, key="p_equilibrio"
                        )

                with cols_p[1]:
                    if prueba["atributos"]["persistencia"]:
                        puntajes["persistencia"] = st.slider(
                            "Persistencia", 1, 10, 7, key="p_persistencia"
                        )
                    if prueba["atributos"]["amargor"]:
                        puntajes["amargor"] = st.slider(
                            "Amargor", 1, 10, 7, key="p_amargor"
                        )
                    if prueba["atributos"]["aroma"]:
                        puntajes["aroma"] = st.slider("Aroma", 1, 10, 7, key="p_aroma")

            comentarios = st.text_area("Comentarios del catador")

            submitted = st.form_submit_button("💾 Guardar Evaluación")

            if submitted:
                resultado = {
                    "catador": catador_nombre,
                    "fecha": datetime.now().strftime("%H:%M:%S"),
                    "puntajes": puntajes,
                    "comentarios": comentarios,
                }

                if prueba["tipo"] == "A/B Simple":
                    resultado["preferencia"] = preferencia
                else:
                    resultado["codigo_diferente"] = codigo_diferente

                prueba["resultados"].append(resultado)
                st.success(f"✅ Evaluación de {catador_nombre} guardada")
                st.rerun()

        # Resultados ingresados
        if prueba["resultados"]:
            st.divider()
            st.subheader("📋 Resultados Ingresados")

            data_res = []
            for r in prueba["resultados"]:
                if prueba["tipo"] == "A/B Simple":
                    resumen = f"Prefiere: {r['preferencia']}"
                else:
                    resumen = f"Diferente: {r['codigo_diferente']}"

                data_res.append(
                    {
                        "Catador": r["catador"],
                        "Resultado": resumen,
                        "Puntaje prom": f"{sum(r['puntajes'].values())/len(r['puntajes']):.1f}",
                        "Hora": r["fecha"],
                    }
                )

            df_res = pd.DataFrame(data_res)
            st.dataframe(df_res, use_container_width=True, hide_index=True)

            # Botón para finalizar prueba
            if (
                len(prueba["resultados"]) >= prueba["num_catadores"]
                and not prueba["completada"]
            ):
                if st.button(
                    "✅ Finalizar Prueba", type="primary", use_container_width=True
                ):
                    prueba["completada"] = True
                    st.success(
                        "Prueba finalizada. Ve a la pestaña 'Análisis Competitivo' para ver resultados."
                    )
                    st.rerun()

    # =========================================================
    # TAB 3: ANÁLISIS COMPETITIVO
    # =========================================================
    with tabs[2]:
        if not st.session_state.pruebas_ab:
            st.info("No hay pruebas realizadas")
            st.stop()

        # Seleccionar prueba para analizar
        pruebas_completadas = [
            p for p in st.session_state.pruebas_ab if p.get("completada", False)
        ]

        if not pruebas_completadas:
            st.warning("No hay pruebas completadas. Finaliza una prueba primero.")
            st.stop()

        prueba_analizar = st.selectbox(
            "Seleccionar prueba para analizar",
            options=[p["id"] for p in pruebas_completadas],
            format_func=lambda x: f"{x} - {next((p['fecha'] for p in pruebas_completadas if p['id']==x), '')}",
            key="analisis_select",
        )

        prueba = next(
            (p for p in pruebas_completadas if p["id"] == prueba_analizar), None
        )

        if prueba:
            st.subheader(f"Análisis de {prueba['id']}")

            col_a1, col_a2 = st.columns(2)

            with col_a1:
                with st.container(border=True):
                    st.write("**📊 Estadísticas Generales**")
                    st.write(f"Total catadores: {len(prueba['resultados'])}")

                    if prueba["tipo"] == "A/B Simple":
                        # Contar preferencias
                        preferencias = {}
                        for r in prueba["resultados"]:
                            pref = r["preferencia"]
                            preferencias[pref] = preferencias.get(pref, 0) + 1

                        for pref, count in preferencias.items():
                            st.metric(
                                f"Prefiere {pref}",
                                f"{count} ({count/len(prueba['resultados'])*100:.0f}%)",
                            )

            with col_a2:
                with st.container(border=True):
                    st.write("**📈 Puntajes Promedio**")

                    # Calcular promedios de atributos
                    atributos_prom = {}
                    for r in prueba["resultados"]:
                        for attr, val in r["puntajes"].items():
                            if attr not in atributos_prom:
                                atributos_prom[attr] = []
                            atributos_prom[attr].append(val)

                    for attr, vals in atributos_prom.items():
                        prom = sum(vals) / len(vals)
                        st.metric(attr.capitalize(), f"{prom:.1f}/10")

            st.divider()

            # Gráfico de radar comparativo
            st.subheader("🕸️ Perfil Sensorial Promedio")

            if atributos_prom:
                categorias = list(atributos_prom.keys())
                valores = [sum(vals) / len(vals) for vals in atributos_prom.values()]

                # Valores de referencia (simulados - en producción vendrían de BD)
                valores_ref = [7.5, 8.0, 7.8, 8.2, 7.5][: len(categorias)]

                fig = go.Figure()

                fig.add_trace(
                    go.Scatterpolar(
                        r=valores,
                        theta=categorias,
                        fill="toself",
                        name="Nuestra Fórmula",
                        line_color="blue",
                    )
                )

                fig.add_trace(
                    go.Scatterpolar(
                        r=valores_ref,
                        theta=categorias,
                        fill="toself",
                        name=referencias.get(
                            prueba["referencia"], prueba["referencia"]
                        ),
                        line_color="red",
                    )
                )

                fig.update_layout(
                    polar=dict(radialaxis=dict(visible=True, range=[0, 10])),
                    showlegend=True,
                    height=500,
                )

                st.plotly_chart(fig, use_container_width=True)

            # Análisis de significancia estadística
            st.divider()
            st.subheader("📊 Significancia Estadística")

            if prueba["tipo"] == "Triangular (2 iguales, 1 diferente)":
                # Prueba triangular
                aciertos = 0
                for r in prueba["resultados"]:
                    # En prueba triangular, el código diferente debería ser el nuestro
                    # Esto es una simplificación
                    if (
                        r.get("codigo_diferente") == prueba["codigos"][0]
                    ):  # Asumiendo que nuestra muestra es el primer código
                        aciertos += 1

                total = len(prueba["resultados"])
                tasa_aciertos = aciertos / total if total > 0 else 0

                st.metric("Tasa de aciertos", f"{tasa_aciertos:.1%}")

                # Prueba binomial simplificada
                if tasa_aciertos > 0.5:
                    st.success(
                        "✅ Los catadores pueden distinguir nuestra fórmula significativamente"
                    )
                else:
                    st.warning("⚠️ No hay diferencia significativa detectable")

            else:  # A/B Simple
                # Calcular preferencia neta
                pref_nuestra = sum(
                    1
                    for r in prueba["resultados"]
                    if r["preferencia"] == prueba["codigos"][0]
                )
                pref_ref = sum(
                    1
                    for r in prueba["resultados"]
                    if r["preferencia"] == prueba["codigos"][1]
                )
                empates = sum(
                    1 for r in prueba["resultados"] if r["preferencia"] == "Empate"
                )

                total = len(prueba["resultados"])

                col_s1, col_s2, col_s3 = st.columns(3)

                with col_s1:
                    st.metric(
                        "Prefieren nuestra",
                        f"{pref_nuestra} ({pref_nuestra/total*100:.0f}%)",
                    )
                with col_s2:
                    st.metric(
                        "Prefieren referencia",
                        f"{pref_ref} ({pref_ref/total*100:.0f}%)",
                    )
                with col_s3:
                    st.metric("Empates", f"{empates} ({empates/total*100:.0f}%)")

                if pref_nuestra > pref_ref:
                    st.success("✅ Nuestra fórmula es preferida sobre la referencia")
                elif pref_ref > pref_nuestra:
                    st.warning("⚠️ La referencia es preferida sobre nuestra fórmula")
                else:
                    st.info("📊 Empate técnico")

    # =========================================================
    # TAB 4: HISTORIAL
    # =========================================================
    with tabs[3]:
        st.subheader("📋 Historial de Pruebas")

        if not st.session_state.pruebas_ab:
            st.info("No hay pruebas registradas")
            st.stop()

        data_historial = []
        for p in st.session_state.pruebas_ab:
            data_historial.append(
                {
                    "ID": p["id"],
                    "Fecha": p["fecha"],
                    "Tipo": p["tipo"],
                    "Catadores": f"{len(p['resultados'])}/{p['num_catadores']}",
                    "Estado": "✅ Completada" if p.get("completada") else "⏳ En curso",
                    "Referencia": referencias.get(p["referencia"], p["referencia"]),
                }
            )

        df_historial = pd.DataFrame(data_historial)
        st.dataframe(df_historial, use_container_width=True, hide_index=True)

        # Opción para cargar prueba anterior
        if st.button("🔄 Cargar prueba seleccionada", use_container_width=True):
            # Esta funcionalidad requeriría un selector
            st.info("Selecciona una prueba de la tabla para cargarla (doble clic)")

# =========================================================
# MÓDULO DE PRUEBAS A/B GANCIA
# =========================================================
elif menu == "⚖️ Pruebas A/B Gancia":
    st.title("⚖️ Pruebas A/B y Análisis Competitivo - Gancia")
    st.caption("Comparación ciega contra referencias de mercado")

    if not repo:
        st.error("Error: Repositorio no disponible")
        st.stop()

    # Inicializar estado de sesión (namespace separado de Fernet)
    if "pruebas_ab_gancia" not in st.session_state:
        st.session_state.pruebas_ab_gancia = []
    if "prueba_actual_gancia" not in st.session_state:
        st.session_state.prueba_actual_gancia = None

    tabs = st.tabs(
        ["🎯 Nueva Prueba", "📊 Resultados", "📈 Análisis Competitivo", "📋 Historial"]
    )

    # =========================================================
    # TAB 1: NUEVA PRUEBA
    # =========================================================
    with tabs[0]:
        st.subheader("Configurar Nueva Prueba A/B")

        col1, col2 = st.columns(2)

        with col1:
            with st.container(border=True):
                st.write("**🧪 Nuestra Fórmula**")

                opciones_blends_g = {}

                if (
                    "micro_gancia_iteraciones" in st.session_state
                    and st.session_state.micro_gancia_iteraciones
                ):
                    for it in st.session_state.micro_gancia_iteraciones:
                        if it["numero"] > 0 and it.get("blend"):
                            blend = it["blend"]
                            opciones_blends_g[f"BLEND-{it['numero']}"] = (
                                f"Iteración {it['numero']} (ABV: {blend.abv_calculado:.1f}%)"
                            )

                opciones_blends_g["custom"] = "✏️ Blend personalizado"

                blend_seleccionado_g = st.selectbox(
                    "Seleccionar blend",
                    options=list(opciones_blends_g.keys()),
                    format_func=lambda x: opciones_blends_g[x],
                    key="ab_gancia_blend",
                )

                if blend_seleccionado_g == "custom":
                    st.text_input(
                        "Nombre del blend",
                        value="Mi Blend Experimental",
                        key="ab_gancia_nombre_custom",
                    )

                    col_c1, col_c2 = st.columns(2)
                    with col_c1:
                        st.number_input(
                            "ABV (%)", value=17.0, step=0.5, key="ab_gancia_abv_custom"
                        )
                    with col_c2:
                        st.number_input(
                            "Azúcar (% p/v)",
                            value=10.0,
                            step=0.5,
                            key="ab_gancia_azucar_custom",
                        )

        with col2:
            with st.container(border=True):
                st.write("**🥇 Referencia de Mercado**")

                referencias_gancia = {
                    "gancia_clasico": "Gancia Clásico",
                    "cinzano": "Cinzano",
                    "martini": "Martini",
                    "otra": "Otra referencia",
                }

                ref_seleccionada_g = st.selectbox(
                    "Seleccionar referencia",
                    options=list(referencias_gancia.keys()),
                    format_func=lambda x: referencias_gancia[x],
                    key="ab_gancia_referencia",
                )

                if ref_seleccionada_g == "otra":
                    st.text_input(
                        "Nombre de la referencia", key="ab_gancia_ref_otra"
                    )

        st.divider()

        # Configuración de la prueba
        st.subheader("⚙️ Configuración de la Prueba")

        col_p1, col_p2, col_p3 = st.columns(3)

        with col_p1:
            tipo_prueba_g = st.radio(
                "Tipo de prueba",
                ["A/B Simple", "Triangular (2 iguales, 1 diferente)"],
                key="ab_gancia_tipo",
            )

        with col_p2:
            num_catadores_g = st.number_input(
                "Número de catadores",
                min_value=1,
                max_value=20,
                value=3,
                key="ab_gancia_catadores",
            )

        with col_p3:
            ciego_g = st.checkbox("Prueba a ciegas", value=True, key="ab_gancia_ciego")

        st.divider()

        # Atributos a evaluar
        st.subheader("📊 Atributos a Evaluar")

        col_a1, col_a2, col_a3 = st.columns(3)

        with col_a1:
            eval_ataque_g = st.checkbox("Ataque", value=True, key="ab_gancia_ataque")
            eval_complejidad_g = st.checkbox(
                "Complejidad", value=True, key="ab_gancia_complejidad"
            )

        with col_a2:
            eval_equilibrio_g = st.checkbox(
                "Equilibrio", value=True, key="ab_gancia_equilibrio"
            )
            eval_persistencia_g = st.checkbox(
                "Persistencia", value=True, key="ab_gancia_persistencia"
            )

        with col_a3:
            eval_amargor_g = st.checkbox("Amargor", value=True, key="ab_gancia_amargor")
            eval_aroma_g = st.checkbox("Aroma", value=False, key="ab_gancia_aroma")

        # Botón para iniciar prueba
        if st.button(
            "🚀 Iniciar Prueba",
            type="primary",
            use_container_width=True,
            key="ab_gancia_iniciar",
        ):
            import uuid
            import random

            prueba_id_g = f"ABG-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:4].upper()}"

            codigos_g = [
                f"M{random.randint(100, 999)}"
                for _ in range(
                    3 if tipo_prueba_g == "Triangular (2 iguales, 1 diferente)" else 2
                )
            ]

            nueva_prueba_g = {
                "id": prueba_id_g,
                "fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
                "tipo": tipo_prueba_g,
                "ciego": ciego_g,
                "num_catadores": num_catadores_g,
                "atributos": {
                    "ataque": eval_ataque_g,
                    "complejidad": eval_complejidad_g,
                    "equilibrio": eval_equilibrio_g,
                    "persistencia": eval_persistencia_g,
                    "amargor": eval_amargor_g,
                    "aroma": eval_aroma_g,
                },
                "blend": blend_seleccionado_g,
                "referencia": ref_seleccionada_g,
                "codigos": codigos_g,
                "resultados": [],
                "completada": False,
            }

            st.session_state.prueba_actual_gancia = nueva_prueba_g
            st.session_state.pruebas_ab_gancia.append(nueva_prueba_g)

            st.success(f"✅ Prueba creada: {prueba_id_g}")
            st.balloons()

    # =========================================================
    # TAB 2: RESULTADOS
    # =========================================================
    with tabs[1]:
        if not st.session_state.prueba_actual_gancia:
            st.info("👈 Crea una prueba primero en la pestaña 'Nueva Prueba'")
            st.stop()

        prueba_g = st.session_state.prueba_actual_gancia

        st.subheader(f"Prueba: {prueba_g['id']}")

        col_r1, col_r2 = st.columns(2)

        with col_r1:
            with st.container(border=True):
                st.write(f"**Tipo:** {prueba_g['tipo']}")
                st.write(f"**Fecha:** {prueba_g['fecha']}")
                st.write(f"**Catadores:** {prueba_g['num_catadores']}")

        with col_r2:
            with st.container(border=True):
                st.write(f"**Códigos de muestra:**")
                for codigo in prueba_g["codigos"]:
                    st.write(f"  • {codigo}")

        st.divider()

        st.subheader("📝 Ingresar Resultados")

        if prueba_g["ciego"]:
            st.info("🔍 Prueba a ciegas - los códigos están aleatorizados")

            col_cod1, col_cod2 = st.columns(2)

            with col_cod1:
                st.write("**Muestras disponibles:**")
                for codigo in prueba_g["codigos"]:
                    st.write(f"• {codigo}")

            with col_cod2:
                st.write("**Instrucciones:**")
                st.write("1. Prueba las muestras en orden aleatorio")
                st.write("2. Identifica cuál prefieres")
                st.write("3. Registra los puntajes por atributo")
        else:
            st.info("🔓 Prueba abierta - las muestras están identificadas")

        with st.form("form_resultados_gancia", border=True):
            st.write("**Registrar evaluación de catador**")

            col_f1, col_f2 = st.columns(2)

            with col_f1:
                catador_nombre_g = st.text_input(
                    "Nombre del catador",
                    value=f"Catador {len(prueba_g['resultados'])+1}",
                )

                if prueba_g["tipo"] == "A/B Simple":
                    preferencia_g = st.radio(
                        "¿Cuál prefieres?",
                        options=[
                            prueba_g["codigos"][0],
                            prueba_g["codigos"][1],
                            "Empate",
                        ],
                        horizontal=True,
                    )
                else:  # Triangular
                    codigo_diferente_g = st.selectbox(
                        "¿Cuál es la muestra diferente?", options=prueba_g["codigos"]
                    )

            with col_f2:
                st.write("**Puntajes (1-10):**")

                puntajes_g = {}
                cols_p = st.columns(2)

                with cols_p[0]:
                    if prueba_g["atributos"]["ataque"]:
                        puntajes_g["ataque"] = st.slider(
                            "Ataque", 1, 10, 7, key="p_gancia_ataque"
                        )
                    if prueba_g["atributos"]["complejidad"]:
                        puntajes_g["complejidad"] = st.slider(
                            "Complejidad", 1, 10, 7, key="p_gancia_complejidad"
                        )
                    if prueba_g["atributos"]["equilibrio"]:
                        puntajes_g["equilibrio"] = st.slider(
                            "Equilibrio", 1, 10, 7, key="p_gancia_equilibrio"
                        )

                with cols_p[1]:
                    if prueba_g["atributos"]["persistencia"]:
                        puntajes_g["persistencia"] = st.slider(
                            "Persistencia", 1, 10, 7, key="p_gancia_persistencia"
                        )
                    if prueba_g["atributos"]["amargor"]:
                        puntajes_g["amargor"] = st.slider(
                            "Amargor", 1, 10, 7, key="p_gancia_amargor"
                        )
                    if prueba_g["atributos"]["aroma"]:
                        puntajes_g["aroma"] = st.slider(
                            "Aroma", 1, 10, 7, key="p_gancia_aroma"
                        )

            comentarios_g = st.text_area("Comentarios del catador")

            submitted_g = st.form_submit_button("💾 Guardar Evaluación")

            if submitted_g:
                resultado_g = {
                    "catador": catador_nombre_g,
                    "fecha": datetime.now().strftime("%H:%M:%S"),
                    "puntajes": puntajes_g,
                    "comentarios": comentarios_g,
                }

                if prueba_g["tipo"] == "A/B Simple":
                    resultado_g["preferencia"] = preferencia_g
                else:
                    resultado_g["codigo_diferente"] = codigo_diferente_g

                prueba_g["resultados"].append(resultado_g)
                st.success(f"✅ Evaluación de {catador_nombre_g} guardada")
                st.rerun()

        if prueba_g["resultados"]:
            st.divider()
            st.subheader("📋 Resultados Ingresados")

            data_res_g = []
            for r in prueba_g["resultados"]:
                if prueba_g["tipo"] == "A/B Simple":
                    resumen_g = f"Prefiere: {r['preferencia']}"
                else:
                    resumen_g = f"Diferente: {r['codigo_diferente']}"

                data_res_g.append(
                    {
                        "Catador": r["catador"],
                        "Resultado": resumen_g,
                        "Puntaje prom": f"{sum(r['puntajes'].values())/len(r['puntajes']):.1f}",
                        "Hora": r["fecha"],
                    }
                )

            df_res_g = pd.DataFrame(data_res_g)
            st.dataframe(df_res_g, use_container_width=True, hide_index=True)

            if (
                len(prueba_g["resultados"]) >= prueba_g["num_catadores"]
                and not prueba_g["completada"]
            ):
                if st.button(
                    "✅ Finalizar Prueba",
                    type="primary",
                    use_container_width=True,
                    key="ab_gancia_finalizar",
                ):
                    prueba_g["completada"] = True
                    st.success(
                        "Prueba finalizada. Ve a la pestaña 'Análisis Competitivo' para ver resultados."
                    )
                    st.rerun()

    # =========================================================
    # TAB 3: ANÁLISIS COMPETITIVO
    # =========================================================
    with tabs[2]:
        if not st.session_state.pruebas_ab_gancia:
            st.info("No hay pruebas realizadas")
            st.stop()

        pruebas_completadas_g = [
            p for p in st.session_state.pruebas_ab_gancia if p.get("completada", False)
        ]

        if not pruebas_completadas_g:
            st.warning("No hay pruebas completadas. Finaliza una prueba primero.")
            st.stop()

        prueba_analizar_g = st.selectbox(
            "Seleccionar prueba para analizar",
            options=[p["id"] for p in pruebas_completadas_g],
            format_func=lambda x: f"{x} - {next((p['fecha'] for p in pruebas_completadas_g if p['id']==x), '')}",
            key="analisis_gancia_select",
        )

        prueba_g = next(
            (p for p in pruebas_completadas_g if p["id"] == prueba_analizar_g), None
        )

        if prueba_g:
            st.subheader(f"Análisis de {prueba_g['id']}")

            col_a1, col_a2 = st.columns(2)

            with col_a1:
                with st.container(border=True):
                    st.write("**📊 Estadísticas Generales**")
                    st.write(f"Total catadores: {len(prueba_g['resultados'])}")

                    if prueba_g["tipo"] == "A/B Simple":
                        preferencias_g = {}
                        for r in prueba_g["resultados"]:
                            pref = r["preferencia"]
                            preferencias_g[pref] = preferencias_g.get(pref, 0) + 1

                        for pref, count in preferencias_g.items():
                            st.metric(
                                f"Prefiere {pref}",
                                f"{count} ({count/len(prueba_g['resultados'])*100:.0f}%)",
                            )

            with col_a2:
                with st.container(border=True):
                    st.write("**📈 Puntajes Promedio**")

                    atributos_prom_g = {}
                    for r in prueba_g["resultados"]:
                        for attr, val in r["puntajes"].items():
                            if attr not in atributos_prom_g:
                                atributos_prom_g[attr] = []
                            atributos_prom_g[attr].append(val)

                    for attr, vals in atributos_prom_g.items():
                        prom = sum(vals) / len(vals)
                        st.metric(attr.capitalize(), f"{prom:.1f}/10")

            st.divider()

            st.subheader("🕸️ Perfil Sensorial Promedio")

            if atributos_prom_g:
                categorias_g = list(atributos_prom_g.keys())
                valores_g = [sum(vals) / len(vals) for vals in atributos_prom_g.values()]

                valores_ref_g = [7.5, 8.0, 7.8, 8.2, 7.5][: len(categorias_g)]

                fig = go.Figure()

                fig.add_trace(
                    go.Scatterpolar(
                        r=valores_g,
                        theta=categorias_g,
                        fill="toself",
                        name="Nuestra Fórmula",
                        line_color="blue",
                    )
                )

                fig.add_trace(
                    go.Scatterpolar(
                        r=valores_ref_g,
                        theta=categorias_g,
                        fill="toself",
                        name=referencias_gancia.get(
                            prueba_g["referencia"], prueba_g["referencia"]
                        ),
                        line_color="red",
                    )
                )

                fig.update_layout(
                    polar=dict(radialaxis=dict(visible=True, range=[0, 10])),
                    showlegend=True,
                    height=500,
                )

                st.plotly_chart(fig, use_container_width=True)

            st.divider()
            st.subheader("📊 Significancia Estadística")

            if prueba_g["tipo"] == "Triangular (2 iguales, 1 diferente)":
                aciertos_g = 0
                for r in prueba_g["resultados"]:
                    if r.get("codigo_diferente") == prueba_g["codigos"][0]:
                        aciertos_g += 1

                total_g = len(prueba_g["resultados"])
                tasa_aciertos_g = aciertos_g / total_g if total_g > 0 else 0

                st.metric("Tasa de aciertos", f"{tasa_aciertos_g:.1%}")

                if tasa_aciertos_g > 0.5:
                    st.success(
                        "✅ Los catadores pueden distinguir nuestra fórmula significativamente"
                    )
                else:
                    st.warning("⚠️ No hay diferencia significativa detectable")

            else:  # A/B Simple
                pref_nuestra_g = sum(
                    1
                    for r in prueba_g["resultados"]
                    if r["preferencia"] == prueba_g["codigos"][0]
                )
                pref_ref_g = sum(
                    1
                    for r in prueba_g["resultados"]
                    if r["preferencia"] == prueba_g["codigos"][1]
                )
                empates_g = sum(
                    1 for r in prueba_g["resultados"] if r["preferencia"] == "Empate"
                )

                total_g = len(prueba_g["resultados"])

                col_s1, col_s2, col_s3 = st.columns(3)

                with col_s1:
                    st.metric(
                        "Prefieren nuestra",
                        f"{pref_nuestra_g} ({pref_nuestra_g/total_g*100:.0f}%)",
                    )
                with col_s2:
                    st.metric(
                        "Prefieren referencia",
                        f"{pref_ref_g} ({pref_ref_g/total_g*100:.0f}%)",
                    )
                with col_s3:
                    st.metric("Empates", f"{empates_g} ({empates_g/total_g*100:.0f}%)")

                if pref_nuestra_g > pref_ref_g:
                    st.success("✅ Nuestra fórmula es preferida sobre la referencia")
                elif pref_ref_g > pref_nuestra_g:
                    st.warning("⚠️ La referencia es preferida sobre nuestra fórmula")
                else:
                    st.info("📊 Empate técnico")

    # =========================================================
    # TAB 4: HISTORIAL
    # =========================================================
    with tabs[3]:
        st.subheader("📋 Historial de Pruebas")

        if not st.session_state.pruebas_ab_gancia:
            st.info("No hay pruebas registradas")
            st.stop()

        data_historial_g = []
        for p in st.session_state.pruebas_ab_gancia:
            data_historial_g.append(
                {
                    "ID": p["id"],
                    "Fecha": p["fecha"],
                    "Tipo": p["tipo"],
                    "Catadores": f"{len(p['resultados'])}/{p['num_catadores']}",
                    "Estado": "✅ Completada" if p.get("completada") else "⏳ En curso",
                    "Referencia": referencias_gancia.get(
                        p["referencia"], p["referencia"]
                    ),
                }
            )

        df_historial_g = pd.DataFrame(data_historial_g)
        st.dataframe(df_historial_g, use_container_width=True, hide_index=True)

        if st.button(
            "🔄 Cargar prueba seleccionada",
            use_container_width=True,
            key="ab_gancia_cargar_hist",
        ):
            st.info("Selecciona una prueba de la tabla para cargarla (doble clic)")

# =========================================================
# MÓDULO DE STOCK
# =========================================================
elif menu == "📦 Stock":
    st.title("📦 Gestión de Stock")
    st.caption("Control de inventario de tinturas y materias primas")

    if not repo:
        st.error("Error: Repositorio no disponible")
        st.stop()

    # Inicializar estado de sesión para movimientos
    if "movimientos_stock" not in st.session_state:
        st.session_state.movimientos_stock = []

    tabs = st.tabs(
        ["📋 Inventario", "📊 Análisis", "📝 Movimientos", "⚙️ Configuración Stock"]
    )

    # =========================================================
    # TAB 1: INVENTARIO
    # =========================================================
    with tabs[0]:
        st.subheader("Inventario Actual de Tinturas")

        # Obtener todas las tinturas
        todas_tinturas = repo.listar()

        if not todas_tinturas:
            st.warning("No hay tinturas registradas")
            st.stop()

        # Filtrar solo tinturas con stock > 0 o que estén en estado lista
        tinturas_con_stock = [
            t
            for t in todas_tinturas
            if t.estado
            and t.estado.value in ["lista", "en_maceracion", "en_estabilizacion"]
        ]

        # Métricas generales
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)

        with col_m1:
            with st.container(border=True):
                total_tinturas = len(tinturas_con_stock)
                st.metric("Total tinturas", total_tinturas)

        with col_m2:
            with st.container(border=True):
                stock_listas = len(
                    [
                        t
                        for t in tinturas_con_stock
                        if t.estado and t.estado.value == "lista"
                    ]
                )
                st.metric("Tinturas listas", stock_listas)

        with col_m3:
            with st.container(border=True):
                volumen_total = sum(t.volumen_disponible_ml for t in tinturas_con_stock)
                st.metric("Volumen total", f"{volumen_total/1000:.2f} L")

        with col_m4:
            with st.container(border=True):
                valor_estimado = volumen_total * 0.5  # Estimado $0.5 por ml
                st.metric("Valor estimado", f"${valor_estimado:.0f}")

        st.divider()

        # Filtros
        from core.tintura_models import Producto, grupos_disponibles_para

        col_f0, col_f1, col_f2, col_f3 = st.columns(4)

        with col_f0:
            filtro_producto_stock = st.selectbox(
                "Filtrar por producto",
                ["Todos"] + [p.value for p in Producto],
                key="stock_filtro_producto",
            )

        with col_f1:
            filtro_estado_stock = st.selectbox(
                "Filtrar por estado",
                ["Todos", "lista", "en_maceracion", "en_estabilizacion"],
                key="stock_filtro_estado",
            )

        with col_f2:
            # Sin key= a propósito (ver el mismo filtro en Listado de
            # Tinturas): con key fija, cambiar filtro_producto_stock dejaba
            # seleccionado un grupo que ya no es válido para el nuevo
            # producto (ej. "citricos" al pasar a Gancia) y el inventario
            # mostraba "sin resultados" en vez de resetear a "Todos".
            filtro_grupo_stock = st.selectbox(
                "Filtrar por grupo",
                ["Todos"] + grupos_disponibles_para(filtro_producto_stock),
            )

        with col_f3:
            busqueda_stock = st.text_input(
                "🔍 Buscar", placeholder="Nombre o ID", key="stock_buscar"
            )

        # Aplicar filtros
        tinturas_filtradas = tinturas_con_stock.copy()

        if filtro_producto_stock != "Todos":
            tinturas_filtradas = [
                t
                for t in tinturas_filtradas
                if t.producto and t.producto.value == filtro_producto_stock
            ]

        if filtro_estado_stock != "Todos":
            tinturas_filtradas = [
                t
                for t in tinturas_filtradas
                if t.estado and t.estado.value == filtro_estado_stock
            ]

        if filtro_grupo_stock != "Todos":
            tinturas_filtradas = [
                t
                for t in tinturas_filtradas
                if t.grupo_funcional and t.grupo_funcional.value == filtro_grupo_stock
            ]

        if busqueda_stock:
            tinturas_filtradas = [
                t
                for t in tinturas_filtradas
                if busqueda_stock.lower() in (t.nombre or "").lower()
                or busqueda_stock in (t.id or "")
            ]

        # Mostrar tabla de inventario
        if tinturas_filtradas:
            data_inventario = []
            for t in tinturas_filtradas:
                # Calcular días restantes si aplica
                dias_restantes = ""
                if (
                    t.fecha_corte_estimada
                    and t.estado
                    and t.estado.value == "en_maceracion"
                ):
                    dias = (t.fecha_corte_estimada - datetime.now()).days
                    dias_restantes = f"{dias} días"
                elif (
                    t.estado
                    and t.estado.value == "en_estabilizacion"
                    and t.fecha_estabilizacion_fin
                ):
                    dias = (t.fecha_estabilizacion_fin - datetime.now()).days
                    dias_restantes = f"{dias} días"

                # Determinar estado de stock
                if t.volumen_disponible_ml == 0:
                    estado_stock = "🔴 Agotado"
                elif t.volumen_disponible_ml < 100:
                    estado_stock = "🟡 Crítico"
                elif t.volumen_disponible_ml < 500:
                    estado_stock = "🟠 Bajo"
                else:
                    estado_stock = "🟢 Normal"

                data_inventario.append(
                    {
                        "ID": t.id,
                        "Nombre": t.nombre,
                        "Producto": t.producto.value if t.producto else "N/A",
                        "Grupo": (
                            t.grupo_funcional.value if t.grupo_funcional else "N/A"
                        ),
                        "Estado": t.estado.value if t.estado else "N/A",
                        "Volumen (ml)": f"{t.volumen_disponible_ml:.0f}",
                        "Stock": estado_stock,
                        "Ubicación": t.ubicacion_almacen or "Sin ubicación",
                        "Días restantes": dias_restantes,
                    }
                )

            df_inventario = pd.DataFrame(data_inventario)

            # Configurar colores para el estado de stock
            def color_estado_stock(val):
                if "🔴" in val:
                    return "background-color: #ffcccc"
                elif "🟡" in val:
                    return "background-color: #fff3cd"
                elif "🟠" in val:
                    return "background-color: #ffe5b4"
                elif "🟢" in val:
                    return "background-color: #d4edda"
                return ""

            st.dataframe(
                df_inventario.style.applymap(color_estado_stock, subset=["Stock"]),
                use_container_width=True,
                hide_index=True,
            )

            # Botón para exportar
            if st.button("📥 Exportar Inventario a CSV", use_container_width=True):
                csv = df_inventario.to_csv(index=False)
                st.download_button(
                    "📥 Descargar CSV",
                    csv,
                    file_name=f"inventario_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv",
                )
        else:
            st.info("No hay tinturas que coincidan con los filtros")

        st.divider()

        # Acciones rápidas sobre stock
        st.subheader("⚡ Acciones Rápidas")

        col_a1, col_a2, col_a3 = st.columns(3)

        with col_a1:
            with st.container(border=True):
                st.write("**Actualizar ubicación**")
                t_sel = st.selectbox(
                    "Seleccionar tintura",
                    options=(
                        [t.id for t in tinturas_filtradas] if tinturas_filtradas else []
                    ),
                    format_func=lambda x: next(
                        (t.nombre for t in tinturas_filtradas if t.id == x), x
                    ),
                    key="stock_sel_ubicacion",
                )
                nueva_ubicacion = st.text_input(
                    "Nueva ubicación", key="stock_nueva_ubic"
                )
                if st.button("📦 Actualizar", key="btn_ubicacion"):
                    if t_sel and nueva_ubicacion:
                        t = repo.get_by_id(t_sel)
                        if t:
                            t.ubicacion_almacen = nueva_ubicacion
                            repo.guardar(t)
                            st.success(f"Ubicación actualizada para {t.nombre}")
                            st.rerun()

        with col_a2:
            with st.container(border=True):
                st.write("**Ajustar volumen**")
                t_sel2 = st.selectbox(
                    "Seleccionar tintura",
                    options=(
                        [t.id for t in tinturas_filtradas] if tinturas_filtradas else []
                    ),
                    format_func=lambda x: next(
                        (t.nombre for t in tinturas_filtradas if t.id == x), x
                    ),
                    key="stock_sel_volumen",
                )
                nuevo_volumen = st.number_input(
                    "Nuevo volumen (ml)",
                    min_value=0,
                    value=0,
                    step=10,
                    key="stock_nuevo_vol",
                )
                if st.button("📊 Actualizar", key="btn_volumen"):
                    if t_sel2 and nuevo_volumen >= 0:
                        t = repo.get_by_id(t_sel2)
                        if t:
                            # Registrar movimiento
                            movimiento = {
                                "fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
                                "tintura": t.nombre,
                                "tipo": "Ajuste manual",
                                "volumen_anterior": t.volumen_disponible_ml,
                                "volumen_nuevo": nuevo_volumen,
                                "diferencia": nuevo_volumen - t.volumen_disponible_ml,
                                "usuario": "Sistema",
                            }
                            st.session_state.movimientos_stock.append(movimiento)

                            t.volumen_disponible_ml = nuevo_volumen
                            repo.guardar(t)
                            st.success(f"Volumen actualizado para {t.nombre}")
                            st.rerun()

        with col_a3:
            with st.container(border=True):
                st.write("**Marcar como agotada**")
                t_sel3 = st.selectbox(
                    "Seleccionar tintura",
                    options=(
                        [
                            t.id
                            for t in tinturas_filtradas
                            if t.volumen_disponible_ml > 0
                        ]
                        if tinturas_filtradas
                        else []
                    ),
                    format_func=lambda x: next(
                        (t.nombre for t in tinturas_filtradas if t.id == x), x
                    ),
                    key="stock_sel_agotar",
                )
                if st.button("⚠️ Marcar agotada", key="btn_agotar"):
                    if t_sel3:
                        t = repo.get_by_id(t_sel3)
                        if t:
                            from core.tintura_models import EstadoTintura

                            t.estado = EstadoTintura.AGOTADA
                            t.volumen_disponible_ml = 0
                            repo.guardar(t)
                            st.success(f"{t.nombre} marcada como agotada")
                            st.rerun()

    # =========================================================
    # TAB 2: ANÁLISIS DE STOCK
    # =========================================================
    with tabs[1]:
        st.subheader("Análisis de Stock")

        todas_tinturas = repo.listar()
        tinturas_con_stock = [
            t
            for t in todas_tinturas
            if t.estado
            and t.estado.value in ["lista", "en_maceracion", "en_estabilizacion"]
        ]

        if not tinturas_con_stock:
            st.info("No hay datos de stock para analizar")
            st.stop()

        col_graf1, col_graf2 = st.columns(2)

        with col_graf1:
            with st.container(border=True):
                st.write("**📊 Distribución por Estado**")

                # Conteo por estado
                estados = {}
                for t in tinturas_con_stock:
                    if t.estado:
                        estado = t.estado.value
                        estados[estado] = estados.get(estado, 0) + 1

                if estados:
                    fig = px.pie(
                        values=list(estados.values()),
                        names=list(estados.keys()),
                        title="Tinturas por Estado",
                        color_discrete_sequence=px.colors.qualitative.Set3,
                    )
                    st.plotly_chart(fig, use_container_width=True)

        with col_graf2:
            with st.container(border=True):
                st.write("**📊 Distribución por Grupo**")

                grupos = {}
                for t in tinturas_con_stock:
                    if t.grupo_funcional:
                        grupo = t.grupo_funcional.value
                        grupos[grupo] = grupos.get(grupo, 0) + 1

                if grupos:
                    fig = px.bar(
                        x=list(grupos.keys()),
                        y=list(grupos.values()),
                        title="Tinturas por Grupo Funcional",
                        color=list(grupos.keys()),
                        color_discrete_sequence=px.colors.qualitative.Set2,
                    )
                    st.plotly_chart(fig, use_container_width=True)

        st.divider()

        # Análisis de volumen por grupo
        st.subheader("📈 Volumen por Grupo Funcional")

        volumen_grupos = {}
        for t in tinturas_con_stock:
            if t.grupo_funcional:
                grupo = t.grupo_funcional.value
                volumen_grupos[grupo] = (
                    volumen_grupos.get(grupo, 0) + t.volumen_disponible_ml
                )

        if volumen_grupos:
            df_volumen = pd.DataFrame(
                {
                    "Grupo": list(volumen_grupos.keys()),
                    "Volumen (ml)": list(volumen_grupos.values()),
                    "Volumen (L)": [v / 1000 for v in volumen_grupos.values()],
                }
            )

            col_v1, col_v2 = st.columns(2)

            with col_v1:
                fig = px.pie(
                    df_volumen,
                    values="Volumen (ml)",
                    names="Grupo",
                    title="Distribución de Volumen por Grupo",
                    color_discrete_sequence=px.colors.qualitative.Set2,
                )
                st.plotly_chart(fig, use_container_width=True)

            with col_v2:
                fig = px.bar(
                    df_volumen,
                    x="Grupo",
                    y="Volumen (L)",
                    title="Volumen en Litros por Grupo",
                    color="Grupo",
                    color_discrete_sequence=px.colors.qualitative.Set2,
                )
                st.plotly_chart(fig, use_container_width=True)

        st.divider()

        # Proyección de consumo
        st.subheader("📉 Proyección de Consumo")

        col_cons1, col_cons2 = st.columns(2)

        with col_cons1:
            consumo_diario = st.slider(
                "Consumo estimado diario (ml/día)",
                min_value=10,
                max_value=500,
                value=100,
                step=10,
                help="Volumen promedio utilizado por día en ensamblajes",
            )

        with col_cons2:
            horizonte = st.selectbox(
                "Horizonte de proyección",
                options=[7, 15, 30, 60, 90],
                format_func=lambda x: f"{x} días",
                index=2,
            )

        if consumo_diario > 0:
            st.write(f"**Proyección a {horizonte} días**")

            data_proyeccion = []
            alertas_bajas = []

            for t in tinturas_con_stock:
                if (
                    t.estado
                    and t.estado.value == "lista"
                    and t.volumen_disponible_ml > 0
                ):
                    dias_disponibles = t.volumen_disponible_ml / consumo_diario

                    estado_proy = "✅ Suficiente"
                    if dias_disponibles < horizonte:
                        estado_proy = "⚠️ Reponer pronto"
                        if dias_disponibles < 7:
                            estado_proy = "🔴 Crítico"
                            alertas_bajas.append(t.nombre)

                    data_proyeccion.append(
                        {
                            "Tintura": t.nombre,
                            "Volumen (ml)": t.volumen_disponible_ml,
                            "Días disponibles": round(dias_disponibles, 1),
                            "Estado": estado_proy,
                        }
                    )

            if data_proyeccion:
                df_proyeccion = pd.DataFrame(data_proyeccion)
                df_proyeccion = df_proyeccion.sort_values("Días disponibles")

                st.dataframe(df_proyeccion, use_container_width=True, hide_index=True)

                # Alertas de stock bajo
                if alertas_bajas:
                    st.warning(
                        f"⚠️ Stock crítico (menos de 7 días): {', '.join(alertas_bajas[:3])}"
                    )

    # =========================================================
    # TAB 3: MOVIMIENTOS
    # =========================================================
    with tabs[2]:
        st.subheader("Registro de Movimientos de Stock")

        col_mov1, col_mov2 = st.columns([2, 1])

        with col_mov1:
            with st.container(border=True):
                st.write("**📝 Nuevo Movimiento**")

                with st.form("form_movimiento", border=True):
                    col_f1, col_f2 = st.columns(2)

                    with col_f1:
                        fecha_mov = st.date_input("Fecha", value=datetime.now())
                        tipo_mov = st.selectbox(
                            "Tipo de movimiento",
                            ["Entrada", "Salida", "Ajuste", "Pérdida", "Transferencia"],
                        )

                    with col_f2:
                        # Obtener tinturas para selector
                        opciones_tinturas_mov = {}
                        for t in todas_tinturas:
                            opciones_tinturas_mov[t.id] = (
                                f"{t.nombre} ({t.volumen_disponible_ml} ml)"
                            )

                        tintura_mov = st.selectbox(
                            "Tintura",
                            options=list(opciones_tinturas_mov.keys()),
                            format_func=lambda x: opciones_tinturas_mov[x],
                        )

                        volumen_mov = st.number_input(
                            "Volumen (ml)", min_value=0.0, value=100.0, step=10.0
                        )

                    motivo_mov = st.text_input(
                        "Motivo / Referencia",
                        placeholder="Ej: Ensamblaje #123, Nuevo lote, etc.",
                    )
                    observaciones_mov = st.text_area("Observaciones", height=100)

                    submitted_mov = st.form_submit_button(
                        "💾 Registrar Movimiento", use_container_width=True
                    )

                    if submitted_mov:
                        t = repo.get_by_id(tintura_mov)
                        if t:
                            # Calcular nuevo volumen según tipo
                            volumen_anterior = t.volumen_disponible_ml
                            if tipo_mov == "Entrada":
                                nuevo_volumen = volumen_anterior + volumen_mov
                            elif tipo_mov in ["Salida", "Pérdida"]:
                                nuevo_volumen = max(0, volumen_anterior - volumen_mov)
                            else:  # Ajuste o Transferencia
                                nuevo_volumen = volumen_mov  # Sobrescribe

                            # Registrar movimiento
                            movimiento = {
                                "fecha": fecha_mov.strftime("%d/%m/%Y"),
                                "hora": datetime.now().strftime("%H:%M"),
                                "tintura": t.nombre,
                                "tipo": tipo_mov,
                                "volumen_anterior": volumen_anterior,
                                "volumen": volumen_mov,
                                "volumen_nuevo": nuevo_volumen,
                                "motivo": motivo_mov,
                                "observaciones": observaciones_mov,
                                "usuario": "Sistema",
                            }
                            st.session_state.movimientos_stock.append(movimiento)

                            # Actualizar stock
                            t.volumen_disponible_ml = nuevo_volumen
                            repo.guardar(t)

                            st.success(
                                f"✅ Movimiento registrado. Nuevo volumen: {nuevo_volumen:.0f} ml"
                            )
                            st.rerun()

        with col_mov2:
            with st.container(border=True):
                st.write("**📊 Resumen de Movimientos**")

                mov_entradas = len(
                    [
                        m
                        for m in st.session_state.movimientos_stock
                        if m["tipo"] == "Entrada"
                    ]
                )
                mov_salidas = len(
                    [
                        m
                        for m in st.session_state.movimientos_stock
                        if m["tipo"] == "Salida"
                    ]
                )
                mov_ajustes = len(
                    [
                        m
                        for m in st.session_state.movimientos_stock
                        if m["tipo"] == "Ajuste"
                    ]
                )

                st.metric("Entradas", mov_entradas)
                st.metric("Salidas", mov_salidas)
                st.metric("Ajustes", mov_ajustes)
                st.metric("Total movimientos", len(st.session_state.movimientos_stock))

        st.divider()

        # Historial de movimientos
        st.subheader("📋 Historial de Movimientos")

        if st.session_state.movimientos_stock:
            # Ordenar por fecha descendente
            movimientos_ordenados = sorted(
                st.session_state.movimientos_stock,
                key=lambda x: x["fecha"] + x.get("hora", ""),
                reverse=True,
            )

            data_mov = []
            for m in movimientos_ordenados[:50]:  # Mostrar últimos 50
                data_mov.append(
                    {
                        "Fecha": f"{m['fecha']} {m.get('hora', '')}",
                        "Tintura": m["tintura"],
                        "Tipo": m["tipo"],
                        "Volumen": f"{m['volumen']:.0f} ml",
                        "Anterior": f"{m['volumen_anterior']:.0f} ml",
                        "Nuevo": f"{m['volumen_nuevo']:.0f} ml",
                        "Motivo": m.get("motivo", "")[:30],
                    }
                )

            df_mov = pd.DataFrame(data_mov)
            st.dataframe(df_mov, use_container_width=True, hide_index=True)

            # Botón para exportar
            if st.button("📥 Exportar Movimientos", use_container_width=True):
                csv = pd.DataFrame(st.session_state.movimientos_stock).to_csv(
                    index=False
                )
                st.download_button(
                    "📥 Descargar CSV",
                    csv,
                    file_name=f"movimientos_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv",
                )
        else:
            st.info("No hay movimientos registrados")

    # =========================================================
    # TAB 4: CONFIGURACIÓN DE STOCK
    # =========================================================
    with tabs[3]:
        st.subheader("⚙️ Configuración de Stock")

        col_conf1, col_conf2 = st.columns(2)

        with col_conf1:
            with st.container(border=True):
                st.write("**📊 Umbrales de Alerta**")

                critico = st.number_input(
                    "Stock crítico (ml)",
                    min_value=0,
                    value=100,
                    step=50,
                    key="umbral_critico",
                )
                bajo = st.number_input(
                    "Stock bajo (ml)",
                    min_value=critico + 1,
                    value=500,
                    step=50,
                    key="umbral_bajo",
                )

                st.caption("Los umbrales se usarán para colorear el inventario")

                if st.button("💾 Guardar umbrales", use_container_width=True):
                    # Guardar en sesión o archivo de configuración
                    st.session_state.umbral_critico = critico
                    st.session_state.umbral_bajo = bajo
                    st.success("Umbrales guardados")

        with col_conf2:
            with st.container(border=True):
                st.write("**📍 Ubicaciones de Almacén**")

                ubicaciones = [
                    "Estante A1",
                    "Estante A2",
                    "Estante B1",
                    "Estante B2",
                    "Cámara 1",
                    "Cámara 2",
                    "Laboratorio",
                ]

                nuevas_ubicaciones = st.multiselect(
                    "Ubicaciones disponibles",
                    options=ubicaciones + ["Agregar nueva..."],
                    default=ubicaciones[:4],
                )

                if "Agregar nueva..." in nuevas_ubicaciones:
                    nueva_ubic = st.text_input("Nueva ubicación")
                    if nueva_ubic and st.button("➕ Agregar"):
                        st.success(f"Ubicación {nueva_ubic} agregada")
                        # Aquí iría la lógica para guardar

        st.divider()

        # Mantenimiento
        st.subheader("🧹 Mantenimiento")

        col_mant1, col_mant2 = st.columns(2)

        with col_mant1:
            if st.button("📊 Recalcular todos los stocks", use_container_width=True):
                with st.spinner("Recalculando..."):
                    # Aquí iría la lógica de recálculo
                    st.success("Stocks recalculados")

        with col_mant2:
            if st.button("📤 Exportar inventario completo", use_container_width=True):
                # Obtener todas las tinturas
                todas = repo.listar()
                data_export = []
                for t in todas:
                    data_export.append(
                        {
                            "ID": t.id,
                            "Nombre": t.nombre,
                            "Producto": t.producto.value if t.producto else "",
                            "Grupo": (
                                t.grupo_funcional.value if t.grupo_funcional else ""
                            ),
                            "Estado": t.estado.value if t.estado else "",
                            "Volumen_inicial_ml": t.volumen_alcohol_ml,
                            "Volumen_disponible_ml": t.volumen_disponible_ml,
                            "Ubicacion": t.ubicacion_almacen,
                            "Fecha_inicio": (
                                t.fecha_inicio.strftime("%Y-%m-%d")
                                if t.fecha_inicio
                                else ""
                            ),
                            "Corte_estimado": (
                                t.fecha_corte_estimada.strftime("%Y-%m-%d")
                                if t.fecha_corte_estimada
                                else ""
                            ),
                        }
                    )

                df_export = pd.DataFrame(data_export)
                csv_export = df_export.to_csv(index=False)

                st.download_button(
                    "📥 Descargar inventario completo",
                    csv_export,
                    file_name=f"inventario_completo_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv",
                )

# =========================================================
# CONFIGURACIÓN
# =========================================================
elif menu == "⚙️ Configuración":
    st.title("⚙️ Configuración del Sistema")
    st.caption("Personaliza los parámetros y preferencias de FernetOS")

    from config.settings import load_settings, save_settings

    # Inicializar configuración en sesión si no existe.
    # parametros/pesos_evaluacion/base_datos se leen de config/settings.yaml
    # (persisten entre reinicios); notificaciones/apariencia son cosméticos y
    # quedan solo en sesión (ver Deferred aspects del spec de robustez).
    if "config_sistema" not in st.session_state:
        _cfg = load_settings()
        st.session_state.config_sistema = {
            "version": "2.0.0",
            "parametros": {
                "abv_min": _cfg.parameters.abv_min,
                "abv_max": _cfg.parameters.abv_max,
                "abv_default": _cfg.parameters.abv_default,
                "azucar_min": _cfg.parameters.azucar_min,
                "azucar_max": _cfg.parameters.azucar_max,
                "azucar_default": _cfg.parameters.azucar_default,
                "ph_min": _cfg.parameters.ph_min,
                "ph_max": _cfg.parameters.ph_max,
                "ph_default": _cfg.parameters.ph_default,
            },
            "pesos_evaluacion": dict(_cfg.sensory.attribute_weights),
            "notificaciones": {
                "sobreextraccion": True,
                "recordatorio_catas": True,
                "stock_bajo": True,
                "corte_proximo": True,
            },
            "apariencia": {
                "tema": "Claro",
                "idioma": "Español",
                "mostrar_metricas": True,
            },
            "base_datos": {
                "auto_backup": _cfg.backup.auto_backup,
                "backup_frecuencia": _cfg.backup.frecuencia,
                "ultimo_backup": _cfg.backup.ultimo_backup,
            },
        }

    # Crear tabs - AHORA CON 7 TABS
    tabs = st.tabs(
        [
            "🎯 Parámetros",
            "⚖️ Pesos Evaluación",
            "🔔 Notificaciones",
            "🎨 Apariencia",
            "💾 Base de Datos",
            "👤 Usuario",
            "📚 Documentación",
        ]
    )

    # =========================================================
    # TAB 0: PARÁMETROS TÉCNICOS
    # =========================================================
    with tabs[0]:
        st.subheader("Parámetros Técnicos por Defecto")
        st.caption("Estos valores se usarán como predeterminados en nuevos blends")

        col_p1, col_p2 = st.columns(2)

        with col_p1:
            with st.container(border=True):
                st.write("**🥃 Parámetros de ABV**")

                abv_min = st.number_input(
                    "ABV mínimo (%)",
                    min_value=30.0,
                    max_value=50.0,
                    value=st.session_state.config_sistema["parametros"]["abv_min"],
                    step=0.5,
                    key="conf_abv_min",
                )

                abv_max = st.number_input(
                    "ABV máximo (%)",
                    min_value=abv_min + 1,
                    max_value=60.0,
                    value=st.session_state.config_sistema["parametros"]["abv_max"],
                    step=0.5,
                    key="conf_abv_max",
                )

                abv_default = st.number_input(
                    "ABV por defecto (%)",
                    min_value=abv_min,
                    max_value=abv_max,
                    value=st.session_state.config_sistema["parametros"]["abv_default"],
                    step=0.5,
                    key="conf_abv_default",
                )

                # Validación
                if abv_default < abv_min or abv_default > abv_max:
                    st.warning(
                        "⚠️ El valor por defecto debe estar entre mínimo y máximo"
                    )

        with col_p2:
            with st.container(border=True):
                st.write("**🍬 Parámetros de Azúcar**")

                azucar_min = st.number_input(
                    "Azúcar mínima (g/L)",
                    min_value=120,
                    max_value=200,
                    value=st.session_state.config_sistema["parametros"]["azucar_min"],
                    step=5,
                    key="conf_azucar_min",
                )

                azucar_max = st.number_input(
                    "Azúcar máxima (g/L)",
                    min_value=azucar_min + 10,
                    max_value=280,
                    value=st.session_state.config_sistema["parametros"]["azucar_max"],
                    step=5,
                    key="conf_azucar_max",
                )

                azucar_default = st.number_input(
                    "Azúcar por defecto (g/L)",
                    min_value=azucar_min,
                    max_value=azucar_max,
                    value=st.session_state.config_sistema["parametros"][
                        "azucar_default"
                    ],
                    step=5,
                    key="conf_azucar_default",
                )

        st.divider()

        with st.container(border=True):
            st.write("**🧪 Parámetros de pH**")

            col_ph1, col_ph2, col_ph3 = st.columns(3)

            with col_ph1:
                ph_min = st.number_input(
                    "pH mínimo",
                    min_value=3.0,
                    max_value=7.0,
                    value=st.session_state.config_sistema["parametros"]["ph_min"],
                    step=0.1,
                    format="%.1f",
                    key="conf_ph_min",
                )

            with col_ph2:
                ph_max = st.number_input(
                    "pH máximo",
                    min_value=ph_min + 0.1,
                    max_value=8.0,
                    value=st.session_state.config_sistema["parametros"]["ph_max"],
                    step=0.1,
                    format="%.1f",
                    key="conf_ph_max",
                )

            with col_ph3:
                ph_default = st.number_input(
                    "pH por defecto",
                    min_value=ph_min,
                    max_value=ph_max,
                    value=st.session_state.config_sistema["parametros"]["ph_default"],
                    step=0.1,
                    format="%.1f",
                    key="conf_ph_default",
                )

        st.divider()

        # Botón para guardar
        if st.button("💾 Guardar Parámetros", type="primary", use_container_width=True):
            st.session_state.config_sistema["parametros"] = {
                "abv_min": abv_min,
                "abv_max": abv_max,
                "abv_default": abv_default,
                "azucar_min": azucar_min,
                "azucar_max": azucar_max,
                "azucar_default": azucar_default,
                "ph_min": ph_min,
                "ph_max": ph_max,
                "ph_default": ph_default,
            }
            _cfg = load_settings()
            _cfg.parameters.abv_min = abv_min
            _cfg.parameters.abv_max = abv_max
            _cfg.parameters.abv_default = abv_default
            _cfg.parameters.azucar_min = azucar_min
            _cfg.parameters.azucar_max = azucar_max
            _cfg.parameters.azucar_default = azucar_default
            _cfg.parameters.ph_min = ph_min
            _cfg.parameters.ph_max = ph_max
            _cfg.parameters.ph_default = ph_default
            save_settings(_cfg)
            st.success("✅ Parámetros guardados correctamente")
            st.balloons()

    # =========================================================
    # TAB 1: PESOS DE EVALUACIÓN
    # =========================================================
    with tabs[1]:
        st.subheader("Pesos para Evaluación Sensorial")
        st.caption("Define la importancia de cada atributo en el puntaje total")

        st.info(
            """
        Los pesos determinan cómo se calcula el puntaje total de una evaluación.
        La suma de todos los pesos debe ser 1.0 (100%).
        """
        )

        with st.container(border=True):
            col_w1, col_w2 = st.columns(2)

            with col_w1:
                peso_ataque = st.slider(
                    "⚡ Ataque",
                    0.0,
                    1.0,
                    st.session_state.config_sistema["pesos_evaluacion"]["ataque"],
                    0.05,
                    key="peso_ataque",
                    help="Impacto inicial en los primeros 3 segundos",
                )

                peso_complejidad = st.slider(
                    "🔄 Complejidad",
                    0.0,
                    1.0,
                    st.session_state.config_sistema["pesos_evaluacion"]["complejidad"],
                    0.05,
                    key="peso_complejidad",
                    help="Variedad de notas y capas de sabor",
                )

                peso_equilibrio = st.slider(
                    "⚖️ Equilibrio",
                    0.0,
                    1.0,
                    st.session_state.config_sistema["pesos_evaluacion"]["equilibrio"],
                    0.05,
                    key="peso_equilibrio",
                    help="Balance general entre todos los componentes",
                )

            with col_w2:
                peso_persistencia = st.slider(
                    "⏱️ Persistencia",
                    0.0,
                    1.0,
                    st.session_state.config_sistema["pesos_evaluacion"]["persistencia"],
                    0.05,
                    key="peso_persistencia",
                    help="Duración del sabor post-deglución",
                )

                peso_amargor = st.slider(
                    "😖 Amargor",
                    0.0,
                    1.0,
                    st.session_state.config_sistema["pesos_evaluacion"]["amargor"],
                    0.05,
                    key="peso_amargor",
                    help="Intensidad y calidad del amargor",
                )

        # Calcular total
        total_pesos = (
            peso_ataque
            + peso_complejidad
            + peso_equilibrio
            + peso_persistencia
            + peso_amargor
        )

        col_total1, col_total2 = st.columns(2)

        with col_total1:
            st.metric("Total pesos", f"{total_pesos:.2f}")

        with col_total2:
            if abs(total_pesos - 1.0) < 0.01:
                st.success("✅ Los pesos suman 1.0 - Correcto")
            else:
                st.error(f"❌ Los pesos deben sumar 1.0 (actual: {total_pesos:.2f})")

        # Botón para guardar
        if st.button("💾 Guardar Pesos", type="primary", use_container_width=True):
            if abs(total_pesos - 1.0) < 0.01:
                pesos = {
                    "ataque": peso_ataque,
                    "complejidad": peso_complejidad,
                    "equilibrio": peso_equilibrio,
                    "persistencia": peso_persistencia,
                    "amargor": peso_amargor,
                }
                st.session_state.config_sistema["pesos_evaluacion"] = pesos
                _cfg = load_settings()
                _cfg.sensory.attribute_weights = pesos
                save_settings(_cfg)
                st.success("✅ Pesos guardados correctamente")
            else:
                st.error("❌ No se pueden guardar pesos que no sumen 1.0")

    # =========================================================
    # TAB 2: NOTIFICACIONES
    # =========================================================
    with tabs[2]:
        st.subheader("Configuración de Notificaciones")
        st.caption("Personaliza las alertas que recibirás del sistema")

        with st.container(border=True):
            st.write("**🔔 Tipos de Notificaciones**")

            col_n1, col_n2 = st.columns(2)

            with col_n1:
                notif_sobreextraccion = st.checkbox(
                    "Alertas de sobreextracción",
                    value=st.session_state.config_sistema["notificaciones"][
                        "sobreextraccion"
                    ],
                    key="notif_sobre",
                    help="Te alertará cuando una tintura supere el punto óptimo",
                )

                notif_recordatorio = st.checkbox(
                    "Recordatorio de catas",
                    value=st.session_state.config_sistema["notificaciones"][
                        "recordatorio_catas"
                    ],
                    key="notif_catas",
                    help="Te recordará registrar catas cada 48h",
                )

            with col_n2:
                notif_stock = st.checkbox(
                    "Stock bajo",
                    value=st.session_state.config_sistema["notificaciones"][
                        "stock_bajo"
                    ],
                    key="notif_stock",
                    help="Te alertará cuando una tintura tenga stock crítico",
                )

                notif_corte = st.checkbox(
                    "Corte próximo",
                    value=st.session_state.config_sistema["notificaciones"][
                        "corte_proximo"
                    ],
                    key="notif_corte",
                    help="Te avisará cuando una maceración esté cerca del punto de corte",
                )

        st.divider()

        with st.container(border=True):
            st.write("**⏰ Frecuencia de Notificaciones**")

            frecuencia = st.radio(
                "¿Con qué frecuencia quieres recibir notificaciones?",
                [
                    "Inmediatamente",
                    "Resumen diario",
                    "Resumen semanal",
                    "Solo en el dashboard",
                ],
                index=0,
                key="frec_notif",
            )

            horario = st.time_input(
                "Horario de notificaciones (para resúmenes)",
                value=datetime.strptime("09:00", "%H:%M").time(),
                key="hora_notif",
            )

        # Botón para guardar
        if st.button(
            "💾 Guardar Notificaciones", type="primary", use_container_width=True
        ):
            st.session_state.config_sistema["notificaciones"] = {
                "sobreextraccion": notif_sobreextraccion,
                "recordatorio_catas": notif_recordatorio,
                "stock_bajo": notif_stock,
                "corte_proximo": notif_corte,
                "frecuencia": frecuencia,
                "horario": str(horario),
            }
            st.success("✅ Configuración de notificaciones guardada")

    # =========================================================
    # TAB 3: APARIENCIA
    # =========================================================
    with tabs[3]:
        st.subheader("Configuración de Apariencia")
        st.caption("Personaliza la interfaz del sistema")

        with st.container(border=True):
            col_a1, col_a2 = st.columns(2)

            with col_a1:
                tema = st.selectbox(
                    "🎨 Tema de color",
                    ["Claro", "Oscuro", "Sistema", "Alto contraste"],
                    index=["Claro", "Oscuro", "Sistema", "Alto contraste"].index(
                        st.session_state.config_sistema["apariencia"]["tema"]
                    ),
                    key="tema_select",
                )

                idioma = st.selectbox(
                    "🌐 Idioma",
                    ["Español", "English", "Português", "Italiano"],
                    index=["Español", "English", "Português", "Italiano"].index(
                        st.session_state.config_sistema["apariencia"]["idioma"]
                    ),
                    key="idioma_select",
                )

            with col_a2:
                mostrar_metricas = st.checkbox(
                    "Mostrar métricas en dashboard",
                    value=st.session_state.config_sistema["apariencia"][
                        "mostrar_metricas"
                    ],
                    key="show_metrics",
                )

                compacto = st.checkbox(
                    "Modo compacto",
                    value=False,
                    key="modo_compacto",
                    help="Reduce el espaciado para mostrar más información",
                )

        st.divider()

        with st.container(border=True):
            st.write("**📊 Configuración de Gráficos**")

            col_g1, col_g2 = st.columns(2)

            with col_g1:
                grafico_tema = st.selectbox(
                    "Tema de gráficos",
                    ["plotly", "plotly_white", "plotly_dark", "ggplot2", "seaborn"],
                    index=0,
                    key="graf_tema",
                )

                mostrar_grid = st.checkbox(
                    "Mostrar cuadrícula en gráficos", value=True, key="graf_grid"
                )

            with col_g2:
                ancho_graficos = st.select_slider(
                    "Ancho de gráficos",
                    options=["Pequeño", "Mediano", "Grande", "Completo"],
                    value="Grande",
                    key="graf_ancho",
                )

        # Botón para guardar
        if st.button("💾 Guardar Apariencia", type="primary", use_container_width=True):
            st.session_state.config_sistema["apariencia"] = {
                "tema": tema,
                "idioma": idioma,
                "mostrar_metricas": mostrar_metricas,
                "compacto": compacto,
                "grafico_tema": grafico_tema,
                "mostrar_grid": mostrar_grid,
                "ancho_graficos": ancho_graficos,
            }
            st.success("✅ Configuración de apariencia guardada")
            st.info("ℹ️ Algunos cambios requieren reiniciar la aplicación")

    # =========================================================
    # TAB 4: BASE DE DATOS
    # =========================================================
    with tabs[4]:
        st.subheader("Configuración de Base de Datos")

        if db:
            db_path = db.db_path if hasattr(db, "db_path") else "data/fernetos.db"
            db_size = os.path.getsize(db_path) / 1024 if os.path.exists(db_path) else 0
            db_size_mb = db_size / 1024

            col_db1, col_db2 = st.columns(2)

            with col_db1:
                with st.container(border=True):
                    st.write("**📊 Información de la Base de Datos**")
                    st.write(f"**Ubicación:** `{db_path}`")
                    st.write(f"**Tamaño:** {db_size:.1f} KB ({db_size_mb:.2f} MB)")

                    # Contar registros
                    with db.get_connection() as conn:
                        cursor = conn.execute("SELECT COUNT(*) FROM tinturas")
                        total_tinturas = cursor.fetchone()[0]

                        cursor = conn.execute("SELECT COUNT(*) FROM registros_curva")
                        total_registros = cursor.fetchone()[0]

                    st.write(f"**Tinturas:** {total_tinturas}")
                    st.write(f"**Registros de curva:** {total_registros}")

            with col_db2:
                with st.container(border=True):
                    st.write("**⚙️ Opciones de Backup**")

                    auto_backup = st.checkbox(
                        "Realizar backup automático",
                        value=st.session_state.config_sistema["base_datos"][
                            "auto_backup"
                        ],
                        key="db_auto_backup",
                    )

                    if auto_backup:
                        backup_frecuencia = st.selectbox(
                            "Frecuencia de backup",
                            ["diario", "semanal", "mensual"],
                            index=["diario", "semanal", "mensual"].index(
                                st.session_state.config_sistema["base_datos"].get(
                                    "backup_frecuencia", "semanal"
                                )
                            ),
                            key="db_frecuencia",
                        )

                        backup_hora = st.time_input(
                            "Hora del backup",
                            value=datetime.strptime("03:00", "%H:%M").time(),
                            key="db_hora",
                        )
                    else:
                        backup_frecuencia = st.session_state.config_sistema[
                            "base_datos"
                        ].get("backup_frecuencia", "semanal")

                    if st.button("💾 Guardar Configuración de Backup"):
                        st.session_state.config_sistema["base_datos"][
                            "auto_backup"
                        ] = auto_backup
                        st.session_state.config_sistema["base_datos"][
                            "backup_frecuencia"
                        ] = backup_frecuencia
                        _cfg = load_settings()
                        _cfg.backup.auto_backup = auto_backup
                        _cfg.backup.frecuencia = backup_frecuencia
                        save_settings(_cfg)
                        st.success("✅ Configuración de backup guardada")

            st.divider()

            # Acciones
            st.subheader("🛠️ Acciones de Mantenimiento")

            col_act1, col_act2, col_act3 = st.columns(3)

            with col_act1:
                if st.button("📥 Hacer Backup Ahora", use_container_width=True):
                    backup_path = db_path.replace(
                        ".db", f'_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
                    )
                    import shutil

                    shutil.copy2(db_path, backup_path)

                    # Registrar en configuración (sesión + disco, para que el
                    # chequeo de backup automático al iniciar la app sepa
                    # cuándo fue el último backup real)
                    ahora = datetime.now().strftime("%d/%m/%Y %H:%M")
                    st.session_state.config_sistema["base_datos"][
                        "ultimo_backup"
                    ] = ahora
                    _cfg = load_settings()
                    _cfg.backup.ultimo_backup = ahora
                    save_settings(_cfg)

                    st.success(f"✅ Backup creado: {backup_path}")

                    # Ofrecer descarga
                    with open(backup_path, "rb") as f:
                        st.download_button(
                            "📥 Descargar Backup",
                            f,
                            file_name=os.path.basename(backup_path),
                            mime="application/octet-stream",
                        )

            with col_act2:
                if st.button("🔍 Verificar Integridad", use_container_width=True):
                    with st.spinner("Verificando integridad de la base de datos..."):
                        try:
                            with db.get_connection() as conn:
                                conn.execute("PRAGMA integrity_check")
                            st.success("✅ Base de datos íntegra - sin errores")
                        except Exception as e:
                            st.error(f"❌ Error en base de datos: {e}")

            with col_act3:
                if st.button("🧹 Optimizar Base de Datos", use_container_width=True):
                    with st.spinner("Optimizando base de datos..."):
                        try:
                            with db.get_connection() as conn:
                                conn.execute("VACUUM")
                            st.success("✅ Base de datos optimizada")

                            # Actualizar tamaño
                            new_size = os.path.getsize(db_path) / 1024
                            st.info(
                                f"Tamaño anterior: {db_size:.1f} KB → Nuevo tamaño: {new_size:.1f} KB"
                            )
                        except Exception as e:
                            st.error(f"Error optimizando: {e}")

            st.divider()

            # Restaurar backup
            with st.expander("🔄 Restaurar Backup"):
                st.warning("⚠️ Esta acción sobrescribirá la base de datos actual")

                archivos_backup = [
                    f
                    for f in os.listdir("data")
                    if f.startswith("fernetos_backup_") and f.endswith(".db")
                ]

                if archivos_backup:
                    backup_seleccionado = st.selectbox(
                        "Seleccionar backup", archivos_backup, key="restore_select"
                    )

                    if st.button(
                        "⚠️ Restaurar Backup", type="secondary", use_container_width=True
                    ):
                        if st.checkbox("Confirmar que quiero restaurar este backup"):
                            backup_full = os.path.join("data", backup_seleccionado)
                            shutil.copy2(backup_full, db_path)
                            st.success(
                                f"✅ Base de datos restaurada desde {backup_seleccionado}"
                            )
                            st.info(
                                "🔄 Reinicia la aplicación para aplicar los cambios"
                            )
                else:
                    st.info("No hay archivos de backup disponibles")
        else:
            st.error("No se pudo acceder a la base de datos")

    # =========================================================
    # TAB 5: USUARIO
    # =========================================================
    with tabs[5]:
        st.subheader("Configuración de Usuario")

        col_u1, col_u2 = st.columns(2)

        with col_u1:
            with st.container(border=True):
                st.write("**👤 Datos Personales**")

                nombre_usuario = st.text_input(
                    "Nombre", value="Master Blender", key="user_nombre"
                )

                email_usuario = st.text_input(
                    "Email", value="blender@fernetos.com", key="user_email"
                )

                rol_usuario = st.selectbox(
                    "Rol",
                    [
                        "Master Blender",
                        "Asistente de Laboratorio",
                        "Catador",
                        "Visitante",
                        "Administrador",
                    ],
                    index=0,
                    key="user_rol",
                )

        with col_u2:
            with st.container(border=True):
                st.write("**🔐 Preferencias de Seguridad**")

                cambiar_password = st.checkbox("Cambiar contraseña", key="cambiar_pass")

                if cambiar_password:
                    pass_actual = st.text_input(
                        "Contraseña actual", type="password", key="pass_actual"
                    )
                    pass_nueva = st.text_input(
                        "Nueva contraseña", type="password", key="pass_nueva"
                    )
                    pass_confirmar = st.text_input(
                        "Confirmar contraseña", type="password", key="pass_confirmar"
                    )

                    if pass_nueva and pass_confirmar and pass_nueva != pass_confirmar:
                        st.warning("⚠️ Las contraseñas no coinciden")

                autoguardado = st.checkbox(
                    "Guardar sesión automáticamente", value=True, key="autosave"
                )

        st.divider()

        with st.container(border=True):
            st.write("**📊 Preferencias del Dashboard**")

            col_d1, col_d2 = st.columns(2)

            with col_d1:
                dashboard_metricas = st.multiselect(
                    "Métricas a mostrar en dashboard",
                    [
                        "Tinturas Activas",
                        "Tinturas Listas",
                        "Ensayos",
                        "Blends Históricos",
                        "Stock Total",
                        "Pruebas A/B",
                    ],
                    default=["Tinturas Activas", "Tinturas Listas", "Stock Total"],
                    key="dashboard_metrics",
                )

                dashboard_periodo = st.selectbox(
                    "Período por defecto en gráficos",
                    ["7 días", "14 días", "30 días", "90 días"],
                    index=1,
                    key="dashboard_periodo",
                )

            with col_d2:
                dashboard_orden = st.radio(
                    "Orden de módulos en sidebar",
                    ["Predeterminado", "Personalizado", "Más usados"],
                    index=0,
                    key="dashboard_orden",
                )

        st.divider()

        # Botones de acción
        col_b1, col_b2, col_b3 = st.columns(3)

        with col_b1:
            if st.button("💾 Guardar Perfil", type="primary", use_container_width=True):
                st.success("✅ Perfil actualizado correctamente")
                st.balloons()

        with col_b2:
            if st.button("📤 Exportar Configuración", use_container_width=True):
                # Crear archivo de configuración
                config_export = st.session_state.config_sistema.copy()
                config_export["usuario"] = {
                    "nombre": nombre_usuario,
                    "email": email_usuario,
                    "rol": rol_usuario,
                    "dashboard_metricas": dashboard_metricas,
                    "dashboard_periodo": dashboard_periodo,
                }

                import json

                config_json = json.dumps(config_export, indent=2, default=str)

                st.download_button(
                    "📥 Descargar Configuración",
                    config_json,
                    file_name=f"fernetos_config_{datetime.now().strftime('%Y%m%d')}.json",
                    mime="application/json",
                )

        with col_b3:
            if st.button("🔄 Resetear Configuración", use_container_width=True):
                if st.checkbox("Confirmar reset a valores por defecto"):
                    # Resetear a valores por defecto
                    st.session_state.config_sistema = {
                        "version": "2.0.0",
                        "parametros": {
                            "abv_min": 38.0,
                            "abv_max": 42.0,
                            "abv_default": 40.0,
                            "azucar_min": 160,
                            "azucar_max": 220,
                            "azucar_default": 195,
                            "ph_min": 4.8,
                            "ph_max": 5.6,
                            "ph_default": 5.2,
                        },
                        "pesos_evaluacion": {
                            "ataque": 0.20,
                            "complejidad": 0.20,
                            "equilibrio": 0.25,
                            "persistencia": 0.20,
                            "amargor": 0.15,
                        },
                        "notificaciones": {
                            "sobreextraccion": True,
                            "recordatorio_catas": True,
                            "stock_bajo": True,
                            "corte_proximo": True,
                        },
                        "apariencia": {
                            "tema": "Claro",
                            "idioma": "Español",
                            "mostrar_metricas": True,
                        },
                        "base_datos": {
                            "auto_backup": True,
                            "backup_frecuencia": "semanal",
                            "ultimo_backup": None,
                        },
                    }
                    st.success("✅ Configuración reseteada a valores por defecto")
                    st.rerun()

    # =========================================================
    # TAB 6: DOCUMENTACIÓN
    # =========================================================
    with tabs[6]:
        # Importar módulos necesarios
        import glob
        import os
        from datetime import datetime

        st.subheader("📚 Documentación del Sistema")

        col_doc1, col_doc2 = st.columns(2)

        with col_doc1:
            with st.container(border=True):
                st.write("**📖 Manual de Usuario**")
                st.write(
                    "Genera el manual completo en PDF con toda la documentación del sistema."
                )

                if st.button("📥 Generar Manual PDF", use_container_width=True):
                    with st.spinner(
                        "Generando manual... (esto puede tomar unos segundos)"
                    ):
                        import subprocess
                        import sys

                        try:
                            # Obtener la ruta absoluta al script
                            script_dir = os.path.dirname(os.path.abspath(__file__))
                            script_path = os.path.join(
                                script_dir, "scripts", "generar_manual_pdf.py"
                            )

                            # Verificar que el script existe
                            if not os.path.exists(script_path):
                                st.error(f"❌ Script no encontrado en: {script_path}")
                                st.info(
                                    "Verifica que el archivo existe en la carpeta 'scripts/'"
                                )
                            else:
                                # Ejecutar el script de generación de PDF
                                result = subprocess.run(
                                    [sys.executable, script_path],
                                    capture_output=True,
                                    text=True,
                                    cwd=os.path.dirname(script_dir),
                                )

                                if result.returncode == 0:
                                    # Buscar el PDF generado más reciente
                                    pdf_files = glob.glob(
                                        "outputs/manuals/manual_fernetos_*.pdf"
                                    )
                                    if pdf_files:
                                        latest_pdf = max(
                                            pdf_files, key=os.path.getctime
                                        )

                                        with open(latest_pdf, "rb") as f:
                                            st.download_button(
                                                "📥 Descargar Manual PDF",
                                                f,
                                                file_name=os.path.basename(latest_pdf),
                                                mime="application/pdf",
                                                use_container_width=True,
                                            )
                                        st.success(
                                            f"✅ Manual generado: {os.path.basename(latest_pdf)}"
                                        )

                                        file_size = os.path.getsize(latest_pdf) / 1024
                                        st.info(f"📊 Tamaño: {file_size:.1f} KB")
                                    else:
                                        st.warning(
                                            "PDF generado pero no encontrado en outputs/manuals/"
                                        )

                                    with st.expander("Ver salida del script"):
                                        st.text(result.stdout)
                                        if result.stderr:
                                            st.error(result.stderr)
                                else:
                                    st.error(
                                        f"❌ Error generando manual (código: {result.returncode})"
                                    )
                                    with st.expander("Ver detalles del error"):
                                        st.text(result.stdout)
                                        st.error(result.stderr)
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")
                            import traceback

                            st.code(traceback.format_exc())

        with col_doc2:
            with st.container(border=True):
                st.write("**📋 Versiones Anteriores**")

                pdf_files = glob.glob("outputs/manuals/manual_fernetos_*.pdf")

                if pdf_files:
                    for pdf in sorted(pdf_files, reverse=True)[:5]:
                        file_name = os.path.basename(pdf)
                        file_size = os.path.getsize(pdf) / 1024
                        mod_time = datetime.fromtimestamp(os.path.getmtime(pdf))

                        with st.container():
                            st.write(f"**{file_name}**")
                            st.caption(
                                f"📅 {mod_time.strftime('%d/%m/%Y %H:%M')} | 📊 {file_size:.1f} KB"
                            )

                            with open(pdf, "rb") as f:
                                st.download_button(
                                    f"📥 Descargar",
                                    f,
                                    file_name=file_name,
                                    mime="application/pdf",
                                    key=f"dl_{pdf}",
                                    use_container_width=True,
                                )
                else:
                    st.info("No hay manuales generados aún")

        st.divider()

        # Scripts disponibles
        st.subheader("🔧 Scripts del Sistema")

        # Obtener la ruta base del proyecto (directorio que contiene app.py)
        base_dir = os.path.dirname(os.path.abspath(__file__))

        # Mostrar la ruta base para debugging (opcional)
        with st.expander("📁 Ver rutas del sistema"):
            st.write(f"**Directorio base:** `{base_dir}`")
            st.write(f"**Archivo actual:** `{__file__}`")

        scripts = [
            (
                "inicializar_bd_fernet.py",
                "Inicializa la base de datos con tinturas de ejemplo",
            ),
            ("check_db.py", "Verifica el estado de la base de datos"),
            ("scripts/generar_manual_pdf.py", "Genera el manual de usuario en PDF"),
        ]

        for script, desc in scripts:
            with st.container(border=True):
                col_s1, col_s2 = st.columns([3, 1])
                with col_s1:
                    st.write(f"**{script}**")
                    st.caption(desc)
                with col_s2:
                    # Construir ruta absoluta correcta
                    script_path = os.path.join(base_dir, script)

                    if os.path.exists(script_path):
                        # CORREGIDO: st.success es una función, necesita paréntesis
                        st.success("✅ Disponible")
                        if st.button(
                            f"▶️ Ejecutar", key=f"run_{script}", use_container_width=True
                        ):
                            with st.spinner(f"Ejecutando {script}..."):
                                try:
                                    import subprocess

                                    result = subprocess.run(
                                        [sys.executable, script_path],
                                        capture_output=True,
                                        text=True,
                                        cwd=base_dir,
                                    )

                                    if result.returncode == 0:
                                        st.success("✅ Ejecutado correctamente")
                                    else:
                                        st.error(
                                            f"❌ Error (código: {result.returncode})"
                                        )

                                    with st.expander("Ver salida"):
                                        st.text(result.stdout)
                                        if result.stderr:
                                            st.error(result.stderr)
                                except Exception as e:
                                    st.error(f"Error: {str(e)}")
                    else:
                        st.error(f"❌ No encontrado")
                        st.caption(f"Buscado en: `{script_path}`")

# =========================================================
# MÓDULO DE TORNEO (cata a ciegas)
# =========================================================
elif menu == "🏆 Torneo":
    st.title("🏆 Torneo")

    from core.validators import FAMILIAS_COMPATIBLES_VALIDAS
    from evaluation.blind_coding import orden_cata_para_jurado
    from evaluation.cierre_ronda import cerrar_ronda_categoria
    from evaluation.historico import historico_productor, historico_receta
    from evaluation.models import Categoria, Evento, Jurado, Muestra, Puntaje, RolJurado, SubModalidad
    from evaluation.progreso import calcular_progreso_categoria
    from evaluation.reportes import generar_ficha_cata_muestra, generar_planilla_resultados_categoria
    from evaluation.repository import (
        CategoriaRepository,
        EventoRepository,
        JuradoRepository,
        MuestraRepository,
        PuntajeRepository,
        RankingRepository,
    )

    evento_repo = EventoRepository(db)
    categoria_repo = CategoriaRepository(db)
    jurado_repo = JuradoRepository(db)
    muestra_repo = MuestraRepository(db)
    puntaje_repo = PuntajeRepository(db)
    ranking_repo = RankingRepository(db)

    def _nombre_categoria(categoria):
        return f"{categoria.familia} ({categoria.submodalidad.value})"

    @st.cache_data(show_spinner=False)
    def _pdf_planilla_resultados(categoria, muestras, ranking):
        # Cacheado por contenido (categoria/muestras/ranking no cambian
        # hasta que se recalcula la ronda): sin esto, Streamlit reconstruye
        # el PDF en cada rerun de la app entera, no solo cuando esta tab
        # esta a la vista (todas las tabs ejecutan su cuerpo en cada rerun).
        return generar_planilla_resultados_categoria(categoria, muestras, ranking)

    @st.cache_data(show_spinner=False)
    def _pdf_ficha_cata(muestra, puntajes, jurados_, puntaje_final):
        return generar_ficha_cata_muestra(muestra, puntajes, jurados_, puntaje_final)

    def _form_crear_evento(key_suffix):
        with st.form(f"torneo_nuevo_evento_{key_suffix}"):
            nombre = st.text_input("Nombre*", key=f"torneo_evento_nombre_{key_suffix}")
            fecha = st.date_input("Fecha*", key=f"torneo_evento_fecha_{key_suffix}")
            sede = st.text_input("Sede*", key=f"torneo_evento_sede_{key_suffix}")
            edicion_numero = st.number_input(
                "Número de edición*",
                min_value=1,
                step=1,
                value=1,
                key=f"torneo_evento_edicion_{key_suffix}",
            )
            if st.form_submit_button("Crear evento"):
                if not nombre or not sede:
                    st.error("Completá nombre y sede.")
                else:
                    try:
                        evento = Evento(
                            nombre=nombre,
                            fecha=fecha.strftime("%Y-%m-%d"),
                            sede=sede,
                            edicion_numero=int(edicion_numero),
                        )
                        evento_repo.guardar(evento)
                        st.session_state["torneo_evento_id"] = evento.id
                        st.success(f"✅ Evento creado: {evento.nombre}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error creando evento: {e}")

    # EventoRepository.listar() ordena por rowid (orden de creacion), asi
    # que eventos[-1] es siempre el evento creado mas recientemente.
    eventos = evento_repo.listar()

    if not eventos:
        st.info("Todavía no hay ningún evento cargado. Creá el primero para empezar.")
        _form_crear_evento("inicial")
    else:
        opciones_evento = {
            e.id: f"{e.nombre} (ed. {e.edicion_numero}, {e.fecha})" for e in eventos
        }
        ids_evento = list(opciones_evento.keys())
        evento_id_default = st.session_state.get("torneo_evento_id", eventos[-1].id)
        if evento_id_default not in opciones_evento:
            evento_id_default = eventos[-1].id

        evento_id = st.selectbox(
            "Evento activo",
            options=ids_evento,
            format_func=lambda eid: opciones_evento[eid],
            index=ids_evento.index(evento_id_default),
        )
        st.session_state["torneo_evento_id"] = evento_id

        # Las categorias de las tabs de abajo estan scopeadas al evento
        # activo; si el evento cambio, las selecciones de categoria
        # guardadas en session_state pueden apuntar a un id que ya no esta
        # en las opciones. Sin este reset explicito, Streamlit las
        # descarta en silencio y cae al primer item de la lista nueva -
        # correcto pero facil de no notar. Limpiarlas hace el reset
        # explicito en vez de depender de ese fallback implicito.
        if st.session_state.get("torneo_ultimo_evento_visto") != evento_id:
            for key in (
                "torneo_categoria_activa",
                "torneo_categoria_muestra",
                "torneo_categoria_progreso",
                "torneo_categoria_resultados",
            ):
                st.session_state.pop(key, None)
            st.session_state["torneo_ultimo_evento_visto"] = evento_id

        with st.expander("➕ Crear nuevo evento"):
            _form_crear_evento("nuevo")

        st.divider()

        categorias = categoria_repo.listar(evento_id=evento_id)
        jurados = jurado_repo.listar()

        tab_config, tab_puntaje, tab_progreso, tab_resultados, tab_productor = st.tabs(
            [
                "⚙️ Configuración",
                "📝 Cargar puntaje",
                "📊 Progreso en vivo",
                "🏅 Resultados",
                "👤 Panel de productor",
            ]
        )

        # TAB CONFIGURACIÓN
        with tab_config:
            st.subheader("Categorías")
            if categorias:
                st.dataframe(
                    pd.DataFrame(
                        [
                            {
                                "ID": c.id,
                                "Familia": c.familia,
                                "Submodalidad": c.submodalidad.value,
                            }
                            for c in categorias
                        ]
                    ),
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.info("Este evento todavía no tiene categorías.")

            with st.form("torneo_nueva_categoria"):
                familia = st.selectbox("Familia*", sorted(FAMILIAS_COMPATIBLES_VALIDAS))
                submodalidad = st.selectbox(
                    "Submodalidad*", [s.value for s in SubModalidad]
                )
                if st.form_submit_button("Crear categoría"):
                    try:
                        categoria = Categoria(
                            evento_id=evento_id,
                            familia=familia,
                            submodalidad=SubModalidad(submodalidad),
                        )
                        categoria_repo.guardar(categoria)
                        st.success(f"✅ Categoría creada: {_nombre_categoria(categoria)}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error creando categoría: {e}")

            st.divider()
            st.subheader("Jurados")
            if jurados:
                st.dataframe(
                    pd.DataFrame(
                        [
                            {
                                "ID": j.id,
                                "Nombre": j.nombre,
                                "Rol": j.rol.value,
                                "Peso de voto": j.peso_voto,
                            }
                            for j in jurados
                        ]
                    ),
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.info("Todavía no hay jurados cargados.")

            with st.form("torneo_nuevo_jurado"):
                nombre_jurado = st.text_input("Nombre*")
                rol_jurado = st.selectbox("Rol*", [r.value for r in RolJurado])
                peso_voto = st.number_input(
                    "Peso de voto*", min_value=0.01, value=1.0, step=0.1
                )
                if st.form_submit_button("Crear jurado"):
                    if not nombre_jurado:
                        st.error("Completá el nombre.")
                    else:
                        try:
                            jurado = Jurado(
                                nombre=nombre_jurado,
                                rol=RolJurado(rol_jurado),
                                peso_voto=peso_voto,
                            )
                            jurado_repo.guardar(jurado)
                            st.success(f"✅ Jurado creado: {jurado.nombre}")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error creando jurado: {e}")

            st.divider()
            st.subheader("Muestras")
            if not categorias:
                st.info("Creá una categoría primero para poder cargar muestras.")
            else:
                categoria_id_muestra = st.selectbox(
                    "Categoría",
                    options=[c.id for c in categorias],
                    format_func=lambda cid: _nombre_categoria(
                        next(c for c in categorias if c.id == cid)
                    ),
                    key="torneo_categoria_muestra",
                )
                revelar = st.checkbox(
                    "🔓 Revelar productor/receta en esta vista", value=False
                )
                muestras_categoria = muestra_repo.listar(categoria_id=categoria_id_muestra)
                if muestras_categoria:
                    st.dataframe(
                        pd.DataFrame(
                            [
                                {
                                    "Código ciego": m.codigo_ciego,
                                    "Receta interna": (
                                        (m.receta_id_interna or "-")
                                        if revelar
                                        else "🔒 oculto"
                                    ),
                                    "Productor": (
                                        (m.productor_id or "-") if revelar else "🔒 oculto"
                                    ),
                                }
                                for m in muestras_categoria
                            ]
                        ),
                        use_container_width=True,
                        hide_index=True,
                    )
                else:
                    st.info("Esta categoría todavía no tiene muestras.")

                with st.form("torneo_nueva_muestra"):
                    receta_id_interna = st.text_input("Receta interna (opcional)")
                    productor_id = st.text_input("Productor (opcional)")
                    if st.form_submit_button("Agregar muestra"):
                        try:
                            muestra = Muestra(
                                categoria_id=categoria_id_muestra,
                                receta_id_interna=receta_id_interna or None,
                                productor_id=productor_id or None,
                            )
                            muestra_repo.guardar(muestra)
                            st.success(
                                f"✅ Muestra creada, código ciego: {muestra.codigo_ciego}"
                            )
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error creando muestra: {e}")

        # TAB CARGAR PUNTAJE
        with tab_puntaje:
            if not jurados:
                st.info("Cargá al menos un jurado en la tab de Configuración.")
            elif not categorias:
                st.info("Cargá al menos una categoría en la tab de Configuración.")
            else:
                col1, col2 = st.columns(2)
                with col1:
                    jurado_id_sel = st.selectbox(
                        "Jurado",
                        options=[j.id for j in jurados],
                        format_func=lambda jid: next(
                            j.nombre for j in jurados if j.id == jid
                        ),
                        key="torneo_jurado_activo",
                    )
                with col2:
                    categoria_id_sel = st.selectbox(
                        "Categoría",
                        options=[c.id for c in categorias],
                        format_func=lambda cid: _nombre_categoria(
                            next(c for c in categorias if c.id == cid)
                        ),
                        key="torneo_categoria_activa",
                    )

                muestras_categoria = muestra_repo.listar(categoria_id=categoria_id_sel)
                if not muestras_categoria:
                    st.info("Esta categoría todavía no tiene muestras.")
                else:
                    orden = orden_cata_para_jurado(muestras_categoria, jurado_id_sel)
                    for muestra in orden:
                        puntajes_existentes = puntaje_repo.listar(
                            muestra_id=muestra.id, jurado_id=jurado_id_sel
                        )
                        puntaje_previo = (
                            puntajes_existentes[0] if puntajes_existentes else None
                        )

                        titulo = f"{'✅' if puntaje_previo else '⬜'} Muestra {muestra.codigo_ciego}"
                        with st.expander(titulo, expanded=puntaje_previo is None):
                            with st.form(f"torneo_puntaje_{muestra.id}_{jurado_id_sel}"):
                                # int(...): Puntaje.visual/aroma/sabor_boca son float
                                # (para la matematica de puntaje_ponderado()), pero
                                # st.slider exige que value/min_value/max_value sean
                                # del mismo tipo numerico.
                                visual = st.slider(
                                    "Visual",
                                    1,
                                    10,
                                    value=int(puntaje_previo.visual) if puntaje_previo else 5,
                                )
                                aroma = st.slider(
                                    "Aroma",
                                    1,
                                    10,
                                    value=int(puntaje_previo.aroma) if puntaje_previo else 5,
                                )
                                sabor_boca = st.slider(
                                    "Sabor y boca",
                                    1,
                                    10,
                                    value=(
                                        int(puntaje_previo.sabor_boca)
                                        if puntaje_previo
                                        else 5
                                    ),
                                )
                                comentario = st.text_area(
                                    "Comentario libre",
                                    value=(
                                        puntaje_previo.comentario_libre
                                        if puntaje_previo
                                        else ""
                                    ),
                                )
                                etiqueta_boton = (
                                    "Actualizar puntaje"
                                    if puntaje_previo
                                    else "Guardar puntaje"
                                )
                                if st.form_submit_button(etiqueta_boton):
                                    try:
                                        puntaje = Puntaje(
                                            muestra_id=muestra.id,
                                            jurado_id=jurado_id_sel,
                                            visual=visual,
                                            aroma=aroma,
                                            sabor_boca=sabor_boca,
                                            comentario_libre=comentario,
                                        )
                                        puntaje_repo.guardar(puntaje)
                                        st.success("✅ Puntaje guardado")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Error guardando puntaje: {e}")

        # TAB PROGRESO EN VIVO
        with tab_progreso:
            if not categorias:
                st.info("Cargá al menos una categoría en la tab de Configuración.")
            else:
                categoria_id_progreso = st.selectbox(
                    "Categoría",
                    options=[c.id for c in categorias],
                    format_func=lambda cid: _nombre_categoria(
                        next(c for c in categorias if c.id == cid)
                    ),
                    key="torneo_categoria_progreso",
                )
                muestras_categoria = muestra_repo.listar(
                    categoria_id=categoria_id_progreso
                )
                # Una sola consulta para todos los Puntaje en vez de una por
                # muestra (mismo criterio que evaluation/cierre_ronda.py).
                ids_muestras_categoria = {m.id for m in muestras_categoria}
                puntajes_categoria = [
                    p for p in puntaje_repo.listar() if p.muestra_id in ids_muestras_categoria
                ]
                progreso = calcular_progreso_categoria(
                    muestras_categoria, jurados, puntajes_categoria
                )

                col1, col2 = st.columns(2)
                with col1:
                    st.metric(
                        "Puntajes cargados",
                        f"{progreso.puntajes_cargados}/{progreso.puntajes_esperados}",
                    )
                with col2:
                    st.metric("Pendientes", len(progreso.pendientes))

                if progreso.pendientes:
                    muestras_por_id = {m.id: m for m in muestras_categoria}
                    jurados_por_id = {j.id: j for j in jurados}
                    st.dataframe(
                        pd.DataFrame(
                            [
                                {
                                    "Muestra": muestras_por_id[mid].codigo_ciego,
                                    "Jurado": jurados_por_id[jid].nombre,
                                }
                                for mid, jid in progreso.pendientes
                            ]
                        ),
                        use_container_width=True,
                        hide_index=True,
                    )

                st.divider()
                if st.button("🔒 Cerrar ronda y calcular ranking", type="primary"):
                    try:
                        ranking = cerrar_ronda_categoria(
                            categoria_id_progreso,
                            muestra_repo,
                            puntaje_repo,
                            jurado_repo,
                            ranking_repo,
                        )
                        st.success("✅ Ronda cerrada, ranking calculado.")
                        muestras_por_id = {m.id: m for m in muestras_categoria}
                        st.dataframe(
                            pd.DataFrame(
                                [
                                    {
                                        "Posición": r.posicion,
                                        "Código": muestras_por_id[r.muestra_id].codigo_ciego,
                                        "Puntaje final": round(r.puntaje_final, 2),
                                    }
                                    for r in ranking
                                ]
                            ),
                            use_container_width=True,
                            hide_index=True,
                        )
                        st.info("Mirá la tab '🏅 Resultados' para descargar los reportes.")
                    except ValueError as e:
                        st.error(f"No se pudo cerrar la ronda: {e}")

        # TAB RESULTADOS
        with tab_resultados:
            # Una sola consulta para todos los Ranking en vez de una por
            # categoria.
            ids_categoria_con_ranking = {r.categoria_id for r in ranking_repo.listar()}
            categorias_con_ranking = [
                c for c in categorias if c.id in ids_categoria_con_ranking
            ]
            if not categorias_con_ranking:
                st.info("Todavía ninguna categoría de este evento cerró su ronda.")
            else:
                categoria_id_resultado = st.selectbox(
                    "Categoría",
                    options=[c.id for c in categorias_con_ranking],
                    format_func=lambda cid: _nombre_categoria(
                        next(c for c in categorias_con_ranking if c.id == cid)
                    ),
                    key="torneo_categoria_resultados",
                )
                categoria_resultado = next(
                    c for c in categorias_con_ranking if c.id == categoria_id_resultado
                )
                ranking = ranking_repo.listar(categoria_id_resultado)
                muestras_categoria = muestra_repo.listar(
                    categoria_id=categoria_id_resultado
                )
                muestras_por_id = {m.id: m for m in muestras_categoria}

                st.dataframe(
                    pd.DataFrame(
                        [
                            {
                                "Posición": r.posicion,
                                "Código": muestras_por_id[r.muestra_id].codigo_ciego,
                                "Puntaje final": round(r.puntaje_final, 2),
                            }
                            for r in ranking
                        ]
                    ),
                    use_container_width=True,
                    hide_index=True,
                )

                pdf_planilla = _pdf_planilla_resultados(
                    categoria_resultado, muestras_categoria, ranking
                )
                st.download_button(
                    "📄 Descargar planilla de resultados (PDF)",
                    data=pdf_planilla,
                    file_name=f"resultados_{categoria_resultado.familia}_{categoria_resultado.submodalidad.value}.pdf",
                    mime="application/pdf",
                )

                st.divider()
                st.subheader("Fichas de cata por muestra")
                ranking_por_muestra = {r.muestra_id: r for r in ranking}
                for muestra in muestras_categoria:
                    r = ranking_por_muestra.get(muestra.id)
                    if not r:
                        continue
                    puntajes_muestra = puntaje_repo.listar(muestra_id=muestra.id)
                    pdf_ficha = _pdf_ficha_cata(
                        muestra, puntajes_muestra, jurados, r.puntaje_final
                    )
                    st.download_button(
                        f"📄 Ficha de cata - {muestra.codigo_ciego}",
                        data=pdf_ficha,
                        file_name=f"ficha_{muestra.codigo_ciego}.pdf",
                        mime="application/pdf",
                        key=f"torneo_ficha_{muestra.id}",
                    )

        # TAB PANEL DE PRODUCTOR
        with tab_productor:
            st.caption(
                "Trazabilidad de una receta o un productor a través de todas las "
                "ediciones del torneo, no solo el evento activo."
            )
            criterio = st.radio(
                "Buscar por", ["Receta interna", "Productor"], horizontal=True
            )
            valor_busqueda = st.text_input(
                "Receta interna" if criterio == "Receta interna" else "Productor"
            )

            if valor_busqueda:
                try:
                    if criterio == "Receta interna":
                        apariciones = historico_receta(
                            valor_busqueda,
                            muestra_repo,
                            categoria_repo,
                            evento_repo,
                            ranking_repo,
                        )
                    else:
                        apariciones = historico_productor(
                            valor_busqueda,
                            muestra_repo,
                            categoria_repo,
                            evento_repo,
                            ranking_repo,
                        )

                    if not apariciones:
                        st.info("Sin apariciones registradas para ese valor.")
                    else:
                        st.dataframe(
                            pd.DataFrame(
                                [
                                    {
                                        "Evento": a.evento_nombre,
                                        "Edición": a.evento_edicion_numero,
                                        "Fecha": a.evento_fecha,
                                        "Categoría": f"{a.categoria_familia} ({a.categoria_submodalidad.value})",
                                        "Código ciego": a.codigo_ciego,
                                        "Posición": (
                                            a.posicion if a.posicion is not None else "—"
                                        ),
                                        "Puntaje final": (
                                            round(a.puntaje_final, 2)
                                            if a.puntaje_final is not None
                                            else "—"
                                        ),
                                    }
                                    for a in apariciones
                                ]
                            ),
                            use_container_width=True,
                            hide_index=True,
                        )
                except Exception as e:
                    st.error(f"Error buscando histórico: {e}")

# =========================================================
# PIE DE PÁGINA
# =========================================================
st.divider()
st.caption(
    f"🍸 FernetOS v2.0.0 | Sistema de Formulación para Amari Competitivos | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
)
