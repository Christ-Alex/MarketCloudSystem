import grpc
from concurrent import futures
import auth_pb2
import auth_pb2_grpc

import firebase_admin
from firebase_admin import credentials, auth, firestore

# Initialize Firebase
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

class AuthService(auth_pb2_grpc.AuthServiceServicer):
    def Register(self, request, context):
        try:
            user = auth.create_user(
                email=request.email,
                password=request.password,
                display_name=request.username
            )
            quota = 5 * 1024 * 1024 * 1024  # 5GB
            db.collection("users").document(user.uid).set({
                "email": request.email,
                "username": request.username,
                "quota_bytes": quota,
                "used_bytes": 0,
                "otp": ""
            })
            return auth_pb2.RegisterResponse(success=True, message="User registered", quota_bytes=quota)
        except Exception as e:
            return auth_pb2.RegisterResponse(success=False, message=str(e), quota_bytes=0)

    def Login(self, request, context):
        try:
            otp = "123456"  # TODO: generate random OTP + send via email/SMS
            user = auth.get_user_by_email(request.email)
            db.collection("users").document(user.uid).update({"otp": otp})
            return auth_pb2.LoginResponse(success=True, message="OTP sent")
        except Exception as e:
            return auth_pb2.LoginResponse(success=False, message=str(e))

    def VerifyOTP(self, request, context):
        try:
            user = auth.get_user_by_email(request.email)
            doc = db.collection("users").document(user.uid).get()
            if doc.exists and doc.to_dict().get("otp") == request.otp_code:
                return auth_pb2.OTPResponse(success=True, message="Authentication successful")
            return auth_pb2.OTPResponse(success=False, message="Invalid OTP")
        except Exception as e:
            return auth_pb2.OTPResponse(success=False, message=str(e))

    def UploadFile(self, request, context):
        try:
            user = auth.get_user_by_email(request.email)
            doc_ref = db.collection("users").document(user.uid)
            doc = doc_ref.get()
            if not doc.exists:
                return auth_pb2.FileUploadResponse(success=False, message="User not found")

            data = doc.to_dict()
            if data["used_bytes"] + request.filesize > data["quota_bytes"]:
                return auth_pb2.FileUploadResponse(success=False, message="Quota exceeded")

            doc_ref.update({"used_bytes": data["used_bytes"] + request.filesize})
            db.collection("files").add({
                "owner_uid": user.uid,
                "filename": request.filename,
                "filesize": request.filesize,
                "storage_nodes": ["nodeA", "nodeB"]
            })
            return auth_pb2.FileUploadResponse(success=True, message="File uploaded")
        except Exception as e:
            return auth_pb2.FileUploadResponse(success=False, message=str(e))

    def ListFiles(self, request, context):
        try:
            user = auth.get_user_by_email(request.email)
            files = db.collection("files").where("owner_uid", "==", user.uid).stream()
            filenames = [f.to_dict()["filename"] for f in files]
            return auth_pb2.ListFilesResponse(filenames=filenames)
        except Exception as e:
            return auth_pb2.ListFilesResponse(filenames=[])

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    auth_pb2_grpc.add_AuthServiceServicer_to_server(AuthService(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print("Server started on port 50051")
    server.wait_for_termination()

if __name__ == "__main__":
    serve()