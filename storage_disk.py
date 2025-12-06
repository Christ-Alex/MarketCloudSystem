import os

class StorageDisk:
    def __init__(self, disk_size_mb: int, disk_type: str, mount_path: str):
        """
        Simulates a virtual disk for a node.
        :param disk_size_mb: Size of the disk in MB
        :param disk_type: Type of disk (SSD, HDD, USB, etc.)
        :param mount_path: Folder path on host machine to represent this disk
        """
        self.disk_size_bytes = disk_size_mb * 1024 * 1024
        self.disk_type = disk_type
        self.mount_path = mount_path

        # Ensure the folder exists
        os.makedirs(self.mount_path, exist_ok=True)

    def get_used_space(self) -> int:
        """Calculate used space in bytes by summing file sizes in mount_path."""
        total = 0
        for root, _, files in os.walk(self.mount_path):
            for f in files:
                total += os.path.getsize(os.path.join(root, f))
        return total

    def get_free_space(self) -> int:
        """Return free space in bytes."""
        return self.disk_size_bytes - self.get_used_space()

    def utilization_percent(self) -> float:
        """Return percentage of disk utilization."""
        if self.disk_size_bytes == 0:
            return 0.0
        return (self.get_used_space() / self.disk_size_bytes) * 100

    def store_file(self, file_name: str, data: bytes) -> bool:
        """
        Store a file if there is enough free space.
        :param file_name: Name of the file to store
        :param data: File contents as bytes
        :return: True if stored successfully, False if not enough space
        """
        if len(data) > self.get_free_space():
            print(f"❌ Not enough space on {self.disk_type} disk at {self.mount_path}")
            return False

        path = os.path.join(self.mount_path, file_name)
        with open(path, "wb") as f:
            f.write(data)
        return True

    def retrieve_file(self, file_name: str) -> bytes | None:
        """
        Retrieve a file if it exists.
        :param file_name: Name of the file to retrieve
        :return: File contents as bytes, or None if not found
        """
        path = os.path.join(self.mount_path, file_name)
        if os.path.exists(path):
            with open(path, "rb") as f:
                return f.read()
        return None


# ---------- Quick test block ----------
if __name__ == "__main__":
    # Create a test disk of 10 MB
    disk = StorageDisk(disk_size_mb=10, disk_type="SSD", mount_path="./test_disk")

    print("Total size (bytes):", disk.disk_size_bytes)
    print("Used space (bytes):", disk.get_used_space())
    print("Free space (bytes):", disk.get_free_space())
    print("Utilization (%):", disk.utilization_percent())

    # Store a small file
    data = b"Hello Ngondi!" * 100
    disk.store_file("hello.txt", data)
    print("After storing file:")
    print("Used space (bytes):", disk.get_used_space())
    print("Utilization (%):", disk.utilization_percent())