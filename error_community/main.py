# main.py  ←  punto de entrada del módulo
from api.community_service import CommunityService

if __name__ == "__main__":
    # Datos de ejemplo (en producción vienen de la BD del proyecto)
    students = [
        {"id": "S001", "total_attempts": 5,  "error_rate": 0.8, "avg_time_sec": 120},
        {"id": "S002", "total_attempts": 3,  "error_rate": 0.6, "avg_time_sec": 90},
        {"id": "S003", "total_attempts": 8,  "error_rate": 0.9, "avg_time_sec": 200},
        {"id": "S004", "total_attempts": 2,  "error_rate": 0.3, "avg_time_sec": 60},
    ]
    errors = [
        {"type_id": 0, "frequency": 12, "severity": 1, "module_id": 0},
        {"type_id": 1, "frequency": 7,  "severity": 2, "module_id": 1},
        {"type_id": 2, "frequency": 4,  "severity": 3, "module_id": 0},
        {"type_id": 3, "frequency": 9,  "severity": 2, "module_id": 2},
    ]
    concepts = [
        {"concept_id": 0, "semester": 1, "difficulty": 0.9},
        {"concept_id": 1, "semester": 2, "difficulty": 0.7},
        {"concept_id": 2, "semester": 2, "difficulty": 0.8},
    ]
    student_commits_error    = [(0,0),(0,1),(1,1),(1,2),(2,2),(2,3),(3,3)]
    student_studies_concept  = [(0,0),(1,0),(1,1),(2,1),(2,2),(3,2)]
    error_maps_concept       = [(0,0),(1,1),(2,1),(3,2)]
    student_error_map = {
        "S001": ["SyntaxError","LogicError"],
        "S002": ["LogicError","RuntimeError"],
        "S003": ["RuntimeError","GapError"],
        "S004": ["GapError"],
    }

    service = CommunityService(threshold=0.70, epochs=100)
    communities = service.run_pipeline(
        students, errors, concepts,
        student_commits_error, student_studies_concept, error_maps_concept,
        student_error_map
    )

    print("\n=== Comunidades detectadas ===")
    for name, info in communities.items():
        print(f"\n{name}:")
        print(f"  Miembros:        {info['members']}")
        print(f"  Errores top:     {info['dominant_errors']}")
        print(f"  Nivel de riesgo: {info['risk_level']}")

    print("\n=== Consulta por estudiante (como lo haría el Agente) ===")
    print(service.get_community_for_student("S001"))