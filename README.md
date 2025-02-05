# Project Plan Overview

## Data Annotation
- **tool**: labelbox?
- video data type: `.mp4` videos
- label data type: `.json` files
- key points strategy: what are my key points?
- bounding box strategy
- export format for annotated videos
- script to convert annotated data into the format needed by yolo
- data augmentation

# Ontology
## 1. Lift Type (Classification)
   - Squat
   - Bench Press
   - Deadlift

## 2. Lifter Body Position (Classification and Bounding Boxes)
   - Starting Position
   - Mid-lift Position
   - End Position
   - Rack (for squat and bench) / Lockout (for deadlift)

## 3. Joint Angles and Positions (Keypoints / Skeleton Tracking)
   - Hip Position
   - Knee Position
   - Elbow Position (Bench Press)
   - Shoulder Position (Bench Press)
   - Foot Position (for Deadlift and Squat)
   - Wrist (for Bench Press)

## 4. Barbell Position (Bounding Boxes and Keypoints)
   - Bar Path (e.g., tracking the vertical movement)
   - Position relative to shoulders (squat), chest (bench), and thighs (deadlift)

## 5. Common Faults or Violations (Classification and Event Marking)
   - Depth (for Squat) – Below parallel, At parallel, Above parallel
   - Bar Control – Jerkiness or stopping mid-lift
   - Foot Movement (for Deadlift) – Shifting feet
   - Butt Lift Off (for Bench Press)
   - Bar not reaching chest (Bench Press)
   - Soft Knees (Deadlift lockout)

## 6. Referee Lights / Decision Outcomes (Event Marking)
   - Successful Lift
   - Failed Lift – Reason(s) if possible

## Training

## Inference

## UI for triggering, viewing footage, displaying referee decision and reasons

## AWS deployment

## 

## Week 1: Project Kickoff and Planning
- **Define Project Scope and Requirements**
  - **Action**: Clearly outline the functionalities of the referee tool.
    - Identify key features needed for the mockup:
      - Real-time pose estimation using YOLO-Pose.
      - Rule enforcement logic for powerlifting competitions.
      - Basic user interface to display results.
  - **Outcome**: A detailed project requirements document.

- **Set Up Development Environment**
  - **Action**: Install necessary tools and frameworks.
    - Python environment setup (preferably using virtual environments).
    - Install PyTorch, YOLO-Pose dependencies, and AWS CLI.
    - Set up version control with Git and create a GitHub repository.
  - **Outcome**: A fully configured development environment.

## **Week 2: Data Collection and Preparation**
- **Gather Datasets**
  - **Action**: Collect videos/images of powerlifting movements.
    - Source data from public datasets or record sample videos.
    - Ensure data represents various angles and conditions.
  - **Outcome**: A dataset ready for processing.

- **Data Annotation (if necessary)**
  - **Action**: Annotate data for training/testing.
    - Use annotation tools like LabelImg for bounding boxes and keypoints.
  - **Outcome**: Annotated dataset for model fine-tuning.

## **Week 3: YOLO-Pose Model Implementation**
- **Model Setup**
  - **Action**: Set up the YOLO-Pose model.
    - Clone the YOLO-Pose repository.
    - Verify the model runs with sample data.
  - **Outcome**: YOLO-Pose running successfully in your environment.

- **Model Fine-Tuning (if necessary)**
  - **Action**: Fine-tune the model with your dataset.
    - Adjust model parameters for better accuracy on powerlifting poses.
  - **Outcome**: A model optimized for your specific use case.

## **Week 4: Inference Pipeline Development**
- **Develop Inference Scripts**
  - **Action**: Write scripts to process videos/images through the model.
    - Handle input data, run inference, and collect outputs.
  - **Outcome**: An inference pipeline that processes data and outputs pose estimations.

- **Rule Enforcement Logic**
  - **Action**: Implement logic to interpret pose estimations according to powerlifting rules.
    - Define criteria for successful lifts (e.g., depth in squats).
  - **Outcome**: A module that evaluates lifts based on model outputs.

## **Week 5: AWS Serverless Integration**
- **AWS Account Setup**
  - **Action**: Ensure you have access to AWS services.
    - Set up IAM roles, AWS Lambda, and AWS S3 buckets.
  - **Outcome**: AWS environment ready for deployment.

- **Deploy Inference Pipeline to AWS Lambda**
  - **Action**: Containerize your application using AWS Lambda Layers or Docker containers (with AWS ECR).
    - Ensure model and dependencies comply with AWS Lambda limitations.
  - **Outcome**: Inference pipeline running on AWS Lambda.

## **Week 6: Optimization and Testing on AWS**
- **Optimize for Serverless Constraints**
  - **Action**: Address cold starts and execution time limits.
    - Use techniques like dependency trimming and warm-up strategies.
  - **Outcome**: Optimized serverless application.

- **Testing on AWS**
  - **Action**: Test the serverless application with sample inputs.
    - Verify accuracy and performance.
  - **Outcome**: Validated serverless inference pipeline.

## **Week 7: Mockup Interface Development**
- **Develop User Interface**
  - **Action**: Create a simple web or desktop interface.
    - Display input videos and overlay pose estimations.
    - Show rule evaluation results.
  - **Outcome**: A functional mockup interface for demonstrations.

