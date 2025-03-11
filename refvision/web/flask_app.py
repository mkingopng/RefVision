# refvision/web/flask_app.py
"""
Flask Application for Playing Contested Lifts
This Flask application serves as a simple interface to authenticate users and
stream a pre-signed video file from AWS S3. It provides:
1. Simple username/password authentication (for proof-of-concept only).
2. A pre-signed URL generation to securely stream videos from S3.
3. Routes for login, logout, and video display.
This application serves as both the user-facing interface (login, video replay)
and the inference API (for cloud deployments).
It uses the FLASK_PORT from config/config.py.
"""
import os
import sys
import boto3
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    jsonify,
)
from dotenv import load_dotenv
from config.config import CFG
from refvision.inference.model_loader import load_model
from refvision.inference.depth_evaluator import evaluate_depth
from refvision.utils.logging_setup import setup_logging

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
load_dotenv()

BASE_DIR = os.path.dirname(__file__)  # This is refvision/web/
TEMPLATE_DIR = os.path.join(
    BASE_DIR, "templates"
)  # ...which is refvision/web/templates/

app = Flask(__name__, template_folder=TEMPLATE_DIR)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "my-super-secret-flask-key")


def create_s3_presigned_url(
    bucket_name: str, object_name: str, expiration: int = 3600
) -> str:
    """
    Generate a presigned URL for an S3 object.
    :param bucket_name:
    :param object_name:
    :param expiration:
    :return:
    """
    s3_client = boto3.client(
        "s3",
        aws_access_key_id=CFG.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=CFG.AWS_SECRET_ACCESS_KEY,
        region_name=CFG.AWS_REGION,
    )
    try:
        response = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket_name, "Key": object_name},
            ExpiresIn=expiration,
        )
        return response
    except Exception as e:
        print(f"Could not generate presigned URL: {e}")
        return ""


def is_authenticated() -> bool:
    """
    Simple check for authentication
    :return: bool
    """
    return session.get("logged_in", False)


def do_auth(username: str, password: str) -> bool:
    """
    authenticate user credentials.
    :param username: (str) Input username.
    :param password: (str) Input password.
    :return: bool: True if authentication is successful, False otherwise.
    """
    return username == CFG.USERNAME and password == CFG.PASSWORD


@app.route("/")
def home():
    """
    Redirect users to login if not authenticated, else show video page
    :return: None
    """
    if not is_authenticated():
        return redirect(url_for("login"))
    return redirect(url_for("show_video"))


@app.route("/login", methods=["GET", "POST"])
def login():
    """
    Handle user authentication via a simple login form.
    Supports GET (display login page) and POST (validate credentials).
    :return: None
    """
    if request.method == "POST":
        user = request.form["username"]
        pwd = request.form["password"]
        if do_auth(user, pwd):
            session["logged_in"] = True
            flash("Logged in successfully!", "success")
            return redirect(url_for("show_video"))
        else:
            flash("Invalid credentials", "error")
            return redirect(url_for("login"))
    return render_template("login.html")


@app.route("/logout")
def logout():
    """
    Log out the user and redirect to the login page
    :return: None
    """
    session.clear()
    flash("Logged out successfully", "info")
    return redirect(url_for("login"))


@app.route("/video")
def show_video():
    """
    Display the video player with a pre-signed S3 URL.
    If the user is not authenticated, redirect to login.
    If S3 URL generation fails, show an error message.
    :return: video
    """
    if not is_authenticated():
        return redirect(url_for("login"))

    presigned_url = create_s3_presigned_url(CFG.S3_BUCKET, CFG.VIDEO_KEY)
    print(f"Generated Pre-Signed URL: {presigned_url}")  # Add this line

    decision = None  # todo: add coordinates for decision here
    if os.path.exists("../../tmp/decision.txt"):
        with open("../../tmp/decision.txt") as f:
            decision = f.read().strip()

    if not presigned_url:
        flash(
            "Error: Video file not found in S3 or presigned URL generation failed.",
            "error",
        )

        return render_template("video.html", presigned_url=None, decision=decision)

    return render_template("video.html", presigned_url=presigned_url, decision=decision)


# ----- Inference Endpoints (for Cloud Use) -----
# todo: These endpoints (e.g. /ping, /invocations) are intended for cloud deployments.
# Global variables to cache the model once loaded.
model = None
device = None
logger = setup_logging(os.path.join(os.path.dirname(__file__), "../logs/yolo_logs.log"))


def initialize_model(model_path: str):
    """
    Load the model and device once and cache them.
    :param model_path:
    :return:
    """
    global model, device
    if model is None:
        logger.info(f"Loading model from {model_path}")
        model, device = load_model(model_path)
    return model, device


@app.route("/ping", methods=["GET"])
def ping():
    return "", 200


@app.route("/invocations", methods=["POST"])
def invocations():
    data = request.get_json(force=True)
    video_path = data.get("video_path")
    model_path = data.get("model_path", os.environ.get("MODEL_S3_PATH"))
    if not video_path or not model_path:
        return jsonify({"error": "Missing video_path or model_path"}), 400
    m, d = initialize_model(model_path)
    # Assume that the model has a method track for inference.
    results = m.track(source=video_path, device=d, show=False, save=True, max_det=1)
    decision = evaluate_depth(results, video_path)
    return jsonify({"decision": decision})


if __name__ == "__main__":
    port = CFG.FLASK_PORT
    app.run(host="0.0.0.0", port=port, debug=True)
