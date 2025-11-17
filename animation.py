# animation.py
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import networkx as nx
from collections import deque
from typing import Dict, List

class NetworkAnimator:
    def __init__(self, nodes: Dict[str, object], connections: List[tuple], frames_per_hop: int = 30, interval_ms: int = 40):
        """
        nodes: dict node_id -> node_obj (node_obj should expose .ip or .ip_address)
        connections: list of (node1, node2)
        """
        self.nodes = nodes
        self.connections = connections
        self.frames_per_hop = int(frames_per_hop)
        self.interval_ms = int(interval_ms)

        # Build graph
        self.G = nx.Graph()
        for nid in nodes.keys():
            self.G.add_node(nid)
        for a, b in connections:
            self.G.add_edge(a, b)

        # Layout once
        self.pos = nx.spring_layout(self.G, seed=7)

        # Figure
        self.fig, self.ax = plt.subplots(figsize=(8, 6))
        self.ax.set_axis_off()

        # Draw static elements
        nx.draw_networkx_edges(self.G, self.pos, ax=self.ax, width=2)
        labels = {}
        for nid in self.G.nodes():
            node_obj = self.nodes.get(nid)
            ip = getattr(node_obj, "ip", None) or getattr(node_obj, "ip_address", None) or ""
            labels[nid] = f"{nid}\n{ip}"
        nx.draw_networkx_nodes(self.G, self.pos, node_size=700, ax=self.ax)
        nx.draw_networkx_labels(self.G, self.pos, labels=labels, ax=self.ax, font_size=9)

        # Active markers and queue
        self.active_markers = []   # each: dict with 'path', 'step', 'artist'
        self._enqueue = deque()

        # Start a single FuncAnimation to update all markers
        self.ani = animation.FuncAnimation(self.fig, self._update_frame, interval=self.interval_ms, blit=True)

    def _compute_path_positions(self, hop_nodes: List[str]):
        positions = []
        for i in range(len(hop_nodes) - 1):
            n1 = hop_nodes[i]
            n2 = hop_nodes[i + 1]
            x1, y1 = self.pos[n1]
            x2, y2 = self.pos[n2]
            for t in range(self.frames_per_hop + 1):
                a = t / float(self.frames_per_hop)
                x = x1 + (x2 - x1) * a
                y = y1 + (y2 - y1) * a
                positions.append((x, y))
        return positions

    def animate_route_nonblocking(self, hop_nodes: List[str], color='red', size=50):
        """Enqueue a moving marker that will follow hop_nodes (list). Returns marker object."""
        if not hop_nodes or len(hop_nodes) < 2:
            return None
        path = self._compute_path_positions(hop_nodes)
        artist, = self.ax.plot([], [], marker='o', linestyle='', markersize=max(4, size/10), color=color, zorder=10)
        marker = {'path': path, 'step': 0, 'artist': artist}
        self._enqueue.append(marker)
        return marker

    def _update_frame(self, frame):
        changed = []

        # move queued markers to active
        while self._enqueue:
            m = self._enqueue.popleft()
            self.active_markers.append(m)
            changed.append(m['artist'])

        # update active markers
        still_active = []
        for m in self.active_markers:
            if m['step'] < len(m['path']):
                x, y = m['path'][m['step']]
                m['artist'].set_data([x], [y])
                m['step'] += 1
                still_active.append(m)
                changed.append(m['artist'])
            else:
                m['artist'].set_data([], [])

        self.active_markers = still_active
        if not changed:
            return tuple()
        return tuple(changed)

    def start(self, block: bool = False):
        """Show the animation window. block=False tries to show non-blocking (depends on backend)."""
        try:
            plt.show(block=block)
        except TypeError:
            plt.show()

    def stop(self):
        plt.close(self.fig)
