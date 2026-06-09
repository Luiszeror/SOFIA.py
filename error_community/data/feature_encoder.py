# data/feature_encoder.py
import torch

def encode_students(student_records: list[dict]) -> torch.Tensor:
    """
    Cada estudiante: {id, total_attempts, error_rate, avg_time_sec}
    Devuelve tensor shape [N_estudiantes, 3]
    """
    features = []
    for s in student_records:
        features.append([
            s["total_attempts"],
            s["error_rate"],        # 0.0 a 1.0
            s["avg_time_sec"] / 300 # normalizar a ~[0,1]
        ])
    return torch.tensor(features, dtype=torch.float)


def encode_errors(error_records: list[dict]) -> torch.Tensor:
    """
    Cada error: {type_id, frequency, severity, module_id}
    severity: 1=sintaxis, 2=lógico, 3=runtime, 4=conceptual
    Devuelve tensor shape [N_tipos_error, 3]
    """
    features = []
    for e in error_records:
        features.append([
            e["frequency"],
            e["severity"],
            e["module_id"]
        ])
    return torch.tensor(features, dtype=torch.float)


def encode_concepts(concept_records: list[dict]) -> torch.Tensor:
    """
    Cada concepto: {concept_id, semester, difficulty}
    difficulty: 0.0 a 1.0
    Devuelve tensor shape [N_conceptos, 2]
    """
    features = []
    for c in concept_records:
        features.append([
            c["semester"],
            c["difficulty"]
        ])
    return torch.tensor(features, dtype=torch.float)


def encode_edges(edge_list: list[tuple]) -> torch.Tensor:
    """
    edge_list: [(src_idx, dst_idx), ...]
    Devuelve edge_index shape [2, N_aristas]
    """
    src = [e[0] for e in edge_list]
    dst = [e[1] for e in edge_list]
    return torch.tensor([src, dst], dtype=torch.long)