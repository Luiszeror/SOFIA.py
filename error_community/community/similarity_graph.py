# community/similarity_graph.py
import torch
import torch.nn.functional as F
import networkx as nx


def build_similarity_graph(
    embeddings: torch.Tensor,
    student_ids: list[str],
    threshold: float = 0.70
) -> nx.Graph:
    """
    Compara cada par de estudiantes con similitud coseno.
    Si la similitud supera el umbral, los conecta con una arista
    ponderada por ese valor.
    """
    G = nx.Graph()
    n = embeddings.shape[0]

    # Agregar todos los nodos con su ID real
    for i, sid in enumerate(student_ids):
        G.add_node(i, student_id=sid)

    # Comparar todos los pares O(n²)
    for i in range(n):
        for j in range(i + 1, n):
            sim = F.cosine_similarity(
                embeddings[i].unsqueeze(0),
                embeddings[j].unsqueeze(0)
            ).item()
            if sim >= threshold:
                G.add_edge(i, j, weight=round(sim, 4))

    print(f"Grafo de similitud: {G.number_of_nodes()} nodos, "
          f"{G.number_of_edges()} aristas (umbral={threshold})")
    return G