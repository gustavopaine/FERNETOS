"""
Salidas exportables del modulo de evaluacion (roadmap, seccion 5.5):
planilla de resultados por categoria y ficha de cata por muestra, en
PDF via reportlab (ya usado en el proyecto, ver
scripts/generar_manual_pdf.py).

Ambas funciones publicas devuelven los bytes del PDF; escribirlos a
disco es responsabilidad de quien las llama.
"""

from io import BytesIO
from typing import List, Tuple

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from evaluation.models import Categoria, Jurado, Muestra, Puntaje, Ranking

_ESTILOS = getSampleStyleSheet()

_ESTILO_TABLA = TableStyle(
    [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f3460")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f2f2f2")]),
    ]
)


def _filas_planilla(
    muestras: List[Muestra], ranking: List[Ranking]
) -> List[Tuple[int, str, float, str]]:
    """
    Una fila por posicion del `ranking`, ordenadas de 1ro a ultimo
    (sin asumir que `ranking` ya venga ordenado). `productor_id` va
    vacio ("-") salvo que la muestra ya lo tenga seteado (revelado) -
    ver docstring de `Muestra`.
    """
    muestras_por_id = {m.id: m for m in muestras}
    filas = []
    for r in sorted(ranking, key=lambda r: r.posicion):
        muestra = muestras_por_id.get(r.muestra_id)
        if muestra is None:
            raise ValueError(f"Ranking referencia una muestra desconocida: {r.muestra_id}")
        filas.append((r.posicion, muestra.codigo_ciego, r.puntaje_final, muestra.productor_id or "-"))
    return filas


def _filas_ficha_cata(
    puntajes: List[Puntaje], jurados: List[Jurado]
) -> List[Tuple[str, float, float, float, float, str]]:
    """
    Una fila por `Puntaje`, en el orden recibido. El nombre del jurado
    se resuelve contra `jurados`; si no esta (dato incompleto), se usa
    el `jurado_id` crudo como fallback - a diferencia de
    `evaluation.scoring`, esto es un reporte de lectura humana, no un
    calculo cuya integridad dependa de tener todos los jurados.
    """
    nombres_por_id = {j.id: j.nombre for j in jurados}
    return [
        (
            nombres_por_id.get(p.jurado_id, p.jurado_id),
            p.visual,
            p.aroma,
            p.sabor_boca,
            p.puntaje_ponderado(),
            p.comentario_libre,
        )
        for p in puntajes
    ]


def generar_planilla_resultados_categoria(
    categoria: Categoria, muestras: List[Muestra], ranking: List[Ranking]
) -> bytes:
    """Planilla de resultados de una categoria: posicion, codigo ciego,
    puntaje final y productor (si ya fue revelado)."""
    filas = _filas_planilla(muestras, ranking)

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    contenido = [
        Paragraph(f"Resultados - {categoria.familia} ({categoria.submodalidad.value})", _ESTILOS["Title"]),
        Spacer(1, 0.5 * cm),
    ]

    encabezado = ["Posicion", "Codigo", "Puntaje final", "Productor"]
    datos = [encabezado] + [
        [str(pos), codigo, f"{puntaje:.2f}", productor]
        for pos, codigo, puntaje, productor in filas
    ]
    tabla = Table(datos, repeatRows=1)
    tabla.setStyle(_ESTILO_TABLA)
    contenido.append(tabla)

    doc.build(contenido)
    return buffer.getvalue()


def generar_ficha_cata_muestra(
    muestra: Muestra, puntajes: List[Puntaje], jurados: List[Jurado], puntaje_final: float
) -> bytes:
    """Ficha de cata de una muestra, para devolver feedback al
    productor: puntaje de cada jurado (con comentario libre) y el
    puntaje final ya calculado (ver `evaluation.scoring`)."""
    filas = _filas_ficha_cata(puntajes, jurados)

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    contenido = [
        Paragraph(f"Ficha de cata - Muestra {muestra.codigo_ciego}", _ESTILOS["Title"]),
        Spacer(1, 0.5 * cm),
    ]

    encabezado = ["Jurado", "Visual", "Aroma", "Sabor/Boca", "Ponderado", "Comentario"]
    datos = [encabezado] + [
        [nombre, str(visual), str(aroma), str(sabor_boca), f"{ponderado:.2f}", comentario]
        for nombre, visual, aroma, sabor_boca, ponderado, comentario in filas
    ]
    tabla = Table(datos, repeatRows=1)
    tabla.setStyle(_ESTILO_TABLA)
    contenido.append(tabla)
    contenido.append(Spacer(1, 0.5 * cm))
    contenido.append(Paragraph(f"Puntaje final: {puntaje_final:.2f}", _ESTILOS["Heading2"]))

    doc.build(contenido)
    return buffer.getvalue()
