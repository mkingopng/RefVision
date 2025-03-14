# unified_app.py
"""
Imports the correct app based on the FLASK_APP_MODE environment variable.
Uses the FLASK_PORT from config/config.py in local mode, and port 8080 in cloud mode.
"""
import os
import dotenv
from refvision.common.config_local import Config as ConfigLocal
from refvision.common.config_cloud import Config as ConfigCloud
from refvision.web.flask_app import app as flask_app

dotenv.load_dotenv()

mode = os.environ.get("FLASK_APP_MODE", "cloud").lower()


if mode == "local":
    port = ConfigLocal.FLASK_PORT
elif mode == "cloud":
    port = ConfigCloud.FLASK_PORT
else:
    raise ValueError("Invalid FLASK_APP_MODE. Set it to 'local' or 'cloud'.")

if __name__ == "__main__":
    flask_app.run(host="0.0.0.0", port=port, debug=(mode == "local"))
