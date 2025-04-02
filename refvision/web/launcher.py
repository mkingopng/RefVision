# refvision/web/launcher.py
"""
Module for launching the Flask app with Gunicorn.
"""
import subprocess
import time
import webbrowser


def launch_gunicorn(flask_port: str, logger=None) -> None:
    """
    Launches Gunicorn to serve the Flask app on the specified port.

    :param flask_port: The port to bind Gunicorn to
    :param logger: (Optional) Logger for logging progress
    :return: None
    """
    if logger:
        logger.info("=== Starting Gunicorn (Flask app) ===")
    bind_address: str = f"0.0.0.0:{flask_port}"
    if logger:
        logger.info(f"Launching Gunicorn on {bind_address}...")

    cmd = [
        "poetry",
        "run",
        "gunicorn",
        "refvision.web.flask_app:app",
        "--chdir",
        "refvision/web",
        "--bind",
        bind_address,
        "--workers",
        "2",
    ]
    if logger:
        logger.info(f"Spawning command: {' '.join(cmd)}")

    gunicorn_process = subprocess.Popen(cmd)
    time.sleep(3)
    url: str = f"http://127.0.0.1:{flask_port}"
    if logger:
        logger.info(f"Opening browser at {url}")
    webbrowser.open(url)

    gunicorn_process.wait()
    if logger:
        logger.info("Gunicorn process has exited. Pipeline complete")
