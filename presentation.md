---
marp: true
theme: default
class: lead
paginate: true
---
#  Presentation Structure and Overview

1. **Introduction (2 minutes)**
   - **Title Slide**
     - Project Name: RefVision
     - Your Name and Contact Information
     - Brief tagline (e.g., "Revolutionizing Powerlifting with Serverless Technology")
---
# Agenda Slide**
Overview of Topics Covered:
1. Problem Statement
2. Proposed Solution
3. Deep Dive into Serverless Components
4. Architecture Walkthrough
5. Implementation Details
6. Challenges and Solutions
7. Future Enhancements and Roadmap
8. Q&A

---
# 2. Problem Statement (3 minutes)
- Contentious Decisions: Referee judgments on "Good" lifts often lead to disputes.
- Lack of Appeals: No effective method exists for athletes to appeal decisions.
- Rising Stakes: Increased prize money and record implications heighten tensions.
- Sport Integrity at Risk: Disputes can detract from the sport's reputation and viewer experience.
- Example: [Embed Video Clip of a Controversial Lift Decision]
- Add Statistics: Include data or statistics to quantify the problem (e.g., number of disputes in recent competitions).
- Impact Statement: Highlight how these disputes affect athletes’ morale and the sport's integrity.

---
# 3. Proposed Solution: RefVision VAR (3 minutes)
- **Video Referee Integration**: Implement a Video Assistant Referee (VAR) system tailored for powerlifting.
- **Supplementary Role**: Enhances human referees with impartial video analysis.
- **Limited Appeals**: Each lifter gets one VAR appeal per meet to ensure tactical use and prevent delays.
- **Enhanced Engagement**: Adds drama and transparency, making competitions more exciting for audiences.
- **Diagram**: Integration of RefVision VAR with Traditional Refereeing

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

---
# 4. Overview of the Architecture
- **Video Ingestion**: Stream live video via Kinesis to S3.
- **Preprocessing**: Lambda functions process frames, storing metadata in DynamoDB.
- **Video Inference**: SageMaker performs pose estimation and classification.
- **Explanation Generation**: AWS Bedrock generates natural language explanations.
- **Results Delivery**: Annotated videos and explanations are served via a web app.
- **Orchestration**: AWS Step Functions manage workflow and integrations.
- **High-Level Architecture Diagram**

---
4. **Deep Dive into Serverless Components (18 minutes)**
   **Each component can have 2-3 slides: Overview, Configuration, Best Practices/Challenges**

---
# 4.1. Video Ingestion and Preprocessing (2 minutes)
Components:
- Local Camera: Captures live video feed.
- AWS Kinesis Video Streams: Streams video to S3 in real-time.
- S3 Buckets:
	- raw Video Storage: raw videos stored as .mp4
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

---
# 4.2 Amazon S3 (2 minutes)**
   - **Slide 1: S3 Buckets for Raw and Preprocessed Video**
     - Explain the dual-bucket strategy for raw and preprocessed data.
     - Discuss bucket policies, lifecycle management, and versioning.
---
   - **Slide 2: S3 Integration with Other Services**
     - Detail how S3 interacts with Kinesis, Lambda, and SageMaker.
     - Use S3 Event Notifications to trigger workflows.
---
   - **Slide 3: Optimization Tips**
     - Storage class selection (e.g., Standard vs. Intelligent-Tiering).
     - Cost optimization with lifecycle policies and data compression.
---
# 4.3 DynamoDB (2 minutes)
## 4.3.1: DynamoDB for Metadata Storage
- why are we using DynamoDB as a controlling store
- Explain why DynamoDB is chosen for its scalability and low latency.
- Data model overview: Meet ID, Squat ID, timestamp, chunk data.

---
## 4.3.2: Table Design and Indexing**
- Discuss partition keys, sort keys, and secondary indexes.
- Show schema for RefVision.

---
# 4.3.3: Best Practices
- Provisioned vs. On-Demand capacity.
- Implementing DynamoDB Streams for real-time data processing.

---
# 4.4 AWS Step Functions (4 minutes)
## 4.4.1: Step Functions Overview
- Introduction to AWS Step Functions and their role in orchestrating workflows.
- Key Features: Visual workflows, state management, error handling.

