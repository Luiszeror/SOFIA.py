# model/gnn_encoder.py
import torch
import torch.nn.functional as F
from torch_geometric.nn import SAGEConv, to_hetero


class GNNEncoder(torch.nn.Module):
    """
    Dos capas SAGEConv.
    Capa 1: proyecta los features a un espacio oculto de 'hidden' dims.
    Capa 2: comprime al embedding final de 'out' dims.
    (-1, -1) le dice a PyG que infiera las dims de entrada en tiempo de ejecución.
    """
    def __init__(self, hidden: int = 32, out: int = 16):
        super().__init__()
        self.conv1 = SAGEConv((-1, -1), hidden)
        self.conv2 = SAGEConv((-1, -1), out)

    def forward(self, x, edge_index):
        x = self.conv1(x, edge_index).relu()
        x = F.dropout(x, p=0.3, training=self.training)
        return self.conv2(x, edge_index)


def build_model(data) -> torch.nn.Module:
    """
    Envuelve GNNEncoder con to_hetero para que funcione
    con el grafo heterogéneo. data.metadata() devuelve
    los tipos de nodo y de arista que hay en el grafo.
    """
    base_model = GNNEncoder(hidden=32, out=16)
    model = to_hetero(base_model, metadata=data.metadata())
    return model