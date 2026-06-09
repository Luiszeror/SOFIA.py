# community/louvain_detector.py
import networkx as nx
import error_community.community as community_louvain  # python-louvain


def detect_communities(
    G: nx.Graph,
    student_ids: list[str]
) -> dict[str, list[str]]:
    """
    Aplica Louvain sobre el grafo de similitud.
    Retorna un dict: { "community_0": ["S001","S002"], "community_1": ["S003"] }
    """
    if G.number_of_edges() == 0:
        # Sin aristas: cada estudiante es su propia comunidad
        return {f"community_{i}": [sid] for i, sid in enumerate(student_ids)}

    partition = community_louvain.best_partition(G, weight="weight")
    # partition = {node_idx: community_id, ...}

    # Agrupar por comunidad
    communities: dict[int, list[str]] = {}
    for node_idx, com_id in partition.items():
        sid = G.nodes[node_idx]["student_id"]
        communities.setdefault(com_id, []).append(sid)

    # Renombrar con keys legibles
    return {
        f"community_{com_id}": members
        for com_id, members in sorted(communities.items())
    }


def label_communities(
    communities: dict[str, list[str]],
    student_error_map: dict[str, list[str]]
) -> dict[str, dict]:
    """
    Añade metadatos a cada comunidad:
    - miembros
    - errores dominantes (los más frecuentes en el grupo)
    - nivel de riesgo
    """
    labeled = {}
    for com_name, members in communities.items():
        # Contar qué errores cometen los miembros de esta comunidad
        error_counts: dict[str, int] = {}
        for sid in members:
            for err in student_error_map.get(sid, []):
                error_counts[err] = error_counts.get(err, 0) + 1

        dominant_errors = sorted(
            error_counts, key=error_counts.get, reverse=True
        )[:2]

        risk = "high" if len(members) >= 3 else "medium" if len(members) == 2 else "low"

        labeled[com_name] = {
            "members": members,
            "dominant_errors": dominant_errors,
            "risk_level": risk,
            "size": len(members)
        }
    return labeled