- **Integration with Backend**
  - **Action**: Connect the UI with AWS Lambda functions.
    - Ensure seamless data flow between frontend and backend.
  - **Outcome**: Integrated system ready for end-to-end testing.

## **Week 8: Final Testing and Presentation Preparation**
- **End-to-End Testing**
  - **Action**: Conduct thorough testing of the entire system.
    - Use different data samples to test robustness.
  - **Outcome**: A stable and reliable mockup.

- **Prepare Presentation**
  - **Action**: Develop presentation materials.
    - Create slides highlighting the project's goals, architecture, and AWS integration.
    - Prepare a live demo or recorded video showcasing the tool.
  - **Outcome**: A polished presentation ready for the AWS Serverless group.

## **Additional Considerations**
- **Project Management**
  - Use agile methodologies to track progress.
  - Set up regular check-ins or sprints to stay on schedule.

- **Documentation**
  - Keep detailed documentation at each step.
  - This will help in both development and during the presentation.

- **Collaboration Tools**
  - Use tools like Trello or Jira for task management.
  - Slack or Microsoft Teams for communication (if working with a team).

- **Learning Resources**
  - **YOLO-Pose Documentation**: Familiarize yourself with model specifics.
  - **AWS Serverless Tutorials**: Leverage AWS's documentation and tutorials on Lambda and serverless deployments.

- **Potential Challenges**
  - **Model Size Limitations**: AWS Lambda has a deployment package size limit (250 MB uncompressed). Consider model optimization or using AWS Elastic Inference.
  - **Execution Time Limits**: Lambda has a maximum execution time (15 minutes). Ensure your inference tasks complete within this limit.
  - **Cold Start Latency**: Serverless functions may have latency issues. Mitigate this with provisioned concurrency if necessary.

## **Next Steps**

1. **This Week**
   - Start with defining the project scope and setting up your environment.
   - Begin collecting datasets.
2. **Communication**
   - If you have team members or mentors, schedule a kickoff meeting.
   - Keep stakeholders updated on progress.
3. **Feedback Loop**
   - Regularly test components as you develop them.
   - Be prepared to iterate based on test results.

```bash
python edit_video.py --input chris_kennedy_squat.mov --output chris_kennedy_squat.mp4 --start 42 --end 62 --width 1920 --height 1080
```

convert to mp4
```bash
ffmpeg -i theo_maddox_deadlift_2.avi -strict -2 theo_maddox_deadlift_2.mp4
```

---------------


# Manually Delete Conflicting Resources
List IAM Roles:
```bash
aws iam list-roles | grep RefVision
```

delete IAM Roles:
```bash
aws iam delete-role --role-name RefVisionFirehoseRole
aws iam delete-role --role-name VideoIngestionFunctionServiceRole
aws iam delete-role --role-name ProcessingPipelineRole
aws iam delete-role --role-name PreprocessingFunctionServiceRole
```

Check S3 Buckets:
```bash
aws s3 ls
```

Ensure all objects, including versions, are deleted from the bucket before attempting to delete the bucket itself.
```bash
aws s3api list-object-versions --bucket ref-vision-video-bucket
```

Delete all versions:
```bash
aws s3api delete-object --bucket ref-vision-video-bucket --key <object-key> --version-id <version-id>
```

delete the bucket:
```bash
aws s3 rb s3://ref-vision-video-bucket --force
```

S3 Bucket (Ensure it's empty):
```bash
aws s3api delete-objects --bucket ref-vision-video-bucket --delete "$(aws s3api list-object-versions --bucket ref-vision-video-bucket --query='{Objects: Versions[].{Key:Key,VersionId:VersionId}}')"
aws s3 rb s3://ref-vision-video-bucket --force
```

Check Firehose Delivery Streams:
```bash
aws firehose list-delivery-streams
```

delete firehose Delivery Streams:
```bash
aws firehose delete-delivery-stream --delivery-stream-name RefVisionFirehoseStream
```

List Kinesis Streams:
```bash
aws kinesis list-streams
````

Delete Kinesis Streams:
```bash
aws kinesis delete-stream --stream-name RefVisionVideoStream
```

List Log Groups:
```bash
aws logs describe-log-groups --log-group-name-prefix /aws/lambda
```

Log Groups:
```bash
aws logs delete-log-group --log-group-name /aws/lambda/VideoIngestionFunction
aws logs delete-log-group --log-group-name /aws/lambda/PreprocessingFunction
```

```bash
aws sqs list-queues
```

SQS Queues:
```bash
aws sqs delete-queue --queue-url https://sqs.ap-southeast-2.amazonaws.com/001499655372/test
```

Verify if there are any lingering stacks in ROLLBACK_COMPLETE or DELETE_FAILED state:
```bash
aws cloudformation list-stacks --query "StackSummaries[?StackStatus=='ROLLBACK_COMPLETE' || StackStatus=='DELETE_FAILED'].[StackName, StackStatus]"
```

Manually delete any remaining stacks via the AWS Console or CLI:
```bash
aws cloudformation delete-stack --stack-name RefVisionStack
```

```bash
poetry run python run_pipeline.py \
  --video data/raw_data/chris_kennedy_squat.mp4 \
  --avi-output runs/pose/track2/chris_kennedy_squat.avi \
  --mp4-output runs/pose/track2/chris_kennedy_squat.mp4 \
  --s3-bucket refvision-annotated-videos \
  --s3-key chris_kennedy_squat.mp4 \
  --flask-port 5000
```