---
## 4.4.2: Configuration and Integration**
- Describe how Step Functions coordinate tasks between Lambda, SageMaker, ECS Fargate, and Bedrock.
- Example state machine for RefVision’s processing pipeline.

---
## 4.4.3: Best Practices and Challenges
- Designing **idempotent** workflows to handle retries gracefully.
- Managing complex workflows with nested Step Functions.
- Monitoring and debugging Step Functions executions.

---
## 4.4.4: Step Functions in RefVision
- Detailed explanation of how Step Functions manage the end-to-end processing of each lift.
- Integration with DynamoDB for state tracking and coordination.

---
# 4.5 Preprocessing with AWS Lambda (2 minutes)
## 4.5.1: Lambda Functions for Frame Extraction**
- Role of Lambda in preprocessing video chunks.
- Event-driven invocation via DynamoDB triggers or Step Functions.

---
## 4.5.2: Configuration and Limits
- Memory allocation, timeout settings, and concurrency management.
- Handling large payloads and retries.

---
## 4.5.3: Best Practices and Optimization
- Code optimisation for faster execution.
- Utilising Lambda Layers for shared dependencies.

---
# 4.6 Video Inference with AWS SageMaker and ECS Fargate (2 minutes)
Components:
- S3 Event Notifications: Trigger inference upon new video/frame uploads.
- ECS Fargate Containers: Handle pose estimation and classification.
- AWS SageMaker Endpoint: Hosts the PoseFormer model for keypoint detection.
- AWS Step Functions: Orchestrate the inference workflow.
- DynamoDB: Stores inference results and metadata.
- S3: Saves annotated videos for replay.

Workflow:
- Trigger: New video segment uploaded to S3 triggers an S3 Event.
- Orchestration: Step Functions initiate the inference process.
- Pose Estimation: SageMaker processes frames to detect keypoints.
- Decision Making: ECS Fargate calculates metrics and determines lift validity.
- Result Storage: Classification results and keypoints are saved to DynamoDB.
- Annotation: Video segments are annotated and stored in S3 for playback.

Inference Pipeline Diagram

---
## 4.6.2: ECS Fargate for Post-Inference Processing
- Explain why ECS Fargate is used alongside SageMaker.
- Container orchestration for calculating keypoint metrics and decision criteria.

---
## 4.6.3: Integration and Scaling**
- How SageMaker and Fargate scale based on demand.
- Configuring autoscaling policies and handling peak loads.

---
# 4.7 Explanation Generation with AWS Bedrock (2 minutes)
## 4.7.1: AWS Bedrock Overview
- Introduction to Bedrock and its capabilities for natural language generation.
- Integration with Lambda for generating explanations.
- Why It Matters:
  - Transparency: Clear explanations help athletes and audiences understand decisions.
  - Engagement: Natural language explanations make the results more relatable and informative.

Components:
- AWS Lambda: Triggers explanation generation post-inference.
- AWS Bedrock: Generates detailed, natural language explanations.
- DynamoDB: Stores explanations and related metadata.

Workflow:
- Inference Completion: Lambda detects that inference results are ready.
- Input Preparation: Keypoints, classification, and confidence scores are formatted for Bedrock.
- Explanation Generation: Bedrock produces a human-readable explanation.
- Storage: Explanations are saved in DynamoDB alongside metadata.

Example Explanation:
- "The lifter's squat was judged 'No Lift' because the hip joint reached 2 cm above the knee joint relative to the floor."

Diagram Showing Data Flow from Inference to Explanation

---
## 4.7.2: Configuration and Usage
- Setting up Bedrock with Claude sonnet.
- Example API calls for generating explanations.

---
## 4.7.3: Best Practices
- Ensuring consistency and accuracy in generated explanations.
- Handling latency by batching requests or optimising prompts.

---
# 4.8 Client-facing Web-Based Application with Flask and AWS CloudFront (2 minutes)
## 4.8.1: Flask & FastAPI for Backend Services
- Role of Flask in serving the web application: API endpoints, data retrieval.
- Deployment options: ECS Fargate (Containers), vs AWS Lambda with API Gateway (Serverless).

