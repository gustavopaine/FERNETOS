import streamlit as st
import subprocess
import sys
import os
import glob
from datetime import datetime

st.set_page_config(page_title="Documentación", page_icon="📚", layout="wide")

st.title("📚 Documentación de FernetOS")
st.caption("Manuales, guías y documentación técnica")

tabs = st.tabs(["📖 Manual de Usuario", "📊 Guías Rápidas", "🔧 Scripts"])

with tabs[0]:
    st.subheader("Manual Completo de Usuario")

    col1, col2 = st.columns([1, 1])

    with col1:
        with st.container(border=True):
            st.write("**📥 Generar Manual PDF**")
            st.write("Genera el manual completo con toda la documentación del sistema.")

            if st.button("📥 Generar Manual", use_container_width=True):
                with st.spinner("Generando manual... (esto puede tomar unos segundos)"):
                    try:
                        result = subprocess.run(
                            [sys.executable, "scripts/generar_manual_pdf.py"],
                            capture_output=True,
                            text=True,
                            cwd=os.path.dirname(os.path.dirname(__file__)),
                        )

                        if result.returncode == 0:
                            pdf_files = glob.glob(
                                "outputs/manuals/manual_fernetos_*.pdf"
                            )
                            if pdf_files:
                                latest_pdf = max(pdf_files, key=os.path.getctime)

                                with open(latest_pdf, "rb") as f:
                                    st.download_button(
                                        "📥 Descargar PDF",
                                        f,
                                        file_name=os.path.basename(latest_pdf),
                                        mime="application/pdf",
                                        use_container_width=True,
                                    )
                                st.success(
                                    f"✅ Manual listo: {os.path.basename(latest_pdf)}"
                                )

                                # Mostrar información del archivo
                                file_size = os.path.getsize(latest_pdf) / 1024
                                st.info(f"📊 Tamaño: {file_size:.1f} KB")
                            else:
                                st.warning("PDF generado pero no encontrado")
                        else:
                            st.error(f"Error: {result.stderr}")
                    except Exception as e:
                        st.error(f"Error: {e}")

    with col2:
        with st.container(border=True):
            st.write("**📋 Versiones Disponibles**")

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
                                f"📥 {file_name[:20]}...",
                                f,
                                file_name=file_name,
                                mime="application/pdf",
                                key=f"dl_{pdf}",
                            )
            else:
                st.info("No hay manuales generados aún")

with tabs[1]:
    st.subheader("Guías Rápidas")

    guias = {
        "Instalación Rápida": """
        1. python -m venv venv
        2. venv\\Scripts\\activate
        3. pip install -r requirements.txt
        4. python inicializar_bd_fernet.py
        5. streamlit run app.py
        """,
        "Flujo de Trabajo": """
        1. Crear tinturas
        2. Registrar catas cada 48h
        3. Analizar curvas
        4. Filtrar y estabilizar
        5. Ensamblar blend
        6. Microblending
        7. Pruebas A/B
        8. Escalar a producción
        """,
        "Solución de Problemas Comunes": """
        Error 'No module named modules': Ejecutar desde raíz del proyecto
        Error 'Port in use': Cerrar otras instancias de Streamlit
        Error 'Base de datos no encontrada': Ejecutar inicializar_bd_fernet.py
        """,
    }

    for titulo, contenido in guias.items():
        with st.expander(titulo):
            st.code(contenido, language="bash")

with tabs[2]:
    st.subheader("Scripts Disponibles")

    scripts = [
        (
            "inicializar_bd_fernet.py",
            "Inicializa la base de datos con tinturas de ejemplo",
        ),
        ("check_db.py", "Verifica el estado de la base de datos"),
        ("scripts/generar_manual_pdf.py", "Genera el manual de usuario en PDF"),
        ("limpiar_duplicados.py", "Limpia tinturas duplicadas (opcional)"),
    ]

    for script, desc in scripts:
        with st.container(border=True):
            col_s1, col_s2 = st.columns([3, 1])
            with col_s1:
                st.write(f"**{script}**")
                st.caption(desc)
            with col_s2:
                if os.path.exists(script) or os.path.exists(
                    os.path.join("scripts", script)
                ):
                    if st.button(f"▶️ Ejecutar", key=f"run_{script}"):
                        with st.spinner(f"Ejecutando {script}..."):
                            try:
                                script_path = (
                                    script
                                    if os.path.exists(script)
                                    else os.path.join("scripts", script)
                                )
                                result = subprocess.run(
                                    [sys.executable, script_path],
                                    capture_output=True,
                                    text=True,
                                )
                                st.code(result.stdout)
                                if result.stderr:
                                    st.error(result.stderr)
                            except Exception as e:
                                st.error(f"Error: {e}")
                else:
                    st.warning("No encontrado")
