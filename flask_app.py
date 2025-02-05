# flask_app.py
"""
flask app for playing contested lifts
"""
import os
import boto3
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask import abort
from dotenv import load_dotenv

load_dotenv()

# Configuration
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.environ.get("AWS_REGION", "ap-southeast-2")
S3_BUCKET_NAME = os.environ.get("S3_BUCKET_NAME", "refvision-annotated-videos")
VIDEO_KEY = os.environ.get("VIDEO_KEY", "chris_kennedy_squat.mp4")
# The shared "username" and "password" for POC. In production, use a proper auth system.
USERNAME = os.environ.get("APP_USERNAME", "admin")
PASSWORD = os.environ.get("APP_PASSWORD", "secret")

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "my-super-secret-flask-key")


# Helpers

def create_s3_presigned_url(bucket_name, object_name, expiration=3600):
    """
    Generate a presigned URL for an S3 object.
    By default, expires in 3600 seconds (1 hour).
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
            Params={'Bucket': bucket_name, 'Key': object_name},
            ExpiresIn=expiration
        )
    except Exception as e:
        print(f"Could not generate presigned URL: {e}")
        return None
    return response


def is_authenticated():
    """Simple check for authentication."""
    return session.get('logged_in', False)

def do_auth(username, password):
    """A very simplistic check for demonstration only."""
    return username == USERNAME and password == PASSWORD


# Routes

@app.route('/')
def home():
    """Just a simple homepage with a link to the login or the video."""
    if not is_authenticated():
        return redirect(url_for('login'))
    return redirect(url_for('show_video'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Simple username/password authentication for the POC."""
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
    """Logs the user out."""
    session.clear()
    flash('Logged out successfully', 'info')
    return redirect(url_for('login'))


@app.route('/video')
def show_video():
    """Main route that displays the video player."""
    if not is_authenticated():
        return redirect(url_for('login'))

    # Generate the pre-signed URL
    presigned_url = create_s3_presigned_url(S3_BUCKET_NAME, VIDEO_KEY)
    print("DEBUG: presigned_url =", presigned_url)
    if not presigned_url:
        # If presigned_url is None, that means the video was not found or an error occurred
        flash("Error: Video file not found in S3 or presigned URL generation failed.", "error")
        return render_template('video.html', presigned_url=None)

    return render_template('video.html', presigned_url=presigned_url)


# Run the app (for local testing)

if __name__ == '__main__':
    # For local dev testing only; in production run via WSGI server (e.g. gunicorn)
    app.run(host='0.0.0.0', port=5000, debug=True)
