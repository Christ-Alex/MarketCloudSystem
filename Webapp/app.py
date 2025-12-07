import sys
import os

# Add PARENT folder (CloudSim root) to Python path FIRST
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

# NOW import the protobuf files
import auth_pb2, auth_pb2_grpc

import io
from datetime import timedelta
from flask import (
    Flask, render_template, request, redirect, url_for,
    send_file, flash, make_response
)
from flask import session as flask_session
import grpc


app = Flask(__name__, template_folder="templates", static_folder="static")

# Secret key for sessions
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "change_this_in_prod")
app.permanent_session_lifetime = timedelta(hours=6)

# Security headers
@app.after_request
def add_security_headers(resp):
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["X-Frame-Options"] = "DENY"
    resp.headers["X-XSS-Protection"] = "1; mode=block"
    resp.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    resp.headers["Content-Security-Policy"] = (
        "default-src 'self'; style-src 'self' 'unsafe-inline'; "
        "script-src 'self'; img-src 'self' data:"
    )
    return resp

# Connect to gRPC server
channel = grpc.insecure_channel("localhost:50051")
stub = auth_pb2_grpc.AuthServiceStub(channel)

# ---------- Utility guards ----------
def require_auth():
    email = flask_session.get("email")
    if not email:
        flash("Please log in first.", "warning")
        return redirect(url_for("home"))
    return None

def safe_redirect_to_dashboard():
    return redirect(url_for("dashboard", email=flask_session.get("email")))

# ---------- Routes ----------
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/register", methods=["POST"])
def register():
    email = request.form.get("email")
    password = request.form.get("password")
    if not email or not password:
        return "Missing email or password", 400
    try:
        response = stub.Register(auth_pb2.RegisterRequest(email=email, password=password))
    except grpc.RpcError as e:
        return f"Registration failed: {e.details()}", 502
    if response.success:
        flask_session["pending_email"] = email
        return redirect(url_for("otp"))
    return f"Registration failed: {response.message}", 400

@app.route("/login", methods=["POST"])
def login():
    email = request.form.get("email")
    password = request.form.get("password")
    if not email or not password:
        return "Missing email or password", 400
    try:
        response = stub.Login(auth_pb2.LoginRequest(email=email, password=password))
    except grpc.RpcError as e:
        return f"Login failed: {e.details()}", 502
    if response.success:
        flask_session["pending_email"] = email
        return redirect(url_for("otp"))
    return f"Login failed: {response.message}", 401

@app.route("/otp", methods=["GET", "POST"])
def otp():
    pending_email = flask_session.get("pending_email")
    if not pending_email:
        flash("Session expired. Please log in again.", "warning")
        return redirect(url_for("home"))

    if request.method == "POST":
        code = request.form.get("otp")
        if not code:
            return "Missing OTP code", 400
        try:
            response = stub.VerifyOTP(auth_pb2.OTPRequest(email=pending_email, otp_code=code))
        except grpc.RpcError as e:
            return f"OTP failed: {e.details()}", 502
        if response.success:
            flask_session.permanent = True
            flask_session["email"] = pending_email
            flask_session.pop("pending_email", None)
            return redirect(url_for("dashboard", email=pending_email))
        return f"OTP failed: {response.message}", 401

    return render_template("otp.html", email=pending_email)

@app.route("/dashboard")
def dashboard():
    if not flask_session.get("email"):
        email_param = request.args.get("email")
        if not email_param:
            return redirect(url_for("home"))
        flask_session["email"] = email_param

    email = flask_session.get("email")

    # Fetch file list
    try:
        response = stub.ListFiles(auth_pb2.ListFilesRequest(email=email))
    except grpc.RpcError as e:
        return f"Failed to list files: {e.details()}", 502

    file_list = list(response.files) if response and response.files else []

    # Fetch quota
    try:
        quota = stub.GetQuota(auth_pb2.QuotaRequest(email=email))
        used_bytes = quota.used_bytes
        total_bytes = quota.total_bytes
    except grpc.RpcError:
        used_bytes = 0
        total_bytes = 5 * 1024 * 1024 * 1024

    percent_used = int((used_bytes / total_bytes) * 100) if total_bytes else 0

    return render_template(
        "dashboard.html",
        email=email,
        files=file_list,
        used=used_bytes,
        total=total_bytes,
        percent=percent_used
    )

@app.route("/upload", methods=["POST"])
def upload():
    if require_auth():
        return require_auth()
    email = flask_session.get("email")

    file = request.files.get("file")
    if not file or file.filename.strip() == "":
        flash("No file selected.", "danger")
        return safe_redirect_to_dashboard()

    filename = file.filename
    content = file.read()
    if len(content) == 0:
        flash("The selected file is empty.", "warning")
        return safe_redirect_to_dashboard()

    try:
        response = stub.UploadFile(auth_pb2.FileUploadRequest(
            email=email,
            filename=filename,
            content=content
        ))
    except grpc.RpcError as e:
        flash(f"Upload failed: {e.details()}", "danger")
        return safe_redirect_to_dashboard()

    if getattr(response, "success", False):
        flash(f"Uploaded {filename}", "success")
    else:
        flash(f"Upload failed: {getattr(response, 'message', 'Unknown error')}", "danger")

    return safe_redirect_to_dashboard()

@app.route("/download/<path:filename>", methods=["GET"])
def download(filename):
    if require_auth():
        return require_auth()
    email = flask_session.get("email")

    try:
        response = stub.DownloadFile(auth_pb2.FileDownloadRequest(
            email=email,
            filename=filename
        ))
    except grpc.RpcError as e:
        return f"Download failed: {e.details()}", 502

    content = getattr(response, "content", None)
    if content is None or len(content) == 0:
        return "File not found or empty content", 404

    return send_file(
        io.BytesIO(content),
        as_attachment=True,
        download_name=os.path.basename(filename)
    )

@app.route("/delete/<path:filename>", methods=["POST"])
def delete(filename):
    if require_auth():
        return require_auth()
    email = flask_session.get("email")

    try:
        response = stub.DeleteFile(auth_pb2.FileDeleteRequest(
            email=email,
            filename=filename
        ))
    except grpc.RpcError as e:
        flash(f"Delete failed: {e.details()}", "danger")
        return safe_redirect_to_dashboard()

    if getattr(response, "success", False):
        flash(f"Deleted {filename}", "success")
    else:
        flash(f"Delete failed: {getattr(response, 'message', 'Unknown error')}", "danger")

    return safe_redirect_to_dashboard()

@app.route("/logout", methods=["POST"])
def logout():
    flask_session.clear()
    flash("You’ve been logged out.", "info")
    return redirect(url_for("home"))

# ---------- Error handlers ----------
@app.errorhandler(405)
def method_not_allowed(e):
    return make_response("Method Not Allowed", 405)

@app.errorhandler(404)
def not_found(e):
    return make_response("Not Found", 404)

@app.errorhandler(500)
def server_error(e):
    return make_response("Something went wrong. Please try again.", 500)

# ---------- HTTPS local dev ----------
if __name__ == "__main__":
    app.run(debug=True, ssl_context="adhoc")