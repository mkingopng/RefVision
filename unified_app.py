# unified_app.py
"""
imports the correct app based on the FLASK_APP_MODE environment variable
"""
import os
import dotenv

dotenv.load_dotenv()

mode = os.environ.get("FLASK_APP_MODE", "cloud").lower()

if mode == "local":
    # use the local web app (authentication + video streaming)
    from refvision.web.flask_app import app as flask_app

    port = 5000  # local version runs on port 5000
elif mode == "cloud":
    # use cloud inference server (for SageMaker)
    from refvision.inference.serve import app as flask_app

    port = 8080  # SageMaker expects port 8080
else:
    raise ValueError("Invalid FLASK_APP_MODE. Set it to 'local' or 'cloud'.")

if __name__ == "__main__":
    flask_app.run(host="0.0.0.0", port=port, debug=(mode == "local"))
