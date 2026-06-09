# model/train.py
import torch
import torch.nn.functional as F
from error_community.data.graph_builder import build_graph
from error_community.model.gnn_encoder import (build_model)


def contrastive_loss(emb, edge_index, margin=0.5):
    """
    Pares positivos (conectados): empuja embeddings cerca.
    Pares negativos (no conectados): empuja embeddings lejos.
    """
    src, dst = edge_index
    pos_sim = F.cosine_similarity(emb[src], emb[dst])
    pos_loss = (1 - pos_sim).mean()

    # Negativas: permutar destinos aleatoriamente
    neg_dst = dst[torch.randperm(dst.size(0))]
    neg_sim = F.cosine_similarity(emb[src], emb[neg_dst])
    neg_loss = F.relu(neg_sim - margin).mean()

    return pos_loss + neg_loss


def train(data, epochs: int = 100, lr: float = 0.01) -> torch.nn.Module:
    model = build_model(data)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)

    model.train()
    for epoch in range(epochs):
        optimizer.zero_grad()

        # Forward pass: obtiene embeddings para todos los tipos de nodo
        out = model(data.x_dict, data.edge_index_dict)

        # Supervisar con la relación student→error
        edge_index = data["student", "commits", "error"].edge_index
        student_emb = out["student"]

        # Solo usamos embeddings de estudiantes para la loss
        loss = contrastive_loss(student_emb, edge_index[:, :edge_index.size(1)])

        loss.backward()
        optimizer.step()

        if epoch % 10 == 0:
            print(f"Epoch {epoch:03d} | Loss: {loss.item():.4f}")

    model.eval()
    return model


def get_student_embeddings(model, data) -> torch.Tensor:
    """
    Extrae el embedding final de cada nodo estudiante.
    Retorna tensor shape [N_estudiantes, 16].
    """
    model.eval()
    with torch.no_grad():
        out = model(data.x_dict, data.edge_index_dict)
    return out["student"]  # [N, 16]