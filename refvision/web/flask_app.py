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
from refvision.common.config import get_config
from refvision.inference.model_loader import load_model
from refvision.utils.logging_setup import setup_logging
from refvision.dynamo_db.dynamodb_helpers import get_item

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
load_dotenv()

cfg = get_config()

BASE_DIR = os.path.dirname(__file__)  # This is refvision/web/
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")

logger = setup_logging(os.path.join(cfg["PROJECT_ROOT"], "logs", "flask_app.log"))

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
        aws_access_key_id=cfg["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=cfg["AWS_SECRET_ACCESS_KEY"],
        region_name=cfg["AWS_REGION"],
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
    return username == cfg["APP_USERNAME"] and password == cfg["APP_PASSWORD"]


@app.route("/")
def home():
    """
    Redirect users to log in if not authenticated, else show video page
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
    if not is_authenticated():
        return redirect(url_for("login"))

    meet_id = os.getenv("MEET_ID")
    record_id = os.getenv("RECORD_ID")
    if not meet_id or not record_id:
        flash("No meet/record ID provided in environment!", "error")
        return render_template("video.html", presigned_url=None, decision=None)

    processed_bucket = cfg["PROCESSED_BUCKET"]
    processed_key = cfg["PROCESSED_KEY"]

    # Then get presigned URL from the processed bucket:
    presigned_url = create_s3_presigned_url(processed_bucket, processed_key)

    # Fetch full DynamoDB item
    item = get_item(meet_id, record_id)
    if not item:
        logger.info(f"No item found in DynamoDB for {meet_id}/{record_id}")
        flash("No item found in DynamoDB", "error")
        return render_template("video.html", presigned_url=None)

    # Pull the decision + explanation out of the item
    decision_data = item.get("InferenceResult")
    explanation_text = item.get("ExplanationText", "")
    short_decision = decision_data["decision"] if decision_data else None

    return render_template(
        "video.html",
        presigned_url=presigned_url,
        decision=short_decision,
        explanation_text=explanation_text,  # pass the explanation
    )


@app.route("/decision")
def show_decision():
    """
    Display the decision data for a specific lift.
    """
    if not is_authenticated():
        return redirect(url_for("login"))

    meet_id = os.getenv("MEET_ID")
    record_id = os.getenv("RECORD_ID")

    if not meet_id or not record_id:
        flash("No meet/record ID provided in environment!", "error")
        return render_template("video.html", presigned_url=None, decision=None)

    item = get_item(meet_id, record_id)
    if not item:
        decision_data = "No decision has been recorded yet."
        logger.info(f"No decision item found in DynamoDB for {meet_id}/{record_id}")
    else:
        decision_data = item.get("InferenceResult", {})
        logger.info(f"Decision data loaded from DynamoDB => {decision_data}")

    return render_template("decision.html", decision_data=decision_data)


# ----- Inference Endpoints (for Cloud Use) -----
# todo: These endpoints (e.g. /ping, /invocations) are intended for cloud deployments.
# Global variables to cache the model once loaded.
model = None
device = None


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
    """
    Health check endpoint.
    :return:
    """
    return "", 200


@app.route("/invocations", methods=["POST"])
def invocations():
    """

    :return:
    """
    data = request.get_json(force=True)
    video_path = data.get("video_path")
    model_path = data.get("model_path", os.environ.get("MODEL_S3_PATH"))
    if not video_path or not model_path:
        return jsonify({"error": "Missing video_path or model_path"}), 400
    m, d = initialize_model(model_path)

    results = m.track(source=video_path, device=d, show=False, save=True, max_det=1)
    results_list = list(results)

    from refvision.analysis.depth_checker import check_squat_depth_by_turnaround

    decision = check_squat_depth_by_turnaround(results_list)
    return jsonify({"decision": decision})


if __name__ == "__main__":
    port = cfg["FLASK_PORT"]
    app.run(host="0.0.0.0", port=port, debug=True)
