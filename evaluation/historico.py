"""
Historico de una receta o un productor a traves de ediciones/eventos
(roadmap, seccion 5.5): para que el productor pueda trazar que version
de su receta compitio, en que categorias, y como puntuo.
"""

from typing import List, Optional

from evaluation.models import AparicionHistorica
from evaluation.repository import (
    CategoriaRepository,
    EventoRepository,
    MuestraRepository,
    RankingRepository,
)


def _historico_por_campo(
    valor: Optional[str],
    campo: str,
    muestra_repo: MuestraRepository,
    categoria_repo: CategoriaRepository,
    evento_repo: EventoRepository,
    ranking_repo: RankingRepository,
) -> List[AparicionHistorica]:
    if valor is None:
        raise ValueError(f"'{campo}' no puede ser None")

    apariciones = []
    for muestra in muestra_repo.listar():
        if getattr(muestra, campo) != valor:
            continue

        categoria = categoria_repo.get_by_id(muestra.categoria_id)
        evento = evento_repo.get_by_id(categoria.evento_id)
        ranking_de_la_muestra = next(
            (r for r in ranking_repo.listar(categoria.id) if r.muestra_id == muestra.id), None
        )

        apariciones.append(
            AparicionHistorica(
                evento_nombre=evento.nombre,
                evento_edicion_numero=evento.edicion_numero,
                evento_fecha=evento.fecha,
                categoria_familia=categoria.familia,
                categoria_submodalidad=categoria.submodalidad,
                muestra_id=muestra.id,
                codigo_ciego=muestra.codigo_ciego,
                posicion=ranking_de_la_muestra.posicion if ranking_de_la_muestra else None,
                puntaje_final=ranking_de_la_muestra.puntaje_final if ranking_de_la_muestra else None,
            )
        )

    return sorted(apariciones, key=lambda a: (a.evento_fecha, a.evento_edicion_numero))


def historico_receta(
    receta_id_interna: Optional[str],
    muestra_repo: MuestraRepository,
    categoria_repo: CategoriaRepository,
    evento_repo: EventoRepository,
    ranking_repo: RankingRepository,
) -> List[AparicionHistorica]:
    """Apariciones de `receta_id_interna` a traves de ediciones, en
    orden cronologico (por fecha de evento)."""
    return _historico_por_campo(
        receta_id_interna, "receta_id_interna", muestra_repo, categoria_repo, evento_repo, ranking_repo
    )


def historico_productor(
    productor_id: Optional[str],
    muestra_repo: MuestraRepository,
    categoria_repo: CategoriaRepository,
    evento_repo: EventoRepository,
    ranking_repo: RankingRepository,
) -> List[AparicionHistorica]:
    """Apariciones de `productor_id` a traves de ediciones, en orden
    cronologico (por fecha de evento)."""
    return _historico_por_campo(
        productor_id, "productor_id", muestra_repo, categoria_repo, evento_repo, ranking_repo
    )