Components:
- S3 Bucket: Hosts processed and annotated videos.
- Flask: Serves the web application backend.
- FastAPI: 
- AWS CloudFront: Distributes web content globally for low latency.
- DynamoDB: Provides data for rendering UI elements.

Workflow:
- Video Replay: Users can watch annotated videos with keypoints and classifications.
- Results Display: View detailed classifications and model-generated explanations.
- Manual Overrides: Judges can adjust decisions if necessary.
- Interactive Features:
	- Live updates during competitions.
    - Filters by lifter, attempt, or classification.

User Interface Mockups: Insert Screenshots or Mockup Images Here

---
5. Integration and Orchestration

Central Control: DynamoDB
- State Management: Tracks the status of each lift and pipeline step.
- Data Linking: Connects video files, frame data, model results, and explanations via unique IDs.

Workflow Orchestration: AWS Step Functions
- Sequential Processing: Manages the flow from preprocessing to inference to explanation.
- Automatic Retries: Handles failures in any step, ensuring robustness.
- Scalability: Efficiently manages multiple concurrent lifts without bottlenecks.

Data Structure Overview:
- Meet ID: Contains metadata for the entire competition.
- Squat ID: Links all data related to a specific lift, including videos, results, and explanations.
- State: Indicates the current processing stage of each lift.

Integration Diagram Showing DynamoDB and Step Functions Coordination

---
## 4.8.2: CloudFront for Content Delivery
- Benefits of using CloudFront: low latency, global distribution.
- Configuration: origin settings, cache behaviours, SSL/TLS.
---
## 4.8.3: Security and Scalability
- Implementing security best practices: HTTPS, WAF, Origin Access Identity (OAI) for S3.
- Scaling Flask services using API Gateway throttling or Fargate task scaling.

---
# 5. Architecture Walkthrough (5 minutes)
Comprehensive Architecture Diagram
- Present a detailed diagram showcasing all serverless components and their interactions.
- Highlight data flow from video ingestion to result delivery.
- **Step-by-Step Explanation**
  - Narrate the end-to-end process, referencing the diagram.
  - Emphasize how Step Functions coordinate the workflow, leveraging DynamoDB for state management.
  - Illustrate the interaction between Step Functions and other services (Lambda, SageMaker, ECS Fargate, Bedrock).
---
# 6. Implementation Details (5 minutes)
## 6.1 Infrastructure as Code (IaC)
- Tools used (e.g., AWS CloudFormation, Terraform, AWS SAM, AWS CDK, Pulumi).
- Benefits of IaC for deploying and managing serverless resources.
- Example IaC snippets for Step Functions and DynamoDB integration.

---
# 6.2: Slide 2: Monitoring and Logging
- Utilise AWS CloudWatch for monitoring Step Functions, Lambda functions, SageMaker endpoints, and other services.
- Implement centralised logging for troubleshooting and performance optimisation.
- Use CloudWatch Logs and AWS X-Ray for tracing Step Functions executions.

---
# 6.3: Security Considerations
- IAM roles and permissions for each service.
- Ensuring data protection with encryption in transit and at rest.
- Implementing VPCs if necessary for additional security layers.
- Secure Step Functions state machines with appropriate IAM policies.

---
# 7. Challenges and Solutions (2 minutes)
- **Common Challenges in Serverless Architectures**
  - Cold starts, state management, debugging complexities.
- **Specific Challenges Faced in RefVision**
  - Handling real-time video processing at scale.
  - Integrating GPU-intensive tasks within a serverless framework.
  - Coordinating multiple services with Step Functions.
- **Solutions and Best Practices**
  - Strategies employed to mitigate these challenges (e.g., provisioned concurrency, using Step Functions for orchestration).
  - Designing Step Functions workflows to be resilient and scalable.
---
# After Action Review (AAR)

---
6. Scaling and Cost Optimization

