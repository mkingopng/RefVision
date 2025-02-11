

## **Cost Control Strategy**
Using AWS doesn’t have to be expensive if we put **strict cost controls** in place. Here’s how:

### **1. Use CDK Destroy at the End of Each Session**
- Run `cdk destroy` after development sessions to delete resources and avoid idle costs.
- This can be automated with a script:
  ```bash
  # Destroy the stack if it's deployed
  cdk list | grep RefVisionStack && cdk destroy -f
  ```

### **2. Use a Budget with Alerts**
- **Set an AWS budget** (e.g., $20 per month).
- Get alerts via email/SNS if you exceed thresholds.
- Use AWS **Billing Alarms** to track S3, Lambda, Kinesis, and Step Functions costs.

### **3. Restrict Expensive Services**
- **Use On-Demand Inferentia instead of GPUs** – GPUs can get costly fast.
- **Limit Kinesis Retention** – Store minimal logs and data.
- **Use S3 Lifecycle Rules** – Auto-delete old videos from S3.
- **Minimize Step Function Executions** – Run only essential flows.

### **4. Keep a Cleanup Routine**
- **Run scheduled cleanups** – A Lambda or script can check for lingering resources.
- **Tag everything** – Helps track what belongs to RefVision.
- **Avoid unneeded logging** – CloudWatch logs can add up.

---

## **Final Decision**
✔ **Use real AWS resources** ✅  
✔ **Destroy resources at the end of each dev session** ✅  
✔ **Monitor spending with budgets & alerts** ✅  
✔ **Keep services minimal & optimized** ✅  

This approach gives you **full AWS compatibility** without breaking the bank.  
Would you like a **cost monitoring & cleanup script** to automate some of this? 🚀




# Component-by-Component Development and Testing Plan

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
