from typing import Dict, Optional, Tuple
from collections import defaultdict
import hashlib
import time
import networkx as nx
from storage_virtual_node import StorageVirtualNode, FileTransfer, TransferStatus

class StorageVirtualNetwork:
    def __init__(self):
        self.nodes: Dict[str, StorageVirtualNode] = {}
        self.transfer_operations: Dict[str, Dict[str, FileTransfer]] = defaultdict(dict)

    def add_node(self, node: StorageVirtualNode):
        self.nodes[node.node_id] = node

    def connect_nodes(self, node1_id: str, node2_id: str, bandwidth: int):
        if node1_id in self.nodes and node2_id in self.nodes:
            self.nodes[node1_id].add_connection(node2_id, bandwidth)
            self.nodes[node2_id].add_connection(node1_id, bandwidth)
            return True
        return False

    def _build_graph(self) -> nx.Graph:
        G = nx.Graph()
        for nid, node in self.nodes.items():
            G.add_node(nid)
            for nbr in node.connections.keys():
                G.add_edge(nid, nbr)
        return G

    def find_route(self, source_id: str, target_id: str) -> Optional[list]:
        if source_id not in self.nodes or target_id not in self.nodes:
            return None
        G = self._build_graph()
        try:
            path = nx.shortest_path(G, source_id, target_id)
            print(f"📡 Route computed: {' → '.join(path)}")
            return path
        except nx.NetworkXNoPath:
            print(f"❌ No route between {source_id} and {target_id}")
            return None

    def initiate_file_transfer(self, source_node_id: str, target_node_id: str, file_name: str, file_size: int) -> Optional[FileTransfer]:
        if source_node_id not in self.nodes or target_node_id not in self.nodes:
            return None

        path = self.find_route(source_node_id, target_node_id)
        if path is None:
            return None

        file_id = hashlib.md5(f"{file_name}-{time.time()}".encode()).hexdigest()
        created_transfers = {}

        for node_id in path:
            node = self.nodes[node_id]
            tr = node.initiate_file_transfer(file_id, file_name, file_size, source_node=source_node_id)
            if tr is None:
                for nid in created_transfers:
                    if file_id in self.nodes[nid].active_transfers:
                        del self.nodes[nid].active_transfers[file_id]
                print(f"❌ Not enough storage on {node_id} to initiate transfer")
                return None
            created_transfers[node_id] = tr

        self.transfer_operations[source_node_id][file_id] = created_transfers[target_node_id]
        return created_transfers[target_node_id]

    def process_file_transfer(self, source_node_id: str, target_node_id: str,file_id: str, chunks_per_step: int = 1) -> Tuple[int, bool]:
        if source_node_id not in self.transfer_operations:
            return (0, False)
        if file_id not in self.transfer_operations[source_node_id]:
            return (0, False)

        transfer = self.transfer_operations[source_node_id][file_id]
        path = self.find_route(source_node_id, target_node_id)
        if path is None:
            return (0, False)

        chunks_done = 0
        for chunk in transfer.chunks:
            if chunk.status == TransferStatus.COMPLETED:
                continue
            if chunks_done >= chunks_per_step:
                break

            hop_ok = True
            for i in range(len(path) - 1):
                hop_from = path[i]
                hop_to = path[i + 1]
                next_node = self.nodes[hop_to]

                # ✅ Mark only the destination hop as final
                is_final = (hop_to == target_node_id)
                ok = next_node.process_chunk_transfer(
                    file_id, chunk.chunk_id, hop_from, is_final_hop=is_final
                )
                if not ok:
                    hop_ok = False
                    break

            if hop_ok:
                chunks_done += 1

        # ✅ Check if the destination node has finalized the file
        dest_node = self.nodes[target_node_id]
        if file_id in dest_node.stored_files:
            del self.transfer_operations[source_node_id][file_id]
            return (chunks_done, True)

        return (chunks_done, False)

    def get_network_stats(self) -> Dict[str, float]:
        total_bandwidth = sum(n.bandwidth for n in self.nodes.values()) or 1
        used_bandwidth = sum(n.network_utilization for n in self.nodes.values())
        total_storage = sum(n.total_storage for n in self.nodes.values()) or 1
        used_storage = sum(n.used_storage for n in self.nodes.values())

        return {
            "total_nodes": len(self.nodes),
            "total_bandwidth_bps": total_bandwidth,
            "used_bandwidth_bps": used_bandwidth,
            "bandwidth_utilization": (used_bandwidth / total_bandwidth) * 100,
            "total_storage_bytes": total_storage,
            "used_storage_bytes": used_storage,
            "storage_utilization": (used_storage / total_storage) * 100,
            "active_transfers": sum(len(t) for t in self.transfer_operations.values())
        }