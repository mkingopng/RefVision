# refvision/inference/serve.py
"""
A simple Flask-based inference server for YOLOv11-Based Squat Depth Detection.
This script loads the model on first invocation and then handles incoming requests.
SageMaker will send POST requests to the /invocations endpoint.
"""
import os
from flask import Flask, request, jsonify
from refvision.inference.model_loader import load_model
from refvision.inference.depth_evaluator import evaluate_depth
from refvision.utils.logging_setup import setup_logging

app = Flask(__name__)

# Configure logging (optional)
logger = setup_logging(
    os.path.join(os.path.dirname(__file__), "../../logs/yolo_logs.log")
)

# global variables to cache the model after first load.
model = None
device = None


def initialize_model(model_path: str):
    """
    Load the model from the given path and return it.
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
def invoke():
    """
    Expects a JSON payload with keys:
      - "video_path": (str) the path to the video file
      - "model_path": (str) the path to the model weights
    Returns a JSON response containing the inference decision.
    """
    data = request.get_json(force=True)
    video_path = data.get("video_path")
    model_path = data.get("model_path", os.environ.get("MODEL_S3_PATH"))

    if not video_path or not model_path:
        return jsonify({"error": "Missing video_path or model_path"}), 400

    # load model if needed.
    m, d = initialize_model(model_path)

    # run tracking inference on the video.
    results = m.track(source=video_path, device=d, show=False, save=True, max_det=1)

    # todo: add detailed debug log information

    # evaluate squat depth and save the decision.
    decision = evaluate_depth(results, video_path)

    # return the inference decision.
    return jsonify({"decision": decision})


if __name__ == "__main__":
    # sageMaker expects your container to listen on 0.0.0.0:8080.
    app.run(host="0.0.0.0", port=8080)