Key Considerations:
    - Preprocessing Efficiency:
        - Utilize AWS Lambda for lightweight tasks to minimize costs.
        - Delegate heavy processing (e.g., frame extraction) to scalable services like SageMaker.
    - Inference Scaling:
        - Auto-Scaling: Configure SageMaker endpoints to scale based on demand.
        - Scale to Zero: Ensure resources are minimized when not in use, reducing idle costs.
    - Data Management:
        - S3 Lifecycle Policies: Automatically delete or archive temporary files after processing.
        - Cost Monitoring: Implement AWS Cost Explorer to track and optimize spending.

Optimization Strategies:
- Serverless Benefits: Pay only for actual usage, ideal for event-driven workloads.
- Hybrid Solutions: Combine serverless with containerized services for GPU-intensive tasks.

Graph or Chart Illustrating Cost Savings Through Optimization

---
# 8. Future Enhancements and Roadmap (1 minute)
- **Potential Improvements**
  - Enhancing ML models for better accuracy.
  - Expanding to other sports or integrating additional features like real-time analytics.
- **Scalability Plans**
  - Adapting the architecture for larger events or more users.
  - Exploring multi-region deployments for global scalability.

---
# 9. Q&A (1 minute)
- **Invite Questions**
  - Open the floor for audience questions to clarify and expand on specific topics.

---

## **Detailed Content Suggestions for Step Functions**

### **4.4 AWS Step Functions (4 minutes)**

#### **Slide 1: Step Functions Overview**
- **Title:** AWS Step Functions Overview
- **Content:**
  - **Definition:** AWS Step Functions is a serverless orchestration service that allows you to coordinate multiple AWS services into serverless workflows.
  - **Role in RefVision:** Acts as the central coordinator for the entire processing pipeline, managing the sequence of tasks from video ingestion to results delivery.
  - **Key Features:**
    - **Visual Workflows:** Easily visualize and manage the flow of tasks.
    - **State Management:** Maintains the state of each step in the workflow.
    - **Error Handling:** Built-in retries, catchers, and parallel execution.
- **Visuals:**
  - Diagram showing Step Functions coordinating multiple services (Lambda, SageMaker, ECS Fargate, Bedrock).

#### **Slide 2: Configuration and Integration**
- **Title:** Configuring Step Functions for RefVision
- **Content:**
  - **State Machine Design:**
    - **States:** Define states such as Video Ingestion, Preprocessing, Inference, Explanation Generation, and Results Delivery.
    - **Transitions:** Show transitions between states based on success or failure.
  - **Integration Points:**
    - **Lambda Triggers:** Invoke Lambda functions for preprocessing and other tasks.
    - **SageMaker Integration:** Directly call SageMaker endpoints for inference.
    - **ECS Fargate Tasks:** Trigger Fargate containers for post-inference processing.
    - **Bedrock Integration:** Invoke Bedrock for explanation generation.
  - **Example State Machine:**
    - Provide a simplified JSON or YAML snippet of the Step Functions state machine for a specific workflow.
- **Visuals:**
  - Example state machine diagram or JSON/YAML code snippet highlighting key transitions.

#### **Slide 3: Best Practices and Challenges**
- **Title:** Best Practices for Using Step Functions
- **Content:**
  - **Designing Idempotent Workflows:** Ensure that workflows can handle retries without adverse effects.
  - **Modular State Machines:** Break down complex workflows into smaller, reusable state machines.
  - **Error Handling:** Utilize retry policies and catchers to gracefully handle failures.
  - **Monitoring:** Use CloudWatch to monitor Step Functions executions, track metrics, and set up alarms for failures.
  - **Scalability:** Design workflows to handle high concurrency and large-scale processing.
- **Visuals:**
  - Checklist of best practices.
  - Diagram showing error handling within a state machine.
- **Additional Notes:**
  - Discuss how you addressed specific challenges, such as coordinating multiple services and ensuring reliable state management.

