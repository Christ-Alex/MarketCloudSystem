import grpc
import auth_pb2
import auth_pb2_grpc

def run():
    # Connect to gRPC server
    channel = grpc.insecure_channel('localhost:50051')
    stub = auth_pb2_grpc.AuthServiceStub(channel)

    # Prompt for user input
    email = input("Enter email: ")
    username = input("Enter username: ")
    password = input("Enter password: ")

    # Register
    response = stub.Register(auth_pb2.RegisterRequest(
        email=email,
        username=username,
        password=password
    ))
    print("Register:", response.success, response.message)

    # Login
    response = stub.Login(auth_pb2.LoginRequest(
        email=email,
        password=password
    ))
    print("Login:", response.success, response.message)

    # Verify OTP (currently hardcoded in server as "123456")
    otp_code = input("Enter OTP (default 123456): ") or "123456"
    response = stub.VerifyOTP(auth_pb2.OTPRequest(
        email=email,
        otp_code=otp_code
    ))
    print("VerifyOTP:", response.success, response.message)

    # Upload File
    filename = input("Enter filename to upload (e.g. report.pdf): ")
    filesize = int(input("Enter file size in bytes (e.g. 204800): "))
    response = stub.UploadFile(auth_pb2.FileUploadRequest(
        email=email,
        filename=filename,
        filesize=filesize
    ))
    print("UploadFile:", response.success, response.message)

    # List Files
    response = stub.ListFiles(auth_pb2.ListFilesRequest(
        email=email
    ))
    print("ListFiles:", response.filenames)

if __name__ == "__main__":
    run()