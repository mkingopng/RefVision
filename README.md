# RefVision: CV-Assisted Judging for Powerlifting

RefVision is a serverless application that brings **video referee** capabilities to powerlifting competitions. It automatically ingests, preprocesses, and analyzes lifting attempts, then generates annotated videos with pose estimation overlays and natural-language explanations for “Good Lift” vs. “No Lift” decisions.

---

## Key Features

1. **Video Ingestion (Kinesis + S3)**  
   - Streams live video from meet cameras and stores raw footage in S3.

2. **Preprocessing (Lambda + DynamoDB)**  
   - Automatically extracts frames and records metadata for each attempt (lifter ID, attempt number, timestamps).

3. **Inference (SageMaker + ECS Fargate)**  
   - Runs a pose estimation model (e.g., PoseFormer, YOLO-based) on GPU to determine squat depth and classify each attempt.

4. **Explanation Generation (AWS Bedrock)**  
   - Converts inference results into human-readable explanations (e.g., “Hip joint was above knee”).

5. **Results Delivery (Flask UI + S3)**  
   - Annotated videos, classification results, and text explanations are shown in a simple web interface for judges and audiences.

6. **Orchestration (Step Functions + DynamoDB)**  
   - Coordinates each pipeline step, handles retries, and maintains the overall system state.

---

## Quick Start

### 1. Prerequisites
- **AWS Account** with access to Kinesis, Lambda, Step Functions, SageMaker, DynamoDB, and Bedrock.
- **Python 3.8+** and [pip](https://pip.pypa.io/en/stable/).
- [**AWS CLI**](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) configured (`aws configure`).

### 2. Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/YourUsername/refvision.git
   cd refvision
   ```
2. poetry
   ```bash
   poetry install
   ```
   
3. Deploy the CloudFormation stack:
   ```bash
   cdk deploy
   ```