#### **Slide 4: Step Functions in RefVision**
- **Title:** Step Functions as the Central Coordinator in RefVision
- **Content:**
  - **End-to-End Orchestration:** Explain how Step Functions manage the entire lifecycle of a lift from video ingestion to results delivery.
  - **Interaction with DynamoDB:**
    - Step Functions read and update state information in DynamoDB to track progress and status.
    - Utilize DynamoDB Streams to trigger Step Functions when new data is available.
  - **Sequential and Parallel Execution:**
    - Handle tasks that need to occur in sequence (e.g., preprocessing before inference) and tasks that can run in parallel (e.g., simultaneous frame extraction).
  - **Workflow Example:**
    - Step-by-step walkthrough of a single lift processing:
      1. **Video Ingestion:** Kinesis streams video to S3.
      2. **Preprocessing:** Lambda functions extract frames.
      3. **Inference:** SageMaker performs pose estimation.
      4. **Post-Inference Processing:** ECS Fargate calculates metrics.
      5. **Explanation Generation:** Bedrock generates explanations.
      6. **Results Delivery:** Annotated videos and explanations are stored and served via the web app.
- **Visuals:**
  - Detailed workflow diagram highlighting Step Functions’ role.
  - Sequence diagram showing interactions between Step Functions and other services.

---

## **Updated Slide Layout Examples**

### **Slide: AWS Step Functions Overview**

---

**Title:** AWS Step Functions Overview

**Content:**
- **Definition:**
  - AWS Step Functions is a serverless orchestration service that coordinates multiple AWS services into flexible workflows.
- **Role in RefVision:**
  - Central orchestrator managing the sequence of tasks from video ingestion to result delivery.
- **Key Features:**
  - **Visual Workflows:** Easily design and visualize complex workflows.
  - **State Management:** Maintains the state and context of each step.
  - **Error Handling:** Built-in mechanisms for retries and error catching.

**Visual:**
- Diagram showing Step Functions in the center, connecting to Lambda, SageMaker, ECS Fargate, Bedrock, and DynamoDB.

**Notes:**
- Emphasize the importance of having a central coordinator to manage the complex interactions between various services.

---

### **Slide: Configuring Step Functions for RefVision**

---

**Title:** Configuring Step Functions for RefVision

**Content:**
- **State Machine Design:**
  - **States:**
    - **Video Ingestion:** Triggered by Kinesis to store video in S3.
    - **Preprocessing:** Lambda functions extract and preprocess frames.
    - **Inference:** SageMaker performs pose estimation.
    - **Post-Inference Processing:** ECS Fargate calculates metrics.
    - **Explanation Generation:** Bedrock generates natural language explanations.
    - **Results Delivery:** Annotated videos and explanations are stored in S3 and served via the web app.
  - **Transitions:**
    - Success and failure transitions between states.
    - Parallel states for concurrent processing where applicable.
- **Integration Points:**
  - **Lambda Invocations:** Step Functions trigger Lambda for preprocessing.
  - **SageMaker Calls:** Direct invocation of SageMaker endpoints for inference.
  - **ECS Fargate Tasks:** Trigger containerized tasks for metric calculations.
  - **Bedrock Integration:** Invoke Bedrock for generating explanations.

**Visual:**
- Simplified state machine diagram showing states and transitions.
- Example JSON snippet illustrating a part of the state machine.

**Notes:**
- Highlight how each state corresponds to a specific task in the processing pipeline.

---

### **Slide: Best Practices for Using Step Functions**

---

**Title:** Best Practices for Using Step Functions

**Content:**
- **Designing Idempotent Workflows:**
  - Ensure that each step can be safely retried without side effects.
- **Modular State Machines:**
  - Break down complex workflows into smaller, reusable components.
- **Error Handling:**
  - Implement retry policies and catchers to manage failures gracefully.
- **Monitoring and Logging:**
  - Use CloudWatch to monitor executions, track performance metrics, and set up alarms for failures.
- **Scalability:**
  - Design workflows to handle high concurrency and large-scale processing demands.

**Visual:**
- Checklist of best practices.
- Diagram illustrating error handling within a state machine (e.g., retries, catch blocks).

**Notes:**
- Discuss specific strategies you employed to ensure reliability and scalability in RefVision’s workflows.

---

### **Slide: Step Functions as the Central Coordinator in RefVision**

---

**Title:** Step Functions as the Central Coordinator in RefVision

**Content:**
- **End-to-End Orchestration:**
  - Manage the entire lifecycle of a lift from video ingestion to results delivery.
- **Interaction with DynamoDB:**
  - Step Functions read and update state information in DynamoDB.
  - Utilize DynamoDB Streams to trigger workflows when new data is available.
