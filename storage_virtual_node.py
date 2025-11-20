import threading
import time
import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Union
from enum import Enum, auto
import hashlib
from ipaddress import IPv4Address

class TransferStatus(Enum):
    PENDING = auto()
    IN_PROGRESS = auto()
    COMPLETED = auto()
    FAILED = auto()

@dataclass
class FileChunk:
    chunk_id: int
    size: int  # in bytes
    checksum: str
    status: TransferStatus = TransferStatus.PENDING
    stored_node: Optional[str] = None

@dataclass
class FileTransfer:
    file_id: str
    file_name: str
    total_size: int  # in bytes
    chunks: List[FileChunk]
    status: TransferStatus = TransferStatus.PENDING
    created_at: float = time.time()
    completed_at: Optional[float] = None

class StorageVirtualNode:
    def __init__(self, node_id: str, ip_address: str, cpu_capacity: int,
                 memory_capacity: int, storage_capacity: int, bandwidth: int):
        self.node_id = node_id
        self.cpu_capacity = cpu_capacity
        self.ip = IPv4Address(ip_address)
        self.memory_capacity = memory_capacity
        self.total_storage = storage_capacity * 1024 * 1024 * 1024  # GB → bytes
        self.bandwidth = bandwidth * 1000000  # Mbps → bps

        # Current utilization
        self.used_storage = 0
        self.active_transfers: Dict[str, FileTransfer] = {}
        self.stored_files: Dict[str, FileTransfer] = {}
        self.network_utilization = 0

        # Performance metrics
        self.total_requests_processed = 0
        self.total_data_transferred = 0
        self.failed_transfers = 0

        # Network connections (neighbor_id -> bps)
        self.connections: Dict[str, int] = {}

        # Thread management
        self._threads: List[threading.Thread] = []
        self._stop_event = threading.Event()

    # ---------- Network topology ----------
    def add_connection(self, node_id: str, bandwidth: int):
        self.connections[node_id] = bandwidth * 1000000  # store in bps
        print(f"Connected {self.node_id} ({self.ip}) <--> {node_id}")

    # ---------- Autonomous behaviors (threads) ----------
    def listen_network(self):
        """Simulate a network listener loop."""
        while not self._stop_event.is_set():
            print(f"[{self.node_id} | {self.ip}] Listening for incoming connections...")
            time.sleep(2)

    def manage_storage(self):
        """Periodically report storage utilization."""
        while not self._stop_event.is_set():
            utilization = self.get_storage_utilization()['utilization_percent']
            print(f"[{self.node_id}] Storage utilization: {utilization:.2f}%")
            time.sleep(5)

    def handle_transfers(self):
        """Monitor active transfers (placeholder for future async processing)."""
        while not self._stop_event.is_set():
            if self.active_transfers:
                print(f"[{self.node_id}] Handling {len(self.active_transfers)} active transfers...")
            time.sleep(3)

    def start(self):
        """Launch autonomous threads for this node."""
        if self._threads:
            print(f"[{self.node_id}] Threads already started.")
            return

        t1 = threading.Thread(target=self.listen_network, daemon=True)
        t2 = threading.Thread(target=self.manage_storage, daemon=True)
        t3 = threading.Thread(target=self.handle_transfers, daemon=True)

        self._threads.extend([t1, t2, t3])
        for t in self._threads:
            t.start()

        print(f"[{self.node_id}] Node started with autonomous threads.")

    def stop(self):
        """Signal threads to stop and wait for them."""
        self._stop_event.set()
        for t in self._threads:
            if t.is_alive():
                t.join(timeout=1.0)
        print(f"[{self.node_id}] Node stopped.")

    # ---------- Transfer utilities ----------
    def _calculate_chunk_size(self, file_size: int) -> int:
        """Determine optimal chunk size based on file size."""
        if file_size < 10 * 1024 * 1024:            # < 10MB
            return 512 * 1024                      # 512KB chunks
        elif file_size < 100 * 1024 * 1024:         # < 100MB
            return 2 * 1024 * 1024                  # 2MB chunks
        else:
            return 10 * 1024 * 1024                 # 10MB chunks

    def _generate_chunks(self, file_id: str, file_size: int) -> List[FileChunk]:
        """Break file into chunks for transfer."""
        chunk_size = self._calculate_chunk_size(file_size)
        num_chunks = math.ceil(file_size / chunk_size)

        chunks = []
        for i in range(num_chunks):
            fake_checksum = hashlib.md5(f"{file_id}-{i}".encode()).hexdigest()
            actual_chunk_size = min(chunk_size, file_size - i * chunk_size)
            chunks.append(FileChunk(
                chunk_id=i,
                size=actual_chunk_size,
                checksum=fake_checksum
            ))
        return chunks

    # ---------- Transfer lifecycle ----------
    def initiate_file_transfer(
        self,
        file_id: str,
        file_name: str,
        file_size: int,
        source_node: Optional[str] = None
    ) -> Optional[FileTransfer]:
        """Initiate a file storage request to this node."""
        if self.used_storage + file_size > self.total_storage:
            return None

        chunks = self._generate_chunks(file_id, file_size)
        transfer = FileTransfer(
            file_id=file_id,
            file_name=file_name,
            total_size=file_size,
            chunks=chunks
        )

        self.active_transfers[file_id] = transfer
        return transfer

    def process_chunk_transfer(
        self,
        file_id: str,
        chunk_id: int,
        source_node: str,
        is_final_hop: bool = False
    ) -> bool:
        """Process an incoming file chunk."""
        if file_id not in self.active_transfers:
            return False

        transfer = self.active_transfers[file_id]

        try:
            chunk = next(c for c in transfer.chunks if c.chunk_id == chunk_id)
        except StopIteration:
            return False

        print(f"[{self.node_id} | {self.ip}] Preparing chunk {chunk.chunk_id} of file {file_id} from {source_node}")

        # Simulate network transfer time
        chunk_size_bits = chunk.size * 8
        available_bandwidth = min(
            self.bandwidth - self.network_utilization,
            self.connections.get(source_node, 0)
        )

        if available_bandwidth <= 0:
            print(f"[{self.node_id}] No available bandwidth for chunk ❌ {chunk.chunk_id}")
            self.failed_transfers += 1
            return False

        transfer_time = chunk_size_bits / available_bandwidth
        print(f"[{self.node_id} | {self.ip}] START transfer of chunk {chunk.chunk_id}")
        print(f"   Using bandwidth: {available_bandwidth} bps")
        print(f"   Estimated time: {transfer_time:.4f}s")

        time.sleep(transfer_time)

        # Update chunk status
        chunk.status = TransferStatus.COMPLETED
        chunk.stored_node = self.node_id
        print(f"[{self.node_id} | {self.ip}]  COMPLETED chunk ✔ {chunk.chunk_id}")

        # Update metrics
        temporary_bandwidth_usage = available_bandwidth * 0.2
        self.network_utilization += temporary_bandwidth_usage
        self.network_utilization -= temporary_bandwidth_usage
        self.network_utilization = max(0, min(self.network_utilization, self.bandwidth))
        self.total_data_transferred += chunk.size

        completed_chunks = sum(1 for c in transfer.chunks if c.status == TransferStatus.COMPLETED)
        total_chunks = len(transfer.chunks)
        print(f"[{self.node_id} | {self.ip}] Progress: {completed_chunks}/{total_chunks} chunks completed")

        # ✅ Only finalize if this is the final hop
        if is_final_hop and all(c.status == TransferStatus.COMPLETED for c in transfer.chunks):
            transfer.status = TransferStatus.COMPLETED
            transfer.completed_at = time.time()
            self.used_storage += transfer.total_size
            self.stored_files[file_id] = transfer
            del self.active_transfers[file_id]
            self.total_requests_processed += 1

            stored_mb = transfer.total_size / (1024 * 1024)
            print(f"[{self.node_id} | {self.ip}] Stored total: {stored_mb:.2f} MB")
            print(f"[{self.node_id} | {self.ip}] 🎉 FILE TRANSFER COMPLETED for file {file_id}")

        return True

    def retrieve_file(
        self,
        file_id: str,
        destination_node: str
    ) -> Optional[FileTransfer]:
        """Initiate file retrieval to another node."""
        if file_id not in self.stored_files:
            return None

        file_transfer = self.stored_files[file_id]
        new_transfer = FileTransfer(
            file_id=f"retr-{file_id}-{time.time()}",
            file_name=file_transfer.file_name,
            total_size=file_transfer.total_size,
            chunks=[
                FileChunk(
                    chunk_id=c.chunk_id,
                    size=c.size,
                    checksum=c.checksum,
                    stored_node=destination_node
                )
                for c in file_transfer.chunks
            ]
        )
        return new_transfer

    # ---------- Metrics ----------
    def get_storage_utilization(self) -> Dict[str, Union[int, float]]:
        return {
            "used_bytes": self.used_storage,
            "total_bytes": self.total_storage,
            "utilization_percent": (self.used_storage / self.total_storage) * 100 if self.total_storage else 0.0,
            "files_stored": len(self.stored_files),
            "active_transfers": len(self.active_transfers)
        }

    def get_network_utilization(self) -> Dict[str, Union[int, float, List[str]]]:
        total_bandwidth_bps = self.bandwidth
        return {
            "current_utilization_bps": self.network_utilization,
            "max_bandwidth_bps": total_bandwidth_bps,
            "utilization_percent": (self.network_utilization / total_bandwidth_bps) * 100 if total_bandwidth_bps else 0.0,
            "connections": list(self.connections.keys())
        }

    def get_performance_metrics(self) -> Dict[str, int]:
        return {
            "total_requests_processed": self.total_requests_processed,
            "total_data_transferred_bytes": self.total_data_transferred,
            "failed_transfers": self.failed_transfers,
            "current_active_transfers": len(self.active_transfers)
        }