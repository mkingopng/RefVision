# refvision/web/flask_app.py
"""
Flask Application for Playing Contested Lifts

This Flask application serves as a simple interface to authenticate users and
stream a pre-signed video file from AWS S3. It provides:
1. Simple username/password authentication (for proof-of-concept only).
2. A pre-signed URL generation to securely stream videos from S3.
3. Routes for login, logout, and video display.
"""
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
import boto3
from flask import Flask, render_template, request, redirect, url_for, session, flash
from dotenv import load_dotenv
from typing import Optional
from config.config import CFG

load_dotenv()

# Configuration
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.environ.get("AWS_REGION", "ap-southeast-2")
S3_BUCKET_NAME = os.environ.get("S3_BUCKET_NAME", "refvision-annotated-videos")
VIDEO_KEY = os.environ.get("VIDEO_KEY", CFG.MP4_FILE)
# The shared "username" and "password" for POC. In production, use a proper auth system.
USERNAME = os.environ.get("APP_USERNAME", "admin")
PASSWORD = os.environ.get("APP_PASSWORD", "secret")

app = Flask(__name__)
app.secret_key = os.environ.get(
    "FLASK_SECRET_KEY",
    "my-super-secret-flask-key"
)


def create_s3_presigned_url(
        bucket_name: str,
        object_name: str,
        expiration: int = 3600
) -> Optional[str]:
    """
    Generate a pre-signed URL for an S3 object, allowing temporary access.
    :param bucket_name: (str) Name of the S3 bucket.
    :param object_name: (str) Key of the S3 object.
    :param expiration: (int) Time (in seconds) for the URL to remain valid.
    :returns: Optional[str]: A pre-signed URL if successful, otherwise None.
    """
    s3_client = boto3.client(
        's3',
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION
    )
    try:
        response = s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': bucket_name,
                'Key': object_name
            },
            ExpiresIn=expiration
        )

    except Exception as e:
        print(f"Could not generate presigned URL: {e}")
        return None
    return response


def is_authenticated() -> bool:
    """
    Simple check for authentication
    :return: bool
    """
    return session.get('logged_in', False)


def do_auth(username: str, password: str) -> bool:
    """
    Authenticate user credentials.
    :param username: (str) Input username.
    :param password: (str) Input password.
    :return: bool: True if authentication is successful, False otherwise.
    """
    return username == USERNAME and password == PASSWORD


@app.route('/')
def home():
    """
    Redirect users to login if not authenticated, else show video page
    :return: None
    """
    if not is_authenticated():
        return redirect(url_for('login'))
    return redirect(url_for('show_video'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Handle user authentication via a simple login form.
    Supports GET (display login page) and POST (validate credentials).
    :return: None
    """
    if request.method == 'POST':
        user = request.form['username']
        pwd  = request.form['password']
        if do_auth(user, pwd):
            session['logged_in'] = True
            flash('Logged in successfully!', 'success')
            return redirect(url_for('show_video'))
        else:
            flash('Invalid credentials', 'error')
            return redirect(url_for('login'))
    return render_template('login.html')


@app.route('/logout')
def logout():
    """
    Log out the user and redirect to the login page
    :return: None
    """
    session.clear()
    flash('Logged out successfully', 'info')
    return redirect(url_for('login'))


@app.route('/video')
def show_video():
    """
    Display the video player with a pre-signed S3 URL.
    If the user is not authenticated, redirect to login.
    If S3 URL generation fails, show an error message.
    :return: video
    """
    if not is_authenticated():
        return redirect(url_for('login'))

    presigned_url = create_s3_presigned_url(
        S3_BUCKET_NAME,
        VIDEO_KEY
    )

    decision = None
    if os.path.exists("../../tmp/decision.txt"):
        with open("../../tmp/decision.txt") as f:
            decision = f.read().strip()

    if not presigned_url:
        flash(
            "Error: Video file not found in S3 or presigned URL generation failed.",
            "error")

        return render_template(
            'video.html',
            presigned_url=None,
            decision=decision
        )

    return render_template(
        'video.html',
        presigned_url=presigned_url,
        decision=decision
    )


if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )
