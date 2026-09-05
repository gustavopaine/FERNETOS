#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔═══════════════════════════════════════════════════════════════╗
║  FERNETOS - GENERADOR DE MANUAL EN PDF                        ║
║  Departamento pruebas                               ║
║  Versión: 1.0.0 | Fecha: Febrero 2026                         ║
╚═══════════════════════════════════════════════════════════════╝

Instrucciones:
1. Instalar dependencias: pip install reportlab
2. Ejecutar: python scripts/generar_manual_pdf.py
3. El PDF se guardará en: outputs/manual_fernetos_v1.0.0.pdf
"""

import sys
import os

# Configurar codificación para Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    Image,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime
import os

# ═══════════════════════════════════════════════════════════════
# CONFIGURACIÓN
# ═══════════════════════════════════════════════════════════════

OUTPUT_DIR = "outputs/manuals"
PDF_FILENAME = f"manual_fernetos_v1.0.0_{datetime.now().strftime('%Y%m%d')}.pdf"

# Crear directorio si no existe
os.makedirs(OUTPUT_DIR, exist_ok=True)
PDF_PATH = os.path.join(OUTPUT_DIR, PDF_FILENAME)

# ═══════════════════════════════════════════════════════════════
# ESTILOS
# ═══════════════════════════════════════════════════════════════


def crear_estilos():
    """Define los estilos de párrafo para el PDF."""
    estilos = getSampleStyleSheet()

    # Título principal
    estilos.add(
        ParagraphStyle(
            name="TituloPrincipal",
            parent=estilos["Heading1"],
            fontSize=24,
            textColor=colors.HexColor("#1a1a2e"),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName="Helvetica-Bold",
        )
    )

    # Subtítulo
    estilos.add(
        ParagraphStyle(
            name="Subtitulo",
            parent=estilos["Heading2"],
            fontSize=16,
            textColor=colors.HexColor("#16213e"),
            spaceAfter=20,
            spaceBefore=10,
            fontName="Helvetica-Bold",
        )
    )

    # Sección
    estilos.add(
        ParagraphStyle(
            name="Seccion",
            parent=estilos["Heading3"],
            fontSize=14,
            textColor=colors.HexColor("#0f3460"),
            spaceAfter=15,
            spaceBefore=20,
            fontName="Helvetica-Bold",
        )
    )

    # Texto normal
    estilos.add(
        ParagraphStyle(
            name="TextoNormal",
            parent=estilos["Normal"],
            fontSize=11,
            textColor=colors.HexColor("#333333"),
            alignment=TA_JUSTIFY,
            leading=16,
            fontName="Helvetica",
        )
    )

    # Texto para código
    estilos.add(
        ParagraphStyle(
            name="Codigo",
            parent=estilos["Normal"],
            fontSize=9,
            textColor=colors.HexColor("#2d2d2d"),
            backColor=colors.HexColor("#f5f5f5"),
            borderColor=colors.HexColor("#dddddd"),
            borderWidth=1,
            borderPadding=10,
            spaceAfter=15,
            fontName="Courier",
        )
    )

    # Nota destacada
    estilos.add(
        ParagraphStyle(
            name="Nota",
            parent=estilos["Normal"],
            fontSize=10,
            textColor=colors.HexColor("#e94560"),
            spaceAfter=15,
            spaceBefore=10,
            fontName="Helvetica-Oblique",
        )
    )

    return estilos


# ═══════════════════════════════════════════════════════════════
# CONTENIDO DEL MANUAL
# ═══════════════════════════════════════════════════════════════


def generar_portada():
    """Genera la portada del manual."""
    contenido = []

    # Espacio inicial
    contenido.append(Spacer(1, 2 * inch))

    # Logo/Título principal - usar caracteres seguros para Windows
    contenido.append(Paragraph("FERNETOS", crear_estilos()["TituloPrincipal"]))

    contenido.append(Spacer(1, 0.5 * inch))

    # Subtítulo
    contenido.append(
        Paragraph("Manual Completo de Usuario", crear_estilos()["Subtitulo"])
    )

    contenido.append(
        Paragraph(
            "Sistema de Formulacion para Amari Competitivos",
            crear_estilos()["TextoNormal"],
        )
    )

    contenido.append(Spacer(1, 1 * inch))

    # Información institucional
    contenido.append(
        Paragraph("Departamento pruebas", crear_estilos()["Seccion"])
    )

    contenido.append(
        Paragraph(
            f"Version: 1.0.0 | Fecha: {datetime.now().strftime('%B %Y')}",
            crear_estilos()["TextoNormal"],
        )
    )

    contenido.append(
        Paragraph(
            "Clasificacion: USO INTERNO - DOCUMENTACION DIDACTICA",
            crear_estilos()["TextoNormal"],
        )
    )

    contenido.append(Spacer(1, 2 * inch))

    # Tabla de metadatos
    datos_metadata = [
        ["Autor:", "Departamento pruebas"],
        ["Responsable:", "Suboficial Gustavo Eduardo PaineFIL"],
        ["Revision:", "Trimestral"],
        ["Proxima actualizacion:", "Mayo 2026"],
    ]

    tabla_metadata = Table(datos_metadata, colWidths=[2 * inch, 4 * inch])
    tabla_metadata.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f0f0f0")),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#333333")),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
            ]
        )
    )

    contenido.append(tabla_metadata)

    contenido.append(PageBreak())

    return contenido


def generar_tabla_contenidos():
    """Genera la tabla de contenidos."""
    contenido = []

    contenido.append(Paragraph("TABLA DE CONTENIDOS", crear_estilos()["Subtitulo"]))
    contenido.append(Spacer(1, 0.5 * inch))

    secciones = [
        "1. Introduccion",
        "2. Requisitos del Sistema",
        "3. Instalacion Paso a Paso",
        "4. Estructura del Proyecto",
        "5. Conceptos Fundamentales",
        "6. Flujo de Trabajo Completo",
        "7. Modulo 1: Panel de Control",
        "8. Modulo 2: Gestion de Tinturas",
        "9. Modulo 3: Curvas de Extraccion",
        "10. Modulo 4: Ensamblaje",
        "11. Modulo 5: Micromezclas",
        "12. Modulo 6: Pruebas A/B",
        "13. Modulo 7: Gestion de Stock",
        "14. Modulo 8: Configuracion",
        "15. Recetas de Ejemplo",
        "16. Solucion de Problemas",
        "17. Glosario de Terminos",
        "18. Seguridad y Buenas Practicas",
        "19. Anexos",
    ]

    datos_tabla = [[f"{i+1}. {sec}"] for i, sec in enumerate(secciones)]
    tabla_contenidos = Table(datos_tabla, colWidths=[6 * inch])
    tabla_contenidos.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("LINEBELOW", (0, 0), (-1, -1), 0.5, colors.HexColor("#dddddd")),
            ]
        )
    )

    contenido.append(tabla_contenidos)
    contenido.append(PageBreak())

    return contenido


def generar_seccion_introduccion():
    """Genera la sección de introducción."""
    contenido = []

    contenido.append(Paragraph("SECCION 1: INTRODUCCION", crear_estilos()["Seccion"]))
    contenido.append(Spacer(1, 0.3 * inch))

    contenido.append(
        Paragraph(
            "FernetOS es un sistema de gestion de formulacion disenado especificamente "
            "para la produccion de fernet y otros amari. A diferencia de metodos artesanales "
            "tradicionales, este sistema te permite control preciso sobre cada variable del "
            "proceso, repetibilidad entre lotes, trazabilidad completa de cada ingrediente, "
            "optimizacion basada en datos reales, escalabilidad desde 10L hasta 1000L, y "
            "ventaja competitiva en catas a ciegas.",
            crear_estilos()["TextoNormal"],
        )
    )

    contenido.append(Spacer(1, 0.3 * inch))

    contenido.append(
        Paragraph(
            "El sistema esta construido sobre tinturas modulares: en lugar de macerar todas "
            "las hierbas juntas, creamos extractos individuales (tinturas) que luego combinamos "
            "como si fueran ingredientes liquidos. Esto nos da un control milimetrico sobre "
            "el perfil final.",
            crear_estilos()["TextoNormal"],
        )
    )

    contenido.append(Spacer(1, 0.5 * inch))

    # Tabla de ventajas
    datos_ventajas = [
        ["Aspecto", "Metodo Tradicional", "Con FernetOS"],
        ["Repetibilidad", '"Mas o menos sale igual"', "Mismo resultado siempre"],
        ["Ajustes", '"A ojo" o por intuicion', "Ajustes milimetricos registrados"],
        ["Errores", "Dificiles de detectar", "El sistema te avisa antes"],
        ["Escalado", '"A ver que pasa si duplico"', "Calculo automatico preciso"],
        ["Documentacion", "Cuaderno que se pierde", "Base de datos con historial"],
    ]

    tabla_ventajas = Table(datos_ventajas, colWidths=[1.8 * inch, 2 * inch, 2 * inch])
    tabla_ventajas.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a1a2e")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
            ]
        )
    )

    contenido.append(tabla_ventajas)
    contenido.append(PageBreak())

    return contenido


def generar_seccion_requisitos():
    """Genera la sección de requisitos."""
    contenido = []

    contenido.append(
        Paragraph("SECCION 2: REQUISITOS DEL SISTEMA", crear_estilos()["Seccion"])
    )
    contenido.append(Spacer(1, 0.3 * inch))

    contenido.append(Paragraph("Hardware Minimo:", crear_estilos()["Subtitulo"]))

    datos_hardware = [
        ["Componente", "Minimo", "Recomendado"],
        ["Sistema Operativo", "Windows 10", "Windows 11"],
        ["Procesador", "Intel i3", "Intel i5 / AMD Ryzen 5"],
        ["Memoria RAM", "4 GB", "8 GB o mas"],
        ["Almacenamiento", "2 GB libres", "10 GB libres"],
        ["Pantalla", "1280x720", "1920x1080 o mas"],
    ]

    tabla_hardware = Table(datos_hardware, colWidths=[2 * inch, 2 * inch, 2 * inch])
    tabla_hardware.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#16213e")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
            ]
        )
    )

    contenido.append(tabla_hardware)
    contenido.append(Spacer(1, 0.5 * inch))

    contenido.append(Paragraph("Software Necesario:", crear_estilos()["Subtitulo"]))

    contenido.append(
        Paragraph(
            "- Python 3.9 o superior (descargar desde python.org)\n"
            "- Navegador web actualizado (Chrome, Firefox, Edge)\n"
            "- No se requiere experiencia en programacion",
            crear_estilos()["TextoNormal"],
        )
    )

    contenido.append(PageBreak())

    return contenido


def generar_seccion_instalacion():
    """Genera la sección de instalación."""
    contenido = []

    contenido.append(
        Paragraph("SECCION 3: INSTALACION PASO A PASO", crear_estilos()["Seccion"])
    )
    contenido.append(Spacer(1, 0.3 * inch))

    pasos = [
        "Paso 1: Verificar Python instalado (python --version)",
        "Paso 2: Descargar proyecto FernetOS",
        "Paso 3: Crear entorno virtual (python -m venv venv)",
        "Paso 4: Activar entorno (.\\venv\\Scripts\\Activate.ps1)",
        "Paso 5: Instalar dependencias (pip install -r requirements.txt)",
        "Paso 6: Inicializar BD (python inicializar_bd_fernet.py)",
        "Paso 7: Ejecutar aplicacion (streamlit run app.py)",
    ]

    for i, paso in enumerate(pasos, 1):
        contenido.append(Paragraph(f"{i}. {paso}", crear_estilos()["TextoNormal"]))
        contenido.append(Spacer(1, 0.1 * inch))

    contenido.append(Spacer(1, 0.5 * inch))

    contenido.append(
        Paragraph(
            "IMPORTANTE: Durante la instalacion de Python, marcar la casilla "
            "'Add Python to PATH' para evitar errores de reconocimiento de comandos.",
            crear_estilos()["Nota"],
        )
    )

    contenido.append(PageBreak())

    return contenido


def generar_seccion_conceptos():
    """Genera la sección de conceptos fundamentales."""
    contenido = []

    contenido.append(
        Paragraph("SECCION 4: CONCEPTOS FUNDAMENTALES", crear_estilos()["Seccion"])
    )
    contenido.append(Spacer(1, 0.3 * inch))

    contenido.append(Paragraph("Que es una tintura?", crear_estilos()["Subtitulo"]))

    contenido.append(
        Paragraph(
            "Una tintura es un extracto liquido obtenido al macerar hierbas, raices o especias "
            "en alcohol. En FernetOS, cada tintura es como un 'ingrediente liquido' que contiene "
            "los compuestos de una sola planta o de un grupo funcional especifico.",
            crear_estilos()["TextoNormal"],
        )
    )

    contenido.append(Spacer(1, 0.3 * inch))

    # Tabla de grupos funcionales
    datos_grupos = [
        ["Grupo", "Funcion", "Ejemplos", "Dias Maceracion"],
        ["Amargos", "Base de amargor", "Genciana, Quina", "16-21"],
        ["Aromatica", "Perfil herbal", "Menta, Romero", "5-7"],
        ["Especias", "Profundidad", "Canela, Cardamomo", "10-14"],
        ["Citricos", "Brillo y frescura", "Naranja, Limon", "3-4"],
        ["Correctivos", "Ajustes finos", "Clavo, Regaliz", "1-7"],
    ]

    tabla_grupos = Table(
        datos_grupos, colWidths=[1.2 * inch, 1.5 * inch, 1.8 * inch, 1 * inch]
    )
    tabla_grupos.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f3460")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
            ]
        )
    )

    contenido.append(tabla_grupos)
    contenido.append(PageBreak())

    return contenido


def generar_seccion_seguridad():
    """Genera la sección de seguridad."""
    contenido = []

    contenido.append(
        Paragraph("SECCION 5: SEGURIDAD Y BUENAS PRACTICAS", crear_estilos()["Seccion"])
    )
    contenido.append(Spacer(1, 0.3 * inch))

    contenido.append(
        Paragraph("Manipulacion Segura de Alcohol:", crear_estilos()["Subtitulo"])
    )

    contenido.append(
        Paragraph(
            "- Usar SIEMPRE alcohol grado alimenticio\n"
            "- Trabajar en area ventilada\n"
            "- Eliminar fuentes de ignicion\n"
            "- Usar EPP: guantes, gafas, delantal\n"
            "- NUNCA usar alcohol de quemar o industrial",
            crear_estilos()["TextoNormal"],
        )
    )

    contenido.append(Spacer(1, 0.3 * inch))

    contenido.append(
        Paragraph("Higiene y Esterilizacion:", crear_estilos()["Subtitulo"])
    )

    contenido.append(
        Paragraph(
            "- Lavar recipientes con jabon neutro\n"
            "- Esterilizar con agua hirviendo (10-15 min) o alcohol 70%\n"
            "- Secar al aire sin tocar con manos\n"
            "- Usar dentro de las 24 horas posteriores",
            crear_estilos()["TextoNormal"],
        )
    )

    contenido.append(PageBreak())

    return contenido


def generar_seccion_anexos():
    """Genera la sección de anexos."""
    contenido = []

    contenido.append(Paragraph("ANEXOS", crear_estilos()["Seccion"]))
    contenido.append(Spacer(1, 0.3 * inch))

    contenido.append(
        Paragraph("Anexo A: Checklist de Instalacion", crear_estilos()["Subtitulo"])
    )
    contenido.append(
        Paragraph(
            "Disponible para imprimir en la carpeta outputs/checklists/",
            crear_estilos()["TextoNormal"],
        )
    )

    contenido.append(Spacer(1, 0.3 * inch))

    contenido.append(
        Paragraph(
            "Anexo B: Plantilla de Registro de Cata", crear_estilos()["Subtitulo"]
        )
    )
    contenido.append(
        Paragraph(
            "Disponible para imprimir en la carpeta outputs/formatos/",
            crear_estilos()["TextoNormal"],
        )
    )

    contenido.append(Spacer(1, 0.3 * inch))

    contenido.append(
        Paragraph("Anexo C: Tabla de Conversiones", crear_estilos()["Subtitulo"])
    )
    contenido.append(
        Paragraph(
            "Volumen, peso y calculos de ABV disponibles en outputs/tablas/",
            crear_estilos()["TextoNormal"],
        )
    )

    contenido.append(Spacer(1, 1 * inch))

    # Pie de página institucional
    contenido.append(
        Paragraph(
            "Departamento pruebas\n"
            "Sistema de Formulacion para Amari Competitivos\n"
            f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
            "Version del Manual: 1.0.0\n"
            "Documento generado automaticamente",
            crear_estilos()["TextoNormal"],
        )
    )

    return contenido


# ═══════════════════════════════════════════════════════════════
# GENERACIÓN DEL PDF
# ═══════════════════════════════════════════════════════════════


def generar_pdf():
    """Función principal que genera el PDF completo."""

    # Usar prints simples sin caracteres especiales para Windows
    print("=" * 60)
    print("FERNETOS - GENERANDO MANUAL EN PDF")
    print("=" * 60)
    print()

    # Crear documento
    doc = SimpleDocTemplate(
        PDF_PATH,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    # Construir contenido
    contenido = []

    print("Generando portada...")
    contenido.extend(generar_portada())

    print("Generando tabla de contenidos...")
    contenido.extend(generar_tabla_contenidos())

    print("Generando seccion 1: Introduccion...")
    contenido.extend(generar_seccion_introduccion())

    print("Generando seccion 2: Requisitos...")
    contenido.extend(generar_seccion_requisitos())

    print("Generando seccion 3: Instalacion...")
    contenido.extend(generar_seccion_instalacion())

    print("Generando seccion 4: Conceptos...")
    contenido.extend(generar_seccion_conceptos())

    print("Generando seccion 5: Seguridad...")
    contenido.extend(generar_seccion_seguridad())

    print("Generando anexos...")
    contenido.extend(generar_seccion_anexos())

    # Construir PDF
    print()
    print("Construyendo documento PDF...")
    doc.build(contenido)

    print()
    print("=" * 60)
    print("PDF GENERADO EXITOSAMENTE")
    print("=" * 60)
    print(f"Ubicacion: {PDF_PATH}")
    print(f"Tamanio: {os.path.getsize(PDF_PATH) / 1024:.1f} KB")
    print("=" * 60)
    print()
    print("Proximos pasos:")
    print("1. Abrir el PDF para verificar formato")
    print("2. Imprimir si necesitas version fisica")
    print("3. Compartir con tu equipo de trabajo")
    print()


if __name__ == "__main__":
    try:
        # Configurar codificación para Windows
        if sys.platform == "win32":
            import io

            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

        generar_pdf()
    except ImportError as e:
        print("Error: La libreria 'reportlab' no esta instalada.")
        print()
        print("Solucion: Ejecutar el siguiente comando:")
        print("   pip install reportlab")
        print()
    except Exception as e:
        print(f"Error inesperado: {str(e)}")
        print()
        print("Verifica que tengas permisos de escritura en la carpeta outputs/")