- **Sequential and Parallel Execution:**
  - Handle dependent tasks in sequence (e.g., preprocessing before inference).
  - Execute independent tasks in parallel to optimize processing time.
- **Workflow Example:**
  - **Step 1:** Video is captured and streamed via Kinesis to S3.
  - **Step 2:** Step Functions trigger Lambda functions for frame extraction.
  - **Step 3:** SageMaker performs pose estimation on preprocessed frames.
  - **Step 4:** ECS Fargate processes inference results to calculate metrics.
  - **Step 5:** Bedrock generates natural language explanations based on metrics.
  - **Step 6:** Annotated videos and explanations are stored in S3 and displayed via the web app.

**Visual:**
- Detailed workflow diagram showing Step Functions coordinating each step.
- Sequence diagram illustrating the flow of data and control between Step Functions and other services.

**Notes:**
- Emphasize the seamless coordination and state management provided by Step Functions, ensuring that each task is executed in the correct order and handling any errors that arise.

---

## **Additional Adjustments to Other Sections**

### **5. Architecture Walkthrough (5 minutes)**
- **Comprehensive Architecture Diagram**
  - **Enhancement:** Ensure Step Functions are prominently featured as the central orchestrator.
  - **Visuals:** Use distinct colors or labels to highlight Step Functions’ interactions with DynamoDB and other services.
- **Step-by-Step Explanation**
  - **Narration Adjustments:** Clearly describe how Step Functions coordinate each step, leveraging DynamoDB for state tracking.
  - **Example Path:** Walk through a single lift’s processing journey, explicitly pointing out where Step Functions manage transitions and error handling.

### **6. Implementation Details (5 minutes)**
- **Slide 1: Infrastructure as Code (IaC)**
  - **Enhancement:** Include Step Functions definitions within your IaC templates.
  - **Visuals:** Show a snippet of a Step Functions state machine definition in CloudFormation or Terraform.
- **Slide 2: Monitoring and Logging**
  - **Enhancement:** Highlight how you monitor Step Functions executions using CloudWatch.
  - **Visuals:** Include screenshots of CloudWatch dashboards tracking Step Functions metrics (e.g., execution counts, success rates, error rates).
- **Slide 3: Security Considerations**
  - **Enhancement:** Detail IAM roles and policies specific to Step Functions, ensuring they have the necessary permissions to invoke other services securely.

### **7. Challenges and Solutions (2 minutes)**
- **Specific Challenges Faced in RefVision**
  - **Enhancement:** Add challenges related to orchestrating complex workflows with Step Functions, such as managing state transitions and handling failures.
- **Solutions and Best Practices**
  - **Enhancement:** Discuss how Step Functions’ features (e.g., retries, error catching, parallel states) helped overcome orchestration challenges.

---

## **Final Recommendations**

1. **Emphasize Step Functions’ Central Role:**
   - Continuously reference how Step Functions orchestrate the entire workflow, ensuring smooth and reliable processing.
   
2. **Use Clear and Detailed Diagrams:**
   - Ensure your architecture diagrams clearly show Step Functions’ interactions with other services.
   - Use annotations to highlight how Step Functions manage state and handle transitions.

3. **Provide Concrete Examples:**
   - Use specific examples or scenarios to illustrate how Step Functions handle complex workflows and error scenarios.

4. **Highlight Benefits:**
   - Showcase how Step Functions contribute to scalability, reliability, and maintainability of RefVision’s architecture.

5. **Engage with Technical Depth:**
   - Since your audience is technically savvy, delve into some of the complexities and nuances of using Step Functions, such as handling long-running tasks or integrating with multiple AWS services.

6. **Rehearse the Flow:**
   - Practice narrating the architecture walkthrough, ensuring you smoothly integrate Step Functions into the explanation without overcomplicating the narrative.

---

By incorporating these detailed slides and emphasizing **AWS Step Functions** as the central orchestrator, your presentation will provide a comprehensive and engaging overview of RefVision’s serverless architecture. This approach will resonate well with your Level 200 serverless meetup audience, showcasing both your technical expertise and the robust design of your solution.

Good luck with your presentation!