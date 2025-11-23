import random
import socket

class NetworkCard:
    def __init__(self):
        # Generate random IP in 10.0.0.x range
        self.ip_address = f"10.0.0.{random.randint(1, 254)}"
        
        # Generate random MAC address
        self.mac_address = self._generate_mac()
        
        # Placeholder socket (can be extended later)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    def _generate_mac(self) -> str:
        """Generate a random MAC address."""
        return ":".join(f"{random.randint(0, 255):02x}" for _ in range(6))
    
    def __repr__(self):
        return f"NetworkCard(IP={self.ip_address}, MAC={self.mac_address})"