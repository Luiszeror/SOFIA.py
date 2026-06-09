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
    """
    Construye el grafo heterogéneo completo.
    Retorna un objeto HeteroData listo para pasar al modelo.
    """
    data = HeteroData()

    # --- Nodos ---
    data["student"].x  = encode_students(students)
    data["error"].x    = encode_errors(errors)
    data["concept"].x  = encode_concepts(concepts)

    # Guardar IDs para recuperarlos después
    data["student"].student_ids = [s["id"] for s in students]

    # --- Aristas ---
    data["student", "commits",  "error"].edge_index   = encode_edges(student_commits_error)
    data["student", "studies",  "concept"].edge_index = encode_edges(student_studies_concept)
    data["error",   "maps_to",  "concept"].edge_index = encode_edges(error_maps_concept)

    return data


# --- Ejemplo de uso con datos reales ---
if __name__ == "__main__":
    students = [
        {"id": "S001", "total_attempts": 5,  "error_rate": 0.8, "avg_time_sec": 120},
        {"id": "S002", "total_attempts": 3,  "error_rate": 0.6, "avg_time_sec": 90},
        {"id": "S003", "total_attempts": 8,  "error_rate": 0.9, "avg_time_sec": 200},
        {"id": "S004", "total_attempts": 2,  "error_rate": 0.3, "avg_time_sec": 60},
    ]
    errors = [
        {"type_id": 0, "frequency": 12, "severity": 1, "module_id": 0},  # SyntaxError
        {"type_id": 1, "frequency": 7,  "severity": 2, "module_id": 1},  # LogicError
        {"type_id": 2, "frequency": 4,  "severity": 3, "module_id": 0},  # RuntimeError
        {"type_id": 3, "frequency": 9,  "severity": 2, "module_id": 2},  # GapError
    ]
    concepts = [
        {"concept_id": 0, "semester": 1, "difficulty": 0.9},  # Recursión
        {"concept_id": 1, "semester": 2, "difficulty": 0.7},  # Arreglos
        {"concept_id": 2, "semester": 2, "difficulty": 0.8},  # Punteros
    ]
    # Qué estudiante cometió qué tipo de error
    student_commits_error = [(0,0),(0,1),(1,1),(1,2),(2,2),(2,3),(3,3)]
    # Qué estudiante está viendo qué concepto
    student_studies_concept = [(0,0),(1,0),(1,1),(2,1),(2,2),(3,2)]
    # Qué error se relaciona con qué concepto
    error_maps_concept = [(0,0),(1,1),(2,1),(3,2)]

    data = build_graph(
        students, errors, concepts,
        student_commits_error,
        student_studies_concept,
        error_maps_concept
    )
    print(data)
    # HeteroData(
    #   student={ x=[4,3], student_ids=[4] },
    #   error={ x=[4,3] },
    #   concept={ x=[3,2] },
    #   (student,commits,error){ edge_index=[2,7] },
    #   ...
    # )