# auth_server.py
import os
import grpc
import logging
import hashlib
from concurrent import futures
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from werkzeug.utils import secure_filename

import auth_pb2
import auth_pb2_grpc

# Project-local imports (your models & utility helpers)
from models import SessionLocal, User, File, Chunk  # ensure these are correct
from utils import hash_password, check_password, generate_otp, send_otp

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("auth_server")

STORAGE_DIR = "storage"
os.makedirs(STORAGE_DIR, exist_ok=True)


class AuthService(auth_pb2_grpc.AuthServiceServicer):
    def Register(self, request, context):
        db: Session = SessionLocal()
        try:
            existing = db.query(User).filter(User.email == request.email).first()
            if existing:
                return auth_pb2.RegisterResponse(success=False, message="User already exists", quota_bytes=0)

            hashed_pw = hash_password(request.password)
            quota = 5 * 1024 * 1024 * 1024  # 5GB

            otp = generate_otp()
            otp_expiry = datetime.utcnow() + timedelta(minutes=5)

            user = User(
                email=request.email,
                password_hash=hashed_pw,
                quota_bytes=quota,
                used_bytes=0,
                otp=otp,
                otp_expiry=otp_expiry
            )

            # If your User model has a username column and proto provided username
            if hasattr(user, "username") and getattr(request, "username", ""):
                user.username = request.username

            db.add(user)
            db.commit()

            # send OTP after commit (so user row exists)
            try:
                send_otp(user.email, otp)
            except Exception:
                logger.exception("Failed to send OTP email; continuing (user registered)")

            return auth_pb2.RegisterResponse(
                success=True,
                message="User registered. OTP sent to email.",
                quota_bytes=quota
            )
        except Exception:
            logger.exception("Register failed")
            db.rollback()
            return auth_pb2.RegisterResponse(success=False, message="Internal server error", quota_bytes=0)
        finally:
            db.close()

    def Login(self, request, context):
        db: Session = SessionLocal()
        try:
            user = db.query(User).filter(User.email == request.email).first()
            if not user:
                return auth_pb2.LoginResponse(success=False, message="User not found")

            if not check_password(request.password, user.password_hash):
                return auth_pb2.LoginResponse(success=False, message="Invalid credentials")

            otp = generate_otp()
            user.otp = otp
            user.otp_expiry = datetime.utcnow() + timedelta(minutes=5)
            db.commit()

            try:
                send_otp(user.email, otp)
            except Exception:
                logger.exception("Failed to send OTP after login; continuing")

            return auth_pb2.LoginResponse(success=True, message="OTP sent to email")
        except Exception:
            logger.exception("Login failed")
            db.rollback()
            return auth_pb2.LoginResponse(success=False, message="Internal server error")
        finally:
            db.close()

    def VerifyOTP(self, request, context):
        db: Session = SessionLocal()
        try:
            user = db.query(User).filter(User.email == request.email).first()
            if not user or not user.otp:
                return auth_pb2.OTPResponse(success=False, message="OTP not found; login first")

            if user.otp != request.otp_code:
                return auth_pb2.OTPResponse(success=False, message="Invalid OTP")

            if not user.otp_expiry or user.otp_expiry < datetime.utcnow():
                return auth_pb2.OTPResponse(success=False, message="OTP expired")

            user.otp = None
            user.otp_expiry = None
            db.commit()

            return auth_pb2.OTPResponse(success=True, message="Authentication successful")
        except Exception:
            logger.exception("VerifyOTP failed")
            db.rollback()
            return auth_pb2.OTPResponse(success=False, message="Internal server error")
        finally:
            db.close()

    def UploadFile(self, request, context):
        db: Session = SessionLocal()
        try:
            user = db.query(User).filter(User.email == request.email).first()
            if not user:
                return auth_pb2.FileUploadResponse(success=False, message="User not found")

            safe_name = secure_filename(request.filename)
            if not safe_name:
                return auth_pb2.FileUploadResponse(success=False, message="Invalid filename")

            user_dir = os.path.join(STORAGE_DIR, request.email)
            os.makedirs(user_dir, exist_ok=True)
            filepath = os.path.join(user_dir, safe_name)

            content_size = len(request.content)

            # Handle overwrite case (determine delta to compute quota usage)
            existing_file = db.query(File).filter(
                File.owner_id == user.id,
                File.filename == safe_name
            ).first()
            old_size = existing_file.size_bytes if existing_file else 0
            delta = content_size - old_size

            # Quota check
            if user.used_bytes + delta > user.quota_bytes:
                return auth_pb2.FileUploadResponse(success=False, message="Quota exceeded")

            # Write file bytes to disk (atomic write pattern)
            tmp_path = filepath + ".uploading"
            with open(tmp_path, "wb") as f:
                f.write(request.content)
            os.replace(tmp_path, filepath)  # atomic on most OSes

            # Upsert file metadata
            if existing_file:
                existing_file.size_bytes = content_size
                file_row = existing_file
            else:
                file_row = File(owner_id=user.id, filename=safe_name, size_bytes=content_size)
                db.add(file_row)
                # ensure we get an id for the new file when inserting related chunk rows
                db.flush()

            # Update user quota usage
            user.used_bytes += delta

            # Upsert chunk metadata (simple single-chunk model here)
            checksum = hashlib.sha256(request.content).hexdigest()
            # If file_row.id might be None for some reason, flush handled above for new rows.
            chunk = db.query(Chunk).filter(
                Chunk.file_id == file_row.id,
                Chunk.chunk_index == 0
            ).first()
            if chunk:
                chunk.size_bytes = content_size
                chunk.checksum = checksum
            else:
                # choose a node id heuristically (placeholder). Later integrate real node selection.
                db.add(Chunk(
                    file_id=file_row.id,
                    chunk_index=0,
                    size_bytes=content_size,
                    node_id=1,
                    checksum=checksum
                ))

            db.commit()
            return auth_pb2.FileUploadResponse(success=True, message="File uploaded")
        except Exception:
            logger.exception("UploadFile failed")
            db.rollback()
            return auth_pb2.FileUploadResponse(success=False, message="Internal server error")
        finally:
            db.close()

    def DownloadFile(self, request, context):
        try:
            safe_name = secure_filename(request.filename)
            if not safe_name:
                return auth_pb2.FileDownloadResponse(content=b"", message="Invalid filename")

            user_dir = os.path.join(STORAGE_DIR, request.email)
            filepath = os.path.join(user_dir, safe_name)
            if not os.path.exists(filepath):
                return auth_pb2.FileDownloadResponse(content=b"", message="File not found")

            with open(filepath, "rb") as f:
                content = f.read()
            return auth_pb2.FileDownloadResponse(content=content, message="File downloaded")
        except Exception:
            logger.exception("DownloadFile failed")
            return auth_pb2.FileDownloadResponse(content=b"", message="Internal server error")

    def DeleteFile(self, request, context):
        db: Session = SessionLocal()
        try:
            user = db.query(User).filter(User.email == request.email).first()
            if not user:
                return auth_pb2.FileDeleteResponse(success=False, message="User not found")

            safe_name = secure_filename(request.filename)
            if not safe_name:
                return auth_pb2.FileDeleteResponse(success=False, message="Invalid filename")

            file = db.query(File).filter(
                File.owner_id == user.id,
                File.filename == safe_name
            ).first()
            if not file:
                return auth_pb2.FileDeleteResponse(success=False, message="File not found")

            # Delete file bytes on disk
            user_dir = os.path.join(STORAGE_DIR, request.email)
            filepath = os.path.join(user_dir, safe_name)
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                except Exception:
                    logger.exception("Failed to remove file from disk")

            # Remove chunk metadata for this file
            db.query(Chunk).filter(Chunk.file_id == file.id).delete()

            # Update quota and delete file row
            user.used_bytes = max(0, user.used_bytes - file.size_bytes)
            db.delete(file)

            db.commit()
            return auth_pb2.FileDeleteResponse(success=True, message="File deleted")
        except Exception:
            logger.exception("DeleteFile failed")
            db.rollback()
            return auth_pb2.FileDeleteResponse(success=False, message="Internal server error")
        finally:
            db.close()

    def ListFiles(self, request, context):
        db: Session = SessionLocal()
        try:
            user = db.query(User).filter(User.email == request.email).first()
            if not user:
                return auth_pb2.ListFilesResponse(files=[])

            file_records = db.query(File).filter(File.owner_id == user.id).all()
            file_infos = [auth_pb2.FileInfo(filename=f.filename, size=f.size_bytes) for f in file_records]
            return auth_pb2.ListFilesResponse(files=file_infos)
        except Exception:
            logger.exception("ListFiles failed")
            return auth_pb2.ListFilesResponse(files=[])
        finally:
            db.close()

    def GetQuota(self, request, context):
        db: Session = SessionLocal()
        try:
            user = db.query(User).filter(User.email == request.email).first()
            if not user:
                return auth_pb2.QuotaResponse(used_bytes=0, total_bytes=0)
            return auth_pb2.QuotaResponse(used_bytes=user.used_bytes, total_bytes=user.quota_bytes)
        except Exception:
            logger.exception("GetQuota failed")
            return auth_pb2.QuotaResponse(used_bytes=0, total_bytes=0)
        finally:
            db.close()


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    auth_pb2_grpc.add_AuthServiceServicer_to_server(AuthService(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    logger.info("Server started on port 50051")
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
