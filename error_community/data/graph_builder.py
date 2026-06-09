# data/graph_builder.py
from torch_geometric.data import HeteroData
from feature_encoder import (
    encode_students, encode_errors,
    encode_concepts, encode_edges
)


def build_graph(
    students: list[dict],
    errors:   list[dict],
    concepts: list[dict],
    student_commits_error: list[tuple],   # (student_idx, error_idx)
    student_studies_concept: list[tuple], # (student_idx, concept_idx)
    error_maps_concept: list[tuple],      # (error_idx, concept_idx)
) -> HeteroData:
    data = HeteroData()

    # --- Nodos ---
    data["student"].x  = encode_students(students)
    data["error"].x    = encode_errors(errors)
    data["concept"].x  = encode_concepts(concepts)

    data["student"].student_ids = [s["id"] for s in students]

    # --- Aristas originales ---
    data["student", "commits",  "error"].edge_index   = encode_edges(student_commits_error)
    data["student", "studies",  "concept"].edge_index = encode_edges(student_studies_concept)
    data["error",   "maps_to",  "concept"].edge_index = encode_edges(error_maps_concept)

    # --- Aristas inversas (necesarias para que to_hetero funcione) ---
    # Sin estas, 'student' nunca es nodo DESTINO y to_hetero no puede
    # aplicarle relu/dropout → ValueError en build_model()
    data["error",   "rev_commits",  "student"].edge_index = encode_edges(
        [(e, s) for s, e in student_commits_error]
    )
    data["concept", "rev_studies",  "student"].edge_index = encode_edges(
        [(c, s) for s, c in student_studies_concept]
    )
    data["concept", "rev_maps_to",  "error"].edge_index   = encode_edges(
        [(c, e) for e, c in error_maps_concept]
    )

    return data