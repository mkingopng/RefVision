---
marp: true
theme: default
class: lead
paginate: true
---
# Title Slide
- Project Name: RefVision
- Michael Kingston [Contact Information]
- Brief tagline (e.g., "Revolutionizing Powerlifting with Serverless Technology")

<!---->

---
# Agenda Slide
- Overview of Topics Covered:
- Problem Statement
- Proposed Solution
- Deep Dive into Serverless Components
- Architecture Walkthrough
- Implementation Details
- Challenges and Solutions
- Future Enhancements and Roadmap
- Q&A

<!---->

---
# 2. Problem Statement (3 minutes)
- Contentious Decisions: Referee judgments on "Good" lifts often lead to disputes.
- Lack of Appeals: No effective method exists for athletes to appeal decisions.
- Rising Stakes: Increased prize money and record implications heighten tensions.
- Sport Integrity at Risk: Disputes can detract from the sport's reputation and viewer experience.
- Example: [Embed Video Clip of a Controversial Lift Decision]

<!---->

---
# 3. Proposed Solution: RefVision VAR (3 minutes)
- Video Referee Integration: Implement a Video Assistant Referee (VAR) system tailored for powerlifting.
- Supplementary Role: Enhances human referees with impartial video analysis.
- Limited Appeals: Each lifter gets one VAR appeal per meet to ensure tactical use and prevent delays.
- Enhanced Engagement: Adds drama and transparency, making competitions more exciting for audiences.
- Diagram: Integration of RefVision VAR with Traditional Refereeing

<!---->

---
# Why Serverless Architecture?
- Cost Efficiency: Pay-as-you-go model ideal for applications with variable usage.
- Scalability: Automatically handles varying loads without manual intervention.
- Maintenance: Reduced overhead in managing infrastructure.

## Challenges:
- GPU Support: Essential for efficient CV model inference; limited in traditional serverless.
- No Native GPU Serverless: AWS lacks a true serverless GPU solution for CV applications.

## Solution:
- Hybrid Approach: Combine AWS SageMaker endpoints with ECS Fargate for scale-to-zero GPU support.
- Icon-based Representation of Benefits and Challenges

<!---->

---
# 4. Overview of the Architecture
- Video Ingestion: Stream live video via Kinesis to S3.
- Preprocessing: Lambda functions process frames, storing metadata in DynamoDB.
- Video Inference: SageMaker performs pose estimation and classification.
- Explanation Generation: AWS Bedrock generates natural language explanations.
- Results Delivery: Annotated videos and explanations are served via a web app.
- Orchestration: AWS Step Functions manage workflow and integrations.
- High-Level Architecture Diagram

<!---->

---
# Deep Dive into Serverless Components (18 minutes)
[Each component can have 2-3 slides: Overview, Configuration, Best Practices/Challenges]

---
# 4.1. Video Ingestion and Preprocessing (2 minutes)
Components:
- Local Camera: Captures live video feed.
- AWS Kinesis Video Streams: Streams video to S3 in real-time.
- S3 Buckets:
  - Raw Video Storage: raw videos stored as .mp4
  - Preprocessed Storage: Processed frames and chunks.
- DynamoDB: Stores metadata and triggers preprocessing.
- AWS Lambda: Executes preprocessing tasks on incoming video.

## Workflow:
- Capture & Stream: Local cameras send live feed to Kinesis Video Streams.
- Storage: Video is segmented and stored in the Raw S3 Bucket.
- Metadata Recording: DynamoDB logs video segment details.
- Preprocessing: Lambda functions extract and transform frames, saving to Preprocessed S3 Bucket.
- Metadata Update: DynamoDB records locations of preprocessed frames.

## Workflow Diagram Illustrating Each Step

<!---->

---
# 4.2 Amazon S3 (2 minutes)
## Slide 1: S3 Buckets for Raw and Preprocessed Video
- Explain the dual-bucket strategy for raw and preprocessed data.
- Discuss bucket policies, lifecycle management, and versioning.

<!---->

---
## Slide 2: S3 Integration with Other Services
- Detail how S3 interacts with Kinesis, Lambda, and SageMaker.
- Use S3 Event Notifications to trigger workflows.

<!---->

---
## Slide 3: Optimization Tips
- Storage class selection (e.g., Standard vs. Intelligent-Tiering).
- Cost optimization with lifecycle policies and data compression.

<!---->

---
# 4.3 DynamoDB (2 minutes)
## 4.3.1: DynamoDB for Metadata Storage
- Why are we using DynamoDB as a controlling store / store of state?
- Explain why DynamoDB is chosen for its scalability and low latency.
- Data model overview: Meet ID, Squat ID, timestamp, chunk data.

<!---->

---
## 4.3.2: Table Design and Indexing
- Discuss partition keys, sort keys, and secondary indexes.
- Show schema for RefVision.

<!---->

---
## 4.3.3: Best Practices
- Provisioned vs. On-Demand capacity.
- Implementing DynamoDB Streams for real-time data processing.

<!---->

---
## 4.4 AWS Step Functions (4 minutes)
### 4.4.1: Step Functions Overview
- Introduction to AWS Step Functions and their role in orchestrating workflows.
- Key Features: Visual workflows, state management, error handling.

<!---->

---
### 4.4.2: Configuration and Integration
- Describe how Step Functions coordinate tasks between Lambda, SageMaker, ECS Fargate, and Bedrock.
- Example state machine for RefVision’s processing pipeline.

<!---->

---
### 4.4.3: Best Practices and Challenges
- Designing idempotent workflows to handle retries gracefully.
- Managing complex workflows with nested Step Functions.
- Monitoring and debugging Step Functions executions.

<!---->

---
### 4.4.4: Step Functions in RefVision
Detailed explanation of how Step Functions manage the end-to-end processing of each lift.
Integration with DynamoDB for state tracking and coordination.

<!---->

---
# 5. Architecture Walkthrough (5 minutes)

- Comprehensive Architecture Diagram
- Present a detailed diagram showcasing all serverless components and their interactions.
- Highlight data flow from video ingestion to result delivery.
- Step-by-Step Explanation
  - Narrate the end-to-end process, referencing the diagram.
  - Emphasize how Step Functions coordinate the workflow, leveraging DynamoDB for state management.
  - Illustrate the interaction between Step Functions and other services (Lambda, SageMaker, ECS Fargate, Bedrock).

<!---->

---
# 6. Implementation Details (5 minutes)

## 6.1 Infrastructure as Code (IaC)
- Tools used (e.g., AWS CloudFormation, Terraform, AWS SAM, AWS CDK, Pulumi).
- Benefits of IaC for deploying and managing serverless resources.
- Example IaC snippets for Step Functions and DynamoDB integration.

<!---->

---
# 7. Challenges and Solutions (2 minutes)
- Common Challenges in Serverless Architectures
  - Cold starts, state management, debugging complexities.

- Specific Challenges Faced in RefVision
  - Handling real-time video processing at scale.
  - Integrating GPU-intensive tasks within a serverless framework.
  - Coordinating multiple services with Step Functions.

- Solutions and Best Practices
  - Strategies employed to mitigate these challenges (e.g., provisioned concurrency, using Step Functions for orchestration).

<!---->

---
# 8. Future Enhancements and Roadmap (1 minute)

- Potential Improvements
  - Enhancing ML models for better accuracy.
  - Expanding to other sports or integrating additional features like real-time analytics.

<!---->

---
# 9. Q&A (1 minute)

<!--
Invite Questions
-->