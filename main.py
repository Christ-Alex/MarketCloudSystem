import time
from storage_virtual_network import StorageVirtualNetwork
from storage_virtual_node import StorageVirtualNode

# Create network
network = StorageVirtualNetwork()

# Create nodes
node1 = StorageVirtualNode("node1", ip_address="10.0.0.1",cpu_capacity=4, memory_capacity=16,storage_capacity=500, bandwidth=1000)
                           
node2 = StorageVirtualNode("node2", ip_address="10.0.0.2",cpu_capacity=8, memory_capacity=32,storage_capacity=1000, bandwidth=2000)

node3 = StorageVirtualNode("node3", ip_address="10.0.0.3",cpu_capacity=4, memory_capacity=16,storage_capacity=500, bandwidth=1000)

node4 = StorageVirtualNode("node4", ip_address="10.0.0.4",cpu_capacity=8, memory_capacity=32,storage_capacity=1000, bandwidth=2000)

# Add nodes to network
network.add_node(node1)
network.add_node(node2)
network.add_node(node3)
network.add_node(node4)

# Start autonomous threads for each node
node1.start()
node2.start()
node3.start()
node4.start()

# Connect nodes with links
network.connect_nodes("node1", "node2", bandwidth=1000)
network.connect_nodes("node1", "node3", bandwidth=2000)
network.connect_nodes("node2", "node4", bandwidth=1000)
network.connect_nodes("node3", "node4", bandwidth=2000)

# Initiate file transfer (100MB file from node1 to node4)
transfer = network.initiate_file_transfer(
    source_node_id="node1",
    target_node_id="node4",
    file_name="large_dataset.zip",
    file_size=100 * 1024 * 1024  # 100MB
)

if transfer:
    print(f"Transfer initiated: {transfer.file_id}")

    try:
        # Process transfer in chunks
        while True:
            chunks_done, completed = network.process_file_transfer(
                source_node_id="node1",
                target_node_id="node4",
                file_id=transfer.file_id,
                chunks_per_step=3  # Process 3 chunks at a time
            )

            print(f"Transferred {chunks_done} chunks, completed: {completed}")

            if completed:
                print("Transfer completed successfully!")
                break

            # Get network stats
            stats = network.get_network_stats()
            print(f"Network utilization: {stats['bandwidth_utilization']:.2f}%")
            print(f"Storage utilization on node4: {node4.get_storage_utilization()['utilization_percent']:.2f}%")

            time.sleep(1)  # small delay for readability

    finally:
        # Graceful shutdown of threads
        node1.stop()
        node2.stop()
        node3.stop()
        node4.stop()