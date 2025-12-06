from sqlalchemy import (
    Column, Integer, String, BigInteger, ForeignKey,
    TIMESTAMP, DateTime, create_engine
)
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from datetime import datetime

# Database connection string
DATABASE_URL = "mysql+pymysql://root:01234@localhost/alexcloud_dist"

# Engine and session
engine = create_engine(DATABASE_URL, echo=True, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

# Base class for models
Base = declarative_base()


# ------------------ MODELS ------------------

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(191), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)

    quota_bytes = Column(BigInteger, nullable=False, default=5 * 1024 * 1024 * 1024)  # 5GB default
    used_bytes = Column(BigInteger, default=0)

    otp = Column(String(10))
    otp_expiry = Column(DateTime)

    # Relationships
    files = relationship("File", back_populates="owner", cascade="all, delete-orphan")
    transfers = relationship("Transfer", back_populates="user", cascade="all, delete-orphan")


class File(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    filename = Column(String(255), nullable=False)
    size_bytes = Column(BigInteger, nullable=False)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

    # Relationships
    owner = relationship("User", back_populates="files")
    chunks = relationship("Chunk", back_populates="file", cascade="all, delete-orphan")
    transfers = relationship("Transfer", back_populates="file", cascade="all, delete-orphan")


class Chunk(Base):
    __tablename__ = "chunks"

    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey("files.id", ondelete="CASCADE"))
    chunk_index = Column(Integer)
    size_bytes = Column(BigInteger)
    node_id = Column(Integer)  # reference to Node.id
    checksum = Column(String(64))

    # Relationships
    file = relationship("File", back_populates="chunks")
    events = relationship("TransferEvent", back_populates="chunk", cascade="all, delete-orphan")


class Node(Base):
    __tablename__ = "nodes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True)
    capacity_bytes = Column(BigInteger)
    used_bytes = Column(BigInteger, default=0)
    status = Column(String(20))


class Transfer(Base):
    __tablename__ = "transfers"

    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey("files.id", ondelete="CASCADE"))
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))

    total_chunks = Column(Integer)
    total_bytes = Column(BigInteger)
    total_hops = Column(Integer)
    duration_ms = Column(Integer)
    status = Column(String(20))

    # Relationships
    file = relationship("File", back_populates="transfers")
    user = relationship("User", back_populates="transfers")
    events = relationship("TransferEvent", back_populates="transfer", cascade="all, delete-orphan")


class TransferEvent(Base):
    __tablename__ = "transfer_events"

    id = Column(Integer, primary_key=True, index=True)
    transfer_id = Column(Integer, ForeignKey("transfers.id", ondelete="CASCADE"))
    chunk_id = Column(Integer, ForeignKey("chunks.id", ondelete="CASCADE"))

    from_node = Column(Integer)  # Node.id
    to_node = Column(Integer)    # Node.id
    hop_index = Column(Integer)
    latency_ms = Column(Integer)
    status = Column(String(20))

    # Relationships
    transfer = relationship("Transfer", back_populates="events")
    chunk = relationship("Chunk", back_populates="events")


# ------------------ UTILITIES ------------------

def init_db():
    """Create all tables in the database."""
    Base.metadata.create_all(bind=engine)