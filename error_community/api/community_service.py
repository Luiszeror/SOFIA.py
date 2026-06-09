# api/community_service.py
from error_community.data.graph_builder import build_graph
from error_community.model.train import train, get_student_embeddings
from error_community.community.similarity_graph import build_similarity_graph
from error_community.community.louvain_detector import detect_communities, label_communities


class CommunityService:
    """
    Servicio principal. Orquesta los 4 pasos del pipeline.
    El Concept Diagnosis Agent llama a este servicio.
    """

    def __init__(self, threshold: float = 0.70, epochs: int = 100):
        self.threshold = threshold
        self.epochs = epochs
        self._communities: dict = {}
        self._student_community_map: dict[str, str] = {}

    def run_pipeline(
        self,
        students, errors, concepts,
        student_commits_error,
        student_studies_concept,
        error_maps_concept,
        student_error_map: dict[str, list[str]]
    ) -> dict:
        """
        Ejecuta el pipeline completo de punta a punta.
        Retorna las comunidades etiquetadas.
        """
        print("=== Paso 1: Construyendo el grafo ===")
        data = build_graph(
            students, errors, concepts,
            student_commits_error,
            student_studies_concept,
            error_maps_concept
        )

        print("=== Paso 2: Entrenando la GNN ===")
        model = train(data, epochs=self.epochs)
        embeddings = get_student_embeddings(model, data)

        print("=== Paso 3: Construyendo grafo de similitud ===")
        student_ids = data["student"].student_ids
        G = build_similarity_graph(embeddings, student_ids, self.threshold)

        print("=== Paso 4: Detectando comunidades ===")
        communities = detect_communities(G, student_ids)
        labeled = label_communities(communities, student_error_map)

        # Guardar mapa inverso: student_id → community_name
        for com_name, info in labeled.items():
            for sid in info["members"]:
                self._student_community_map[sid] = com_name

        self._communities = labeled
        return labeled

    def get_community_for_student(self, student_id: str) -> dict:
        """
        El Concept Diagnosis Agent llama esto con el ID del estudiante
        para saber a qué comunidad pertenece y qué intervención activar.
        """
        com_name = self._student_community_map.get(student_id)
        if not com_name:
            return {"community": None, "message": "Estudiante no encontrado"}
        return {
            "student_id": student_id,
            "community": com_name,
            **self._communities[com_name]
        }

    def get_all_communities(self) -> dict:
        """Para el Instructor Dashboard."""
        return self._communities