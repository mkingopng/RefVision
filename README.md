3. Component-by-Component Development and Testing Plan

I recommend the following sequence. For each component, we will write tests (with pytest) to validate functionality before moving on.
Component 1: Video Conversion and Preprocessing

    Task: Ensure that your function to convert non-mp4 files to mp4 (stripping metadata) works correctly.
    Test: Write pytest tests that provide sample video files and assert that the output is mp4 with no extra metadata.

Component 2: Critical Frame Detection

    Task: Verify that your find_critical_frame() function correctly processes a prerecorded video and returns the expected key frame index.

    Test: Create a test video (or use a sample) and check that the function returns the correct index.

    Optional: Wrap this function as a Lambda handler locally (simulate invocation via LocalStack) so you can later deploy it as a serverless function.

Component 3: Inference with YOLOv11-Pose

    Task: Run your inference code (in refvision/inference/inference.py) locally on a prerecorded video and verify that it produces the expected results.
    Test: Write tests that run the YOLO inference on a sample video (mocking any non-deterministic parts if needed) and check that the output contains valid detections and keypoints.

Component 4: State Management via DynamoDB

    Task: Define the data model (video metadata, inference results, explanation text, etc.) and implement functions that read and write to DynamoDB.
    Test: Using LocalStack’s DynamoDB endpoint, write tests to create, update, and query items.

Component 5: Explanation Generation

    Task: Create a Lambda function that uses AWS Bedrock (or, for development, a mock that calls OpenAI GPT) to generate natural language explanations based on inference results.
    Test: Write unit tests (or use mocked API responses) that confirm the function generates the expected explanation text.

Component 6: Web Application

    Task: Improve your Flask app (HTML, CSS, authentication) and ensure it can fetch data (e.g., video URL, decision, explanation) from DynamoDB.
    Test: Write tests for your Flask routes (using pytest and Flask’s test client) to ensure that login, video streaming, and results display work correctly.

Component 7: Orchestration via Step Functions

    Task: Define a simple Step Functions state machine that calls your Lambda functions (or local functions) in sequence.
    Test: Use the AWS CDK’s local unit tests (or even a local simulation using Step Functions Local) to verify that the workflow transitions correctly, including retries on error.

Component 8: Deployment Scripts and Infrastructure

    Task: Write and test your CDK stack(s) to provision the required AWS resources.
    Test: Use cdk synth and cdk deploy --require-approval never (when you’re ready for production) along with integration tests that use LocalStack if possible.

4. Next Steps and How to Proceed

Since you mentioned that the first priority is to set up a development environment that does not incur costs, I recommend starting with the following:

    Set Up Docker and LocalStack:
    – Create your docker-compose.yml as above and run LocalStack locally.
    – Verify you can connect using AWS CLI or boto3 (set endpoint_url='http://localhost:4566').

    Create and Activate Your Virtual Environment:
    – Install all dependencies and verify that your test suite (pytest) runs locally.

    Write a Minimal Test for One Component (e.g., the Critical Frame Detection Function):
    – Create a test file in tests/ that loads a small sample video file and asserts that find_critical_frame() returns the expected index.
    – Once this test passes locally, commit your work and move to the next component.

    Document Your Local Configuration:
    – Use environment variables (or a separate local config file) to set endpoints for LocalStack so that your code can seamlessly switch between local and live AWS endpoints.

    Decide on the Inference Execution Environment:
    – For now, run your YOLOv11-pose inference locally (or on a non-GPU machine) with the understanding that later you’ll port it to an ECS Fargate task that has GPU support and scales to zero. – You might simulate this with a Docker container locally that mimics the ECS task.

    Plan the Step Functions Orchestration:
    – Begin with a simple state machine definition that calls your preprocessing Lambda and then your inference Lambda. Test this workflow locally (using Step Functions Local if desired).

    Keep Everything Under Version Control and Write Tests:
    – Use pytest for unit tests. Create a suite of integration tests that use LocalStack to simulate S3, DynamoDB, and Lambda invocations.