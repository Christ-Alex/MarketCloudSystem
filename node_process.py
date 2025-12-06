# node_process.py
import multiprocessing as mp
import time
from typing import Dict, Any
from storage_virtual_node import StorageVirtualNode

# --------- Command keys ---------
# { "op": "start" }
# { "op": "stop" }
# { "op": "add_connection", "node_id": "node2", "bandwidth": 1000 }
# { "op": "initiate_transfer", "file_id": "...", "file_name": "...", "file_size": 100*1024*1024 }
# { "op": "process_chunk", "file_id": "...", "chunk_id": 0, "source_node": "node1", "is_final_hop": True }
# { "op": "get_stats" }

def node_loop(node_id: str, cpu_capacity: int, memory_capacity: int, storage_capacity_mb: int,
              bandwidth_mbps: int, cmd_q: mp.Queue, resp_q: mp.Queue):
    node = StorageVirtualNode(
        node_id=node_id,
        cpu_capacity=cpu_capacity,
        memory_capacity=memory_capacity,
        storage_capacity_mb=storage_capacity_mb,
        bandwidth=bandwidth_mbps
    )

    running = True
    started = False

    while running:
        try:
            cmd: Dict[str, Any] = cmd_q.get(timeout=0.25)
        except Exception:
            cmd = None

        if cmd is None:
            continue

        op = cmd.get("op")

        if op == "start":
            if not started:
                node.start()
                started = True
            resp_q.put({"node": node_id, "ok": True})

        elif op == "stop":
            node.stop()
            running = False
            resp_q.put({"node": node_id, "ok": True})

        elif op == "add_connection":
            node.add_connection(cmd["node_id"], cmd["bandwidth"])
            resp_q.put({"node": node_id, "ok": True})

        elif op == "initiate_transfer":
            tr = node.initiate_file_transfer(
                file_id=cmd["file_id"],
                file_name=cmd["file_name"],
                file_size=cmd["file_size"],
                source_node=cmd.get("source_node")
            )
            resp_q.put({"node": node_id, "ok": tr is not None})

        elif op == "process_chunk":
            ok = node.process_chunk_transfer(
                file_id=cmd["file_id"],
                chunk_id=cmd["chunk_id"],
                source_node=cmd["source_node"],
                is_final_hop=cmd["is_final_hop"]
            )
            resp_q.put({"node": node_id, "ok": ok})

        elif op == "get_stats":
            resp_q.put({
                "node": node_id,
                "storage": node.get_storage_utilization(),
                "network": {
                    "current_utilization_bps": node.network_utilization,
                    "max_bandwidth_bps": node.bandwidth
                },
                "perf": node.get_performance_metrics()
            })

        else:
            resp_q.put({"node": node_id, "ok": False, "error": f"unknown op {op}"})

        # Allow threads to run
        time.sleep(0.01)