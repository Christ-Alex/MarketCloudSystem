# auth_client.py
import os
import grpc
import auth_pb2
import auth_pb2_grpc

def run():
    channel = grpc.insecure_channel('localhost:50051')
    stub = auth_pb2_grpc.AuthServiceStub(channel)

    email = input("Enter email: ").strip()
    username = input("Enter username: ").strip()
    password = input("Enter password: ").strip()

    # Register
    resp = stub.Register(auth_pb2.RegisterRequest(
        email=email,
        username=username,
        password=password
    ))
    print("Register:", resp.success, resp.message)

    # Login -> triggers OTP send
    resp = stub.Login(auth_pb2.LoginRequest(email=email, password=password))
    print("Login:", resp.success, resp.message)

    otp_code = input("Enter OTP (check console or email): ").strip()
    resp = stub.VerifyOTP(auth_pb2.OTPRequest(email=email, otp_code=otp_code))
    print("VerifyOTP:", resp.success, resp.message)

    # Upload a file (read bytes)
    filename = input("Path to file to upload (leave empty to skip): ").strip()
    if filename:
        if not os.path.exists(filename):
            print("File not found:", filename)
        else:
            with open(filename, "rb") as f:
                content = f.read()
            resp = stub.UploadFile(auth_pb2.FileUploadRequest(
                email=email,
                filename=os.path.basename(filename),
                content=content
            ))
            print("UploadFile:", resp.success, resp.message)

    # List files
    resp = stub.ListFiles(auth_pb2.ListFilesRequest(email=email))
    print("Files:")
    for f in resp.files:
        print(f" - {f.filename} ({f.size} bytes)")

if __name__ == "__main__":
    run()
