---
marp: true
theme: default
class: lead
paginate: true
---

<!-- Slide 1: Title Slide -->
# **RefVision: Bringing VAR to Powerlifting**

**Michael Kingston**  
**email: michael.kenneth.kingston@gmail.com**
LinkedIn: [Michael Kingston](https://www.linkedin.com/in/michael-kenneth-kingston)

**Tagline:** *“Ensuring Fairness and Transparency in Powerlifting”*

---

<!-- Slide 2: Agenda -->
# Agenda

1. **Introduction**
2. **Problem Statement**
3. **Proposed Solution**
4. **Deep Dive into Serverless Components**
5. **Architecture Walkthrough**
6. **Challenges and Solutions**
7. **Future Enhancements & Roadmap**
8. **Q&A**

---

<!-- Slide 3: Introduction -->
# 1. Introduction

**Context**: In sports like football and tennis, Video Assistant Referees are common and well established. In powerlifting, disputes often arise over judging decisions.

**My Goal**:
- Use ML to to provide real-time, impartial video analysis for lifters and referees.
- Leverage a serverless architecture for deployment
- Provide an impartial appeal mechanism for lifters & add excitement for spectators.

**Key Takeaway**: We’ll explore how AWS serverless components can orchestrate this pipeline efficiently, scaling up when needed and scaling down to near-zero when idle.

<!-- presenter note -->

---

<!-- Slide 4: Problem Statement -->
# 2. Problem Statement

- **Contentious Decisions**: Referees often disagree with lifters and their coaches about “No Lift” calls.
- **Lack of Appeals**: No effective formal mechanism for lifters to challenge 
  disputed calls.
- **Rising Stakes**: Prize money, records, and fan engagement are at risk, increasing the tensions around contentious decisions.
- **Impact on Sport Integrity**: Unresolved disputes can tarnish the sport’s reputation and detract from audience enjoyment.

---

<!-- Slide 4: Example -->
# An example of a contentious decision
<p style="text-align: center;">
  <video width="800" height="450" controls>
    <source src="Keeta_squat_1.mp4" type="video/mp4">
    Your browser does not support the video tag.
  </video>
</p>

<!-- presenter note
Do you think this was a good lift or a no lift?

The judges decided that it was high, and therefore no lift. That cost this 
lifter first place, and $20,000 in prize money.
-->

---

<!-- Slide 5: Proposed Solution -->
# 3. Proposed Solution: RefVision VAR

**RefVision**: a layer of objective fairness and drama to powerlifting competitions.
1. **Supplemental**: Works alongside human referees, not replacing them.  
2. **Appeal Mechanism**: Lifters get one appeal per meet for a “Video Review.”
3. **Impartial Analysis**: ML models provide objective lift evaluations.
4. **Enhanced Engagement**: Real-time visual overlays and natural explanations bring the audience closer to the action.

**Key Features**:
- Pose estimation for precise lift judging.  
- Automated “Good Lift” / “No Lift” classification.  
- Natural language explanations (AWS Bedrock).

---

<!-- Slide 6: Why Serverless Architecture -->
# Why Serverless?

- **Pay-As-You-Go**: Competitions don't happen every day. Serverless is ideal 
  for intermittent usage, because you only pay for compute during event days.
- **Scalability**: Auto-scales for high traffic on meet day; scales down to near-zero when idle.
- **Reduced Maintenance**: Less time spent managing servers or complex infrastructure.

---
<!-- Slide 7: Challenges to Serverless Architecture -->

# The Main Challenge:  
- **Accelerator Needs**: effective real-time CV video inference demands accelerators
- The delay required to run inference on CPU is unacceptable.
- Pure serverless accelerators (like we have for LLM with Bedrock) don’t exist natively on AWS **yet**.

**Solution**:  
- **Hybrid Approach**: AWS SageMaker endpoints + ECS Fargate for accelerator-based tasks with scale-to-zero configurations.
- **Options**: AWS has its own accelerators (Inf1, Inf2) for SageMaker endpoints, and they are **REALLY GOOD**

<!-- presenter note
- For comparison, each frame takes 1000ms to process on a CPU, but <10ms with an accelerator.
- A lift requires approx 800 frames to be processed, assuming 1080p video at 30fps.
- This means a lift would take 13min to process on a CPU, but 8s on an accelerator.
- I really like Inf2 because they are as fast as an H100 cluster but up to 75% cheaper. They are also much more available
- the only downside is that you need to learn some new tools to make it work. I don't see that as a major issue, but it is something to consider.
- inf2 is available in ap-southeast-2, but you have to apply for access. a small demand is approved automatically
-->

---

<!-- Slide 8: Deep Dive into Serverless Components (intro) -->
# 4. Deep Dive into Serverless Components

We’ll highlight how each AWS service fits into the pipeline:
1. Video Ingestion & Preprocessing **(Kinesis, S3, Lambda)**  
2. Data Storage & Control **(DynamoDB)**  
3. Workflow Orchestration **(Step Functions)**  
4. Inference **(SageMaker, ECS Fargate)**  
5. Explanation Generation **(AWS Bedrock)**  
6. Web App & Delivery **(Flask, CloudFront)**

---

<!-- Slide 9: Video Ingestion & Preprocessing -->
## 4.1 Video Ingestion & Preprocessing

**Workflow**:
1. **Trigger**: an audio trigger starts the step function, and the video stream starts.
2. **Lift Data**: the meet software sends a JSON payload with lifter data 
   (name, lift, attempt number, etc.) at the same time as the video stream.
3. **Camera Feeds → Kinesis Video Streams**: Real-time streaming of video
4. **Preprocessing**: Firehose performs real-time cropping, resizing, and video format transformations
5. **Storage**: Kinesis stores the video in **S3** bucket
6. **DynamoDB**: Records metadata (lifter data, timestamps, chunk references).  
7. **AWS Lambda**: multiple triggers for kinesis & firehose, and updates DynamoDB.

<!-- presenter note
**Why**:
- Kinesis streams live video.
- Firehose pre-processes video on the fly. Different cameras generate different video formats and contain different metadata that can mess up our inference. we need to  convert all video files to mp4 and strip all metadata before inference
- we store the original videos separately from the processed videos, because they're usefule for further fine tuning of existing models and development of new models
- DynamoDB tracks all the metadata for each lift.
- the step function coordinates everything
-->
---

<!-- Slide 10: DynamoDB -->
## 4.2 DynamoDB

- **Purpose**: Central store for Lifter and lift data, video metadata, processing states, inference results, decision, natural language explanations.
- **Data Model**:  
  - **Partition Key**: `LifterID_LiftID`  
  - **Sort Key**: `datatype_timestamp`

| Partition Key | Sort Key                    | Metadata                |
|---------------|-----------------------------|-------------------------|
| 12345_Squat1  | Video_20240216T123456       | Preprocessed frame data |
| 12345_Squat1  | Inference_20240216T123456   | Inference results       |
| 12345_Squat1  | Decision_20240216T123456    | “Good Lift” / “No Lift” |
| 12345_Squat1  | Explanation_20240216T123456 | LLM explanation         |

<!-- presenter note
why do we need a store of state?

In RefVision, we're dealing with multiple asynchronous serverless 
components that need to coordinate video ingestion, preprocessing, inference, explanation generation, and result storage. DynamoDB serves as a centralised store of state, ensuring smooth orchestration and tracking across different AWS services.

partition key

sort key
-->
---

<!-- Slide 10: AWS Step Functions -->
## 4.3 AWS Step Functions

**Key Features**:
1. **Visual Workflows**: Easy to monitor states.  
2. **State Management**: Maintains the context for each video segment.  
3. **Error Handling**: Retries and catchers for robust failover.  

**Configuration**:
- **States**:
  1. **Streaming** (Kinesis)
  2. **Preprocessing** (Firehose)
  3. **Inference** (SageMaker/ECS)
  4. **Explanation** (Bedrock)  
  5. **Metadata Storage** (DynamoDB) at each step
- **Transitions**: Each step triggers the next upon successful completion or retries on failure.

<!-- presenter note
Role: Central Orchestrator for the entire pipeline.

Why: Eliminates “spaghetti code” for orchestrating multiple services. is used to orchestrate the RefVision pipeline because it provides a serverless, reliable, and fault-tolerant way to manage the different stages of video processing, inference, and explanation generation.

the Step function is the conductor
DynamoDB is the state memory store

The step function:
✅ Handles Failures & Retries Automatically → If a step fails, Step Functions can retry without reprocessing everything.
✅ Ensures Proper Execution Order → Each step runs only when the previous one completes successfully.
✅ Integrates Seamlessly with DynamoDB → It checks the processing state in DynamoDB and triggers the next action when ready.
✅ Reduces Code Complexity → Instead of managing state manually in multiple Lambda functions, Step Functions visually define the execution flow.
-->

---

<!-- Slide 11: Inference with SageMaker & ECS -->
## 4.4 Inference (SageMaker)

1. **SageMaker Endpoint**: Hosts YOLO11 pose model with accelerator support.
2. **DynamoDB**: Updated with classification results (e.g., “Good Lift” vs. “No Lift”).  

**Why**:
- an **Accelerator** is necessary for efficient pose estimation.

<!-- presenter note
- this is the only non-serverless part of the pipeline.
- I tried many workarounds to make this serverless, but was unsuccessful
- I'm hoping that AWS will release a serverless accelerator soon. This could be done on lambda.
-->

---

<!-- Slide 12: Explanation Generation with AWS Bedrock -->
## 4.5 Explanation Generation (Bedrock)

- **Lambda** triggers once classification is available.  
- **Bedrock** (Claude) transforms the decision and keypoints into a natural explanation:
  > “This squat was a ‘No Lift’ because the lifter’s hip crease was 2 cm above the knee.”

- **DynamoDB** stores the explanation for retrieval by the web app.

<!-- presenter note
in most cases the visual explanation provided by the skeleton overlay is 
enough to see why the lift failed, however there are a lot of reasons (30) 
why a lift might fail, that may not be immediately obvious to the audience. 

Its also really helpful to the commentator to have an explanation to hand 
to explain a decision to the audience, even if the lifter has not chosen to 
appeal the lift
-->
---

<!-- Slide 13: Web App & Delivery -->
## 4.6 Web App & Delivery (Flask + CloudFront)

- **Flask** (or FastAPI): Provides APIs and the front-end to display annotated videos and results.  
- **AWS CloudFront**: Delivers static content (annotated videos, web assets) globally with low latency.  
- **UI**: Judges can watch the replay, see keypoints, read the LLM explanation, and even override decisions if needed.

---

<!-- Slide 14: Architecture Walkthrough -->
# 5. Architecture Walkthrough

**Comprehensive Flow**:
1. **Live Capture**: Camera → Kinesis → S3  
2. **Preprocessing**: Lambda triggered by DynamoDB  
3. **Step Functions**: Coordinates inference steps  
4. **Inference**: Pose detection via SageMaker
5. **Explanation**: AWS Bedrock → DynamoDB  
6. **Annotated Video**: S3 for final media  
7. **Web App**: Displays decisions, explanations

---

<!-- Slide 15: Diagram -->

**Diagram**:  
- Show an arrow-based flow with Step Functions in the center orchestrating each step, referencing S3, Lambda, SageMaker, ECS, DynamoDB, and Bedrock.

---

<!-- Slide 15: Challenges and Solutions -->
# 6. Challenges & Solutions

**1. Accelerators in Serverless**  
   - **Compromise Solution**: SageMaker endpoints for inference
   - A better solution would be for AWS to offer accelerator-enabled serverless.

**2. Streaming**  
   - **Solution**: Kinesis for quick ingestion, firehose for preprocessing, and Step Functions for orchestration.

**3. State Management**  
   - **Solution**: DynamoDB to track each chunk/frame’s status; Step Functions to orchestrate transitions.

**4. Natural Language Explanations**  
   - **Solution**: AWS Bedrock for quick, context-aware text generation; triggers from Step Functions or Lambda.

---

<!-- Slide 16: output -->

# Output: Annotated video with skeleton overlay
<p style="text-align: center;">
  <video width="800" height="450" controls>
    <source src="theo_maddox_squat_2.mp4" type="video/mp4">
    Your browser does not support the video tag.
  </video>
</p>

---

<!-- Slide 17: Future Improvements -->
# 7. Future Improvements

1. **Architecture**:
   - there are **many** parts of the current architecture that can be improved to make the system more robust, efficient and cost-effective. I need to 
     keep working on it to make it more efficient, cost-effective and robust.

2. **Models**:
   - **Classifier model**: The pipeline needs an effective classifier model to identify the lifter and only focus on the lifter. 
   - **Fine-tuning Yolo11**: Yolo11 is a great model for pose estimation, but it is not perfect for this application. 

3. **Accuracy Improvements**  
   - 3x camera setups are required to better emulate how all 3 judges see 
     the lift. 

4. **Expand Beyond Powerlifting**  
   - Weightlifting (snatch, clean & jerk)
   - Exercise physiology and rehabilitation

5. **Multiple and Multi-Region Deployments**
   - For large and international meets, i need to be able to run 
     concurrent systems with minimal latency.

<!-- presenter note
As you can see from the demonstration, the model struggles to focus on the lifter when there are multiple people in the frame. It also struggles with occlusion. The solution is relatively straightforward: the lifter is the person holding the  barbell. However, computer vision models for video are generally trained on COCO, and "barbell" is not a class in COCO.

Many of the rules in powerlifting are more nuanced than comparing relative keypoints at a moment in time and require fine turning on a custom, labelled dataset to judge failures based on all modalities.

It would be a legitimate criticism to say that the current tool is biased 
because it looks from only one angle. This needs to be corrected. we need 
to use 3 cameras to capture the lift from the perspective of all 3 judges.
-->

---

<!-- Slide 16: Future Improvements -->
**Next Steps**  
1. Recording video from the perspective of all 3 judges.
2. labelling a custom dataset for fine tuning Yolo11
3. Training a classifier model to identify the lifter based on the barbell
4. ongoing testing and validation of the system privately at meets
5. ongoing iterative improvement of the architecture

---

<!-- Slide 17: Q&A -->
# Q&A


*Thank You!*  
Contact: **michael.kenneth.kingston@gmail.com**

---
