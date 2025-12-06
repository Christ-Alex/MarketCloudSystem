import matplotlib.pyplot as plt
import matplotlib.animation as animation
import networkx as nx # type: ignore

class NetworkAnimator:
    def __init__(self, nodes, connections):
        """
        nodes: dict {node_id -> StorageVirtualNode}
        connections: list of (node1, node2)
        """
        self.nodes = nodes
        self.connections = connections

        self.G = nx.Graph()
        for node in nodes:
            self.G.add_node(node)
        for a, b in connections:
            self.G.add_edge(a, b)

        # Fix positions for the graph
        self.pos = nx.spring_layout(self.G, seed=7)

        # Matplotlib figure
        self.fig, self.ax = plt.subplots(figsize=(7, 6))

        nx.draw_networkx_edges(self.G, self.pos, ax=self.ax, width=2)
        nx.draw_networkx_labels(self.G, self.pos, ax=self.ax, font_size=10)

        # Moving chunk dot
        self.chunk_dot, = self.ax.plot([], [], 'ro', markersize=10)

        # Multi-hop positions
        self.full_path = []
        self.step = 0

    def compute_path(self, source, target):
        """Compute the route (multi-hop path)"""
        try:
            hop_nodes = nx.shortest_path(self.G, source, target)
        except:
            print("No route found between nodes.")
            return []

        positions = []
        for i in range(len(hop_nodes) - 1):
            x1, y1 = self.pos[hop_nodes[i]]
            x2, y2 = self.pos[hop_nodes[i+1]]

            # 30 animation frames per hop
            for t in range(31):
                x = x1 + (x2 - x1) * (t / 30)
                y = y1 + (y2 - y1) * (t / 30)
                positions.append((x, y))

        return positions

    def update_frame(self, frame):
        if self.step < len(self.full_path):
            x, y = self.full_path[self.step]
            self.chunk_dot.set_data([x], [y])
            self.step += 1
        return self.chunk_dot,

    def animate_chunk(self, source, target):
        """Animate one chunk moving from source → target"""
        self.full_path = self.compute_path(source, target)
        self.step = 0

        ani = animation.FuncAnimation(
            self.fig,
            self.update_frame,
            frames=len(self.full_path),
            interval=40,
            blit=True,
            repeat=False
        )

        plt.title(f"Chunk Transfer: {source} → {target}")
        plt.show()
