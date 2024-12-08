Amazon Bedrock provides access to various foundation models, including some with multimodal capabilities that can process both text and images. Notably, Meta's Llama 3.2 models, available through Amazon Bedrock, support vision tasks by integrating image encoder representations into the language model. 

However, Amazon Bedrock does not natively support video processing. For tasks involving video analysis, such as assessing the depth of a squat in a powerlifting competition, AWS offers other services like Amazon Rekognition. Amazon Rekognition is designed for video analysis and can detect objects, activities, and scenes within videos. It requires videos to be encoded using the H.264 codec and formatted as either MPEG-4 or MOV. 

To achieve your specific goal of evaluating squat depth in powerlifting competitions, you could develop a custom computer vision model using AWS services like Amazon SageMaker for model training and deployment, and Amazon Rekognition for video analysis. This approach would allow you to process video data and perform the necessary analysis to judge squat depth.

In summary, while Amazon Bedrock offers multimodal models capable of processing images, it does not support video processing. For video analysis tasks, leveraging other AWS services such as Amazon Rekognition and Amazon SageMaker would be more appropriate. 

You’re correct that identifying key points such as the hip, knee, and floor makes this a **pose estimation** problem. Here’s a breakdown of baseline models and frameworks you could consider, along with some alternative framings:

we'll use Claude which is available on bedrock for the language component of this application

---

### **Pose Estimation Models**

1. **MediaPipe**
   - **Strengths**: Lightweight, real-time, and provides body landmarks with high accuracy.
   - **Limitations**: May struggle with certain complex or occluded poses. Limited customizability for unique use cases like powerlifting.
   - **Why it fits**: Out-of-the-box keypoint detection makes it a fast and simple option for initial prototyping.

2. **OpenPose**
   - **Strengths**: High-accuracy pose estimation. Captures 135 keypoints, including hands and feet.
   - **Limitations**: Computationally expensive; requires a strong GPU.
   - **Why it fits**: OpenPose has been used in sports analysis due to its rich keypoint set and ability to process multiple individuals.

3. **YOLO-based Keypoint Detection (e.g., YOLOv7 Pose)**
   - **Strengths**: Combines object detection and pose estimation in a single model. YOLO's architecture is lightweight and fast.
   - **Limitations**: Lower accuracy compared to specialized models like OpenPose.
   - **Why it fits**: YOLO-style models excel when speed and ease of deployment are crucial.

4. **DeepLabCut**
   - **Strengths**: Designed for scientific use cases, particularly for motion analysis and biomechanics.
   - **Limitations**: Requires labeled training data specific to your task. Not real-time without optimization.
   - **Why it fits**: Offers a highly customizable framework for analyzing squat depth with tailored accuracy.

5. **HRNet (High-Resolution Network)**
   - **Strengths**: State-of-the-art performance in pose estimation; balances speed and accuracy well.
   - **Limitations**: Requires significant computational resources for high-res input.
   - **Why it fits**: Provides fine-grained keypoint detection, which is ideal for nuanced biomechanics tasks.

---

### **Alternative Framings**

1. **Object Detection + Keypoint Estimation**
   - Use an object detection model (e.g., YOLOv8 or Faster R-CNN) to detect the person and then run pose estimation within the bounding box.
   - Pros: Modular and allows optimization of person detection separately.
   - Cons: Slower than unified models like YOLO Pose.

2. **Depth Estimation Models**
   - Incorporate monocular depth estimation models (e.g., DPT, MiDaS) to determine relative joint height with respect to the floor in 3D space.
   - Pros: Removes ambiguity about camera angles and plane alignment.
   - Cons: Computationally intensive; requires careful calibration.

3. **Video-Based Temporal Models**
   - Use spatiotemporal models like PoseFormer (a transformer for pose estimation) to analyze the entire movement sequence rather than individual frames.
   - Pros: Captures dynamics of the squat over time, reducing misclassification from a single frame.
   - Cons: Requires longer input sequences and more processing.

---

### **Other Potential Approaches**

- **Classify Squats Directly with a Custom Model**
   - Instead of explicitly tracking keypoints, train a neural network to classify squats as "to depth" or "not to depth" directly from video or pose data. Use 3D Convolutional Neural Networks (3D-CNNs) or LSTMs for video sequence input.
   - Pros: Simplifies the task; avoids potential errors from pose estimation.
   - Cons: May require a large labeled dataset to train effectively.

- **Hybrid Approaches**
   - Combine pose estimation with rule-based systems. For example:
     - Detect keypoints using MediaPipe or OpenPose.
     - Apply biomechanical rules to decide depth.

---

### Recommendations for a Baseline
1. **Start with MediaPipe** for its simplicity and speed, especially for prototyping. 
2. Evaluate **YOLOv7 Pose** if you want a fast and integrated solution for both detection and pose.
3. Transition to **HRNet or OpenPose** for higher accuracy if precision becomes critical.
4. Consider adding **3D depth estimation** with MiDaS or DPT if camera alignment variability is a concern.

This phased approach lets you iterate quickly while progressively refining your model and approach. Let me know if you'd like help setting up one of these solutions!

Yes, you can absolutely use **PoseFormer** in this manner! PoseFormer is a state-of-the-art spatiotemporal model for pose estimation and can be fine-tuned for specific use cases like assessing squat depth in powerlifting. Here’s how you can approach it:

---

### **Workflow to Use and Fine-Tune PoseFormer**

1. **Pretrained Model as a Baseline**
   - **Goal**: Establish a baseline by evaluating the pretrained PoseFormer on your squat dataset.
   - **Steps**:
     1. Load the pretrained PoseFormer model. Pretrained weights are typically available for datasets like **COCO** or **MPII Human Pose**.
     2. Run inference on your dataset to extract joint positions (e.g., hip, knee, floor position).
     3. Apply a rule-based logic to determine squat depth (e.g., hip joint lower than knee joint relative to the floor).
     4. Measure performance using metrics such as:
        - **Accuracy**: Correctly classified squats (to depth/not to depth).
        - **Precision/Recall**: Especially useful if data is imbalanced.

2. **Fine-Tuning the Model**
   - **Goal**: Adapt PoseFormer to your specific task and improve performance.
   - **Steps**:
     1. **Dataset Preparation**:
        - Label your dataset with keypoints (e.g., hip, knee) and optionally classifications (e.g., "to depth"/"not to depth").
        - Ensure diversity in camera angles, body types, and squat styles.
     2. **Fine-Tuning Process**:
        - Freeze early layers to retain the pretrained spatial understanding.
        - Modify and fine-tune the later layers for better temporal reasoning specific to squats.
        - Use a small learning rate (e.g., `1e-5` to `1e-4`) to avoid catastrophic forgetting.
     3. **Training Settings**:
        - Use a loss function like **Mean Squared Error (MSE)** for keypoints or **Cross-Entropy Loss** for classification.
        - Augment your training data with realistic transformations (e.g., slight rotations, noise, scaling) to improve robustness.

3. **Comparative Analysis**
   - Evaluate the **baseline pretrained model** and the **fine-tuned model** on the same test set.
   - Compare metrics such as:
     - Mean Per Joint Position Error (MPJPE): Average error in keypoint localization.
     - Classification Accuracy: For "to depth"/"not to depth."
     - Latency: For real-time applications.

---

### **How to Fine-Tune PoseFormer**

- **Frameworks**: PoseFormer is typically implemented in **PyTorch**. Check the original repository or variants for pretrained weights and training scripts.
- **Pretrained Weights**: Available for datasets like **COCO** and **Human3.6M**.
- **Dataset Annotation**:
  - Tools like **Label Studio** or **COCO Annotator** can help annotate your dataset for keypoints and/or labels.
  - If video is the input, ensure you generate labeled sequences with consistent temporal annotations.

---

### **Resources**

- **PoseFormer Official Repository**: [GitHub](https://github.com/yangsenius/PoseFormer)
  - Includes pretrained weights and training scripts.
- **Datasets**:
  - **COCO Keypoints**: General-purpose pose dataset.
  - **Human3.6M**: For 3D human pose estimation.
  - Consider creating a custom dataset if your task is domain-specific.

---

By comparing the pretrained and fine-tuned models, you’ll identify how much domain-specific adaptation improves performance and whether it justifies the effort for your application. Let me know if you'd like help with specific steps, like setting up the dataset or training scripts!

For a task like fine-tuning **PoseFormer** and running it near real-time, you will indeed need significant GPU resources, but a serverless approach can still work with proper planning. Here’s a breakdown of what you’ll need:

---

### **Compute Needs**

1. **Model Training (Fine-Tuning)**
   - **GPU Requirements**: 
     - PoseFormer is a transformer-based model, and fine-tuning it on video sequences is computationally intensive.
     - Recommended GPUs: 
       - **NVIDIA V100 (16 GB)**: Suitable for most fine-tuning tasks.
       - **NVIDIA A100 (40 GB)**: For faster training and handling larger batch sizes.
     - **Duration**:
       - Fine-tuning on a dataset with a few thousand video sequences could take a few hours to a few days depending on GPU type and dataset size.
   - **Options**:
     - Use **AWS EC2 instances** with GPUs (e.g., P3 or P4 instances).
     - Alternatively, use **AWS SageMaker** with a managed GPU instance for training. While it’s not serverless, it scales well for training workloads.

2. **Inference (Near Real-Time Inference)**
   - **GPU Requirements**:
     - Running PoseFormer for near real-time inference requires a lightweight, optimized deployment environment.
     - Consider **T4 GPUs** for cost-effective inference workloads.
   - **Latency**:
     - PoseFormer can process a single video frame sequence in about 20-50ms on modern GPUs, depending on optimizations and sequence length.
   - **Options**:
     - Deploy on **Amazon ECS or Fargate with GPU support** for a serverless-like architecture.
     - Alternatively, use **AWS Lambda with GPUs** via **Lambda’s container support**, which allows you to run GPU-enabled workloads with frameworks like PyTorch.

---

### **Serverless GPU Deployment Options**

1. **Amazon ECS/Fargate with GPUs**
   - **Why It Fits**: ECS and Fargate support GPU-enabled containers, providing a managed environment that scales based on workload.
   - **Steps**:
     1. Build a Docker container with the PoseFormer model and PyTorch environment.
     2. Configure the container to run inference for batches of frames.
     3. Use an event-driven architecture (e.g., AWS SQS or EventBridge) to queue incoming video sequences for processing.
     4. Deploy to Fargate with GPU resources.
   - **Costs**: Pay only for the time the container is active, which aligns with serverless principles.

2. **AWS Lambda with GPU Support**
   - AWS Lambda does not natively support GPUs, but you can use **Lambda's container image support** to run GPU-based workloads in a highly ephemeral, serverless environment.
   - **Considerations**:
     - Keep models lightweight or split tasks into smaller subtasks due to Lambda's execution time limits (15 minutes max).
     - Use pre-optimized or distilled versions of PoseFormer to reduce inference time.

3. **Amazon SageMaker Endpoint with Auto-Scaling**
   - While not strictly serverless, **SageMaker Endpoints** can scale to zero when idle (via manual teardown or cost optimization strategies).
   - **Steps**:
     1. Deploy the fine-tuned PoseFormer model as a SageMaker endpoint.
     2. Configure auto-scaling rules based on request volume.

---

### **Suggestions for Real-Time Inference**

- **Preprocessing**:
  - Preprocess video streams to extract sequences of frames and batch them efficiently. This reduces overhead and ensures the model focuses only on relevant frames.
- **Optimization**:
  - Use model optimization techniques like **TorchScript**, **ONNX Runtime**, or **TensorRT** to reduce inference time and GPU memory requirements.
- **Edge Case**:
  - If real-time performance is paramount, deploy PoseFormer on an **edge device** with a GPU (e.g., NVIDIA Jetson) to eliminate latency from cloud communication.

---

### **Recommended AWS Workflow**

1. **Training**:
   - Use **EC2 GPU instances** or **SageMaker with GPU** for training PoseFormer. Opt for on-demand instances to save costs.
2. **Inference**:
   - Deploy on **Amazon ECS/Fargate with GPUs** for a serverless inference pipeline.
   - Use **AWS S3 for video storage** and **SQS for event-driven processing** to trigger inference jobs.

By combining these approaches, you can build a robust, scalable, and cost-effective architecture that meets near-real-time requirements without compromising on serverless principles. Let me know if you'd like detailed steps for any part!

---
Your plan is solid and outlines a sophisticated yet achievable architecture for the task. Here’s an expanded version of your plan, structured into components and workflow steps:

---


---

This architecture is modular, scalable, and serverless where possible. It’s well-suited to your use case and ensures both efficiency and explainability. Let me know if you'd like detailed steps for implementing any part of it!

Great! Let’s start with **Step 1: Video Ingestion and Preprocessing**. Here's a detailed plan for this step:

---

### **Step 1: Video Ingestion and Preprocessing**

#### **Goal**
To set up a pipeline that:
1. Streams video data from a camera to AWS.
2. Preprocesses video frames for inference while storing raw and processed data in S3.

---

### **1.1. Video Ingestion**

#### **Components**
- **AWS Kinesis Video Streams**: Capture live video feed from cameras.
- **S3 Bucket**: Store video segments and preprocessed frames.

#### **Steps**
1. **Set Up Kinesis Video Stream**:
   - Create a Kinesis Video Stream to receive video data from the camera.
   - Use a Kinesis SDK (Python or compatible library) on the client device (camera system) to send the video feed to Kinesis.
     - Codec: H.264
     - Container format: MPEG-4 or MKV
     - Resolution: Adapt based on need (e.g., 720p for efficiency).
   - **Resources**:
     - AWS CLI: `aws kinesisvideo create-stream --stream-name "PowerliftingMeet"`
     - Kinesis Producer SDK for Python: Integrate with the camera feed.

2. **Configure Data Retention**:
   - Set a retention period (e.g., 24 hours) in Kinesis to temporarily store the video stream.

3. **Stream to S3**:
   - Set up an **AWS Lambda function** triggered by the Kinesis Video Stream to save video chunks to an S3 bucket.
   - Lambda writes the video chunks with a structured naming convention:
     - `s3://meet-id/squat-id/video-{timestamp}.mp4`

---

### **1.2. Preprocessing Video Frames**

#### **Components**
- **AWS Lambda**: Lightweight preprocessing triggered by video uploads.
- **S3 Bucket**: Store preprocessed frames for inference.
- **DynamoDB**: Record metadata for frames (e.g., frame IDs, timestamps).

#### **Steps**
1. **Lambda Trigger**:
   - Configure an S3 event notification to invoke a Lambda function when new video chunks are uploaded.

2. **Frame Extraction**:
   - Use Python libraries like OpenCV or FFmpeg within the Lambda function to:
     - Extract frames at regular intervals (e.g., 30 frames per second or keyframes only).
     - Optionally, resize and crop frames to the desired input size for the model (e.g., 256x256).

   ```python
   import cv2
   import boto3

   s3 = boto3.client('s3')

   def extract_frames(video_path, output_path, frame_rate):
       cap = cv2.VideoCapture(video_path)
       count = 0
       success, image = cap.read()
       while success:
           if int(cap.get(cv2.CAP_PROP_POS_FRAMES)) % frame_rate == 0:
               cv2.imwrite(f"{output_path}/frame-{count}.jpg", image)
               count += 1
           success, image = cap.read()
       cap.release()
   ```

3. **Store Frames**:
   - Save extracted frames in S3 under a structured path:
     - `s3://meet-id/squat-id/frame-{timestamp}.jpg`

4. **Record Metadata**:
   - Update DynamoDB with metadata for each frame:
     - Frame ID, timestamp, S3 location, and status ("preprocessed").

```python
import boto3

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('PowerliftingMeet')

def update_metadata(meet_id, squat_id, frame_id, s3_location):
   table.put_item(
       Item={
           'MeetID': meet_id,
           'SquatID': squat_id,
           'FrameID': frame_id,
           'S3Location': s3_location,
           'Status': 'Preprocessed'
       }
   )
```

---

### **1.3. Testing and Validation**

#### **Test Cases**
1. Simulate video streaming from a local camera to Kinesis.
2. Verify video chunks are uploaded to S3.
3. Confirm that Lambda is triggered correctly and:
   - Frames are extracted.
   - Preprocessed frames are saved in S3.
   - Metadata is recorded in DynamoDB.

#### **Metrics for Success**
- Frame extraction rate (e.g., extracting 90% of expected frames).
- Latency between video upload and frame extraction.
- Correctness of DynamoDB records.

---

### **1.4. Optimization**

1. **Performance**:
   - Use multi-threading or multiprocessing in Lambda for efficient frame extraction.
   - Optimize Lambda memory and runtime to handle larger video chunks.

2. **Cost Control**:
   - Use lifecycle policies on S3 to delete raw video chunks after preprocessing.
   - Ensure extracted frames are stored in cost-efficient S3 tiers (e.g., S3 Standard-Infrequent Access).

---

### **Deliverables for Step 1**
- **Kinesis Video Stream** configured and receiving video data.
- **S3 Bucket** storing raw video chunks and preprocessed frames.
- **AWS Lambda Function** extracting frames and saving metadata in DynamoDB.
- Test logs verifying the correctness of each component.

---

Do you want to proceed with any specific sub-step, or should I provide resources and further details for implementation?

### **Step 2: Inference Pipeline**

#### **Goal**
To set up a pipeline that:
1. Uses preprocessed frames from **S3** as input for inference.
2. Employs **AWS SageMaker Endpoints** for running the PoseFormer model to extract keypoints and assess squat depth.
3. Records inference results in **DynamoDB**.

---

### **2.1. SageMaker Endpoint for PoseFormer**

#### **Components**
- **AWS SageMaker**: Deploy the PoseFormer model for inference.
- **Model Optimization**: Use frameworks like ONNX or TorchScript to optimize PoseFormer for deployment.
- **AWS Lambda/Step Functions**: Invoke the model and handle orchestration.

#### **Steps**
1. **Prepare the Model**:
   - Optimize PoseFormer for inference:
     - Export the trained model to ONNX or TorchScript for faster execution.
     - Validate the exported model locally.

     ```python
     import torch
     model = torch.load('poseformer.pth')
     scripted_model = torch.jit.script(model)
     scripted_model.save('poseformer_scripted.pt')
     ```

2. **Deploy to SageMaker**:
   - Package the optimized model and create a SageMaker endpoint:
     - Use a SageMaker **PyTorch Model** to deploy the model.
     - Enable GPU inference for real-time performance.

```bash
aws sagemaker create-model --model-name PoseFormerEndpoint --primary-container \
'{"Image": "763104351884.dkr.ecr.us-west-2.amazonaws.com/pytorch-inference:1.10.2-gpu-py38-cu113-ubuntu20.04", "ModelDataUrl": "s3://model-bucket/poseformer_scripted.pt"}'
```

3. **Auto-Scaling and Cost Control**:
   - Configure the SageMaker endpoint to scale down when idle:
     - Use **Multi-Model Endpoints** if you plan to host multiple models.
   - Set a lifecycle policy to pause or terminate the endpoint during non-competition times.

---

### **2.2. Orchestration with AWS Step Functions**

#### **Components**
- **Step Functions**: Orchestrate inference steps.
- **Lambda Functions**: Manage requests to the SageMaker endpoint.
- **DynamoDB**: Record inference results.

#### **Steps**
1. **Define the Step Function Workflow**:
   - Triggered when new frames are marked as "preprocessed" in DynamoDB.
- Steps:
  1. Retrieve frame metadata from DynamoDB.
  2. Invoke a Lambda function to send the frame to the SageMaker endpoint.
  3. Process the PoseFormer output:
     - Extract keypoints (hip, knee, floor).
     - Calculate squat depth classification ("to depth"/"not to depth").
  4. Store the results in DynamoDB.

  Example Step Function JSON:

```json
{
"StartAt": "InvokeLambda",
"States": {
  "InvokeLambda": {
    "Type": "Task",
    "Resource": "arn:aws:lambda:us-west-2:123456789012:function:InvokePoseFormer",
    "Next": "StoreResults"
  },
  "StoreResults": {
    "Type": "Task",
    "Resource": "arn:aws:lambda:us-west-2:123456789012:function:StoreInferenceResults",
    "End": true
  }
}
}
```

2. **Lambda Function for Inference**:
   - Load the frame from S3.
- Send the frame to the SageMaker endpoint and parse the response.

```python
import boto3
import json
from PIL import Image

sagemaker_runtime = boto3.client('sagemaker-runtime')

def invoke_poseformer(frame_s3_uri, endpoint_name):
  # Load frame from S3
  s3 = boto3.client('s3')
  bucket, key = frame_s3_uri.split('/', 1)
  response = s3.get_object(Bucket=bucket, Key=key)
  image = Image.open(response['Body'])

  # Convert image to bytes
  image_bytes = image.tobytes()

  # Invoke SageMaker endpoint
  response = sagemaker_runtime.invoke_endpoint(
      EndpointName=endpoint_name,
      ContentType='application/octet-stream',
      Body=image_bytes
  )
  return json.loads(response['Body'])
```

3. **Store Results in DynamoDB**:
   - Record keypoints and classification results for each frame:
     - Keypoints: `{hip: [x, y], knee: [x, y], floor: [y]}`
     - Classification: `"to depth"`/`"not to depth"`
     - Confidence scores.

---

### **2.3. Testing and Validation**

#### **Test Cases**
1. Run the Step Function with a sample frame:
   - Confirm the Lambda function invokes the SageMaker endpoint correctly.
   - Validate PoseFormer output against expected keypoints.
2. Check DynamoDB records for inference results.

#### **Metrics for Success**
- Average latency per frame for inference (target: <100ms).
- Accuracy of "to depth"/"not to depth" classifications.
- Consistency of DynamoDB records.

---

### **2.4. Optimization**

1. **Inference Speed**:
   - Batch multiple frames for inference to reduce endpoint invocation overhead.
   - Explore **AWS Elastic Inference** for cost-effective GPU acceleration.
2. **Data Management**:
   - Use **DynamoDB Streams** to monitor changes and trigger subsequent processes.
   - Delete preprocessed frames from S3 after inference if no longer needed.

---

### **Deliverables for Step 2**
- **SageMaker Endpoint** hosting the PoseFormer model.
- **Step Function** orchestrating frame-based inference.
- **DynamoDB** updated with keypoints and classifications.

---

Would you like to move to the next step or dive deeper into setting up any specific part of this step?

### **Step 3: Explanation Generation**

#### **Goal**
To use a language model to generate a clear, natural-language explanation for the squat depth decision based on PoseFormer’s output. Store the explanation alongside the classification in DynamoDB for later use in the web interface.

---

### **3.1. Explanation Pipeline**

#### **Components**
- **AWS Lambda**: Trigger explanation generation upon receiving inference results.
- **Language Model (e.g., OpenAI GPT via API, AWS Bedrock)**: Generate natural language explanations.
- **DynamoDB**: Store explanations with associated metadata.

---

### **3.2. Workflow**

#### **Steps**
1. **Lambda Trigger**:
   - Configure DynamoDB streams to trigger a Lambda function when new inference results are recorded.
- Example DynamoDB entry:

```json
{
"MeetID": "meet-001",
"SquatID": "squat-001",
"FrameID": "frame-003",
"Keypoints": {
  "Hip": [120, 200],
  "Knee": [150, 190],
  "Floor": 200
},
"Classification": "to depth",
"Confidence": 0.95
}
```

2. **Prepare Language Model Input**:
   - Format keypoints and classification into a structured prompt for the language model.
   - Example Prompt:
     ```
     Input:
     - Hip joint position: 120, 200
     - Knee joint position: 150, 190
     - Floor position: 200
     - Squat classification: "to depth"
     - Confidence: 95%

     Task:
     - Generate a concise explanation for this squat depth decision.
     ```
   - Output Example:
     ```
     The squat was classified as "to depth" because the hip joint reached 10 pixels lower than the knee joint relative to the floor. Confidence in this decision is 95%.
     ```

3. **Call Language Model**:
   - Use a pre-trained language model (AWS Bedrock’s Claude or Jurassic models) via an API call.
- Example Lambda function for explanation generation:
```python
import boto3

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('PowerliftingMeet')

def generate_explanation(event, context):
  for record in event['Records']:
      if record['eventName'] == 'INSERT':
          item = record['dynamodb']['NewImage']
          keypoints = item['Keypoints']
          classification = item['Classification']
          confidence = item['Confidence']

          # Generate explanation
          openai.api_key = "your-api-key"
          prompt = f"""
          Input:
          - Hip joint position: {keypoints['Hip']}
          - Knee joint position: {keypoints['Knee']}
          - Floor position: {keypoints['Floor']}
          - Squat classification: {classification}
          - Confidence: {confidence * 100}%

          Task:
          - Generate a concise explanation for this squat depth decision.
          """
          response = openai.Completion.create(
              engine="gpt-4",
              prompt=prompt,
              max_tokens=100
          )
          explanation = response['choices'][0]['text']

          # Update DynamoDB
          table.update_item(
              Key={'MeetID': item['MeetID'], 'SquatID': item['SquatID']},
              UpdateExpression="SET Explanation = :exp",
              ExpressionAttributeValues={':exp': explanation}
          )
```

4. **Store Explanation**:
   - Add the generated explanation to the corresponding DynamoDB record under the `Explanation` attribute.

---

### **3.3. Testing and Validation**

#### **Test Cases**
1. Simulate a DynamoDB update with a sample inference result.
   - Validate the Lambda function correctly triggers and formats the prompt.
   - Confirm the language model generates a coherent explanation.
   - Verify the explanation is written back to DynamoDB.

2. Test edge cases:
   - Low-confidence classifications.
   - Ambiguous keypoint positions.

#### **Metrics for Success**
- Completeness: All inference results generate corresponding explanations.
- Accuracy: Explanations align with the actual model outputs.
- Latency: Explanation generation completes within acceptable limits (e.g., <1 second per squat).

---

### **3.4. Optimization**

1. **Batch Processing**:
   - For high-volume meets, batch multiple inference results into a single API call to the language model to reduce costs and latency.

2. **Caching**:
   - If multiple frames from the same squat produce identical results, reuse the explanation instead of generating a new one.

3. **Cost Management**:
   - Use lightweight language models (e.g., AWS Bedrock models like Claude or Cohere Command) if the task does not require GPT-level complexity.

---

### **3.5. Deliverables for Step 3**
- **Lambda Function**: Generates natural-language explanations for squat decisions.
- **Language Model Integration**: API calls to OpenAI GPT or AWS Bedrock.
- **DynamoDB Updates**: Records explanations alongside inference results.

---

Let me know if you want to move to the next step or explore further implementation details for explanation generation!

### **Step 4: Web-Based Application**

#### **Goal**
To build a user-friendly web application for judges and organizers to review results, replay annotated videos, and access the model's decisions and explanations.

---

### **4.1. Application Features**

1. **Real-Time Updates**:
   - Display live results from the ongoing meet (e.g., squat classifications, confidence scores).
2. **Annotated Video Replay**:
   - Allow users to replay annotated video segments with keypoints and visual overlays.
3. **Explanations**:
   - Show the generated explanations for the model’s decisions.
4. **Manual Overrides**:
   - Enable judges to override decisions if necessary, recording manual corrections in DynamoDB.
5. **User Authentication**:
   - Use AWS Cognito to manage secure access for judges and organizers.

---

### **4.2. Technology Stack**

1. **Frontend**:
   - Framework: **React.js** or **Streamlit** (for rapid development).
   - Visualization Libraries: **D3.js** or **Plotly** for keypoint overlays and metrics.
2. **Backend**:
   - Framework: **Flask** or **FastAPI** for API endpoints.
   - Database: **DynamoDB** for fetching and updating meet data.
3. **Video Streaming**:
   - Host annotated videos in **S3** and serve through **CloudFront** for low-latency playback.

---

### **4.3. Workflow**

#### **Frontend**
1. **Dashboard**:
   - Display the meet overview: lifter names, attempts, and results.
   - Provide filters (e.g., lifter, attempt, squat classification).
2. **Video Player**:
   - Embed a video player (e.g., Video.js) to play annotated videos stored in S3.
   - Overlay keypoints and decisions on the video using preprocessed annotations.

   Example: 
   - Draw keypoints and lines using an HTML `<canvas>` over the video.

```javascript
const canvas = document.getElementById('overlay');
const ctx = canvas.getContext('2d');
ctx.beginPath();
ctx.moveTo(hip.x, hip.y);
ctx.lineTo(knee.x, knee.y);
ctx.stroke();
```

3. **Decision Panel**:
   - Show:
     - Squat classification (e.g., "to depth").
     - Confidence score (e.g., 95%).
     - Model-generated explanation.
   - Include a button for judges to override decisions.

---

#### **Backend**
1. **API Endpoints**:
   - Fetch meet data:
     - **GET /meet/{meet_id}/results**: Return all attempts and classifications for a meet.
   - Fetch video metadata:
     - **GET /squat/{squat_id}/video**: Return S3 URL for the annotated video.
   - Update overrides:
     - **POST /squat/{squat_id}/override**: Update a manual correction.

   Example FastAPI code:

```python
from fastapi import FastAPI
import boto3
from boto3 import dynamodb
import json

app = FastAPI()

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('PowerliftingMeet')

@app.get("/meet/{meet_id}/results")
def get_results(meet_id: str):
   response = table.query(
       KeyConditionExpression="MeetID = :meet_id",
       ExpressionAttributeValues={":meet_id": meet_id}
   )
   return response['Items']

@app.post("/squat/{squat_id}/override")
def override_decision(squat_id: str, classification: str):
   table.update_item(
       Key={'SquatID': squat_id},
       UpdateExpression="SET Classification = :cls, ManualOverride = :mo",
       ExpressionAttributeValues={
           ':cls': classification,
           ':mo': True
       }
   )
   return {"status": "success"}
```

2. **Data Pipeline**:
   - Use DynamoDB to track:
     - Frame-level annotations.
     - Squat classifications and explanations.
     - Overrides and their timestamps.

---

### **4.4. Deployment**

1. **Frontend Deployment**:
   - Use **AWS Amplify** for hosting the React.js frontend or Streamlit app.
   - Configure **CloudFront** for content distribution.

2. **Backend Deployment**:
   - Host the Flask/FastAPI application on **AWS Lambda** using a serverless framework like **Zappa** or **AWS API Gateway**.

---

### **4.5. Testing and Validation**

1. **Frontend Testing**:
   - Verify that video playback with overlays works across browsers.
   - Ensure filters and sorting on the dashboard function correctly.

2. **Backend Testing**:
   - Test all API endpoints for correctness and error handling.
   - Simulate manual overrides and validate updates in DynamoDB.

3. **End-to-End Testing**:
   - Simulate a meet, process video segments, and confirm real-time updates in the web app.

---

### **4.6. Optimization**

1. **Caching**:
   - Use **AWS CloudFront** to cache video segments and metadata for faster access.
2. **UI Performance**:
   - Optimize overlays to render smoothly, especially on low-power devices.
3. **Real-Time Data**:
   - Use **WebSockets** or **AWS AppSync** to push updates to the web app in real-time.

---

### **Deliverables for Step 4**
- **Frontend**: Web app for real-time results, video replay, and overrides.
- **Backend**: API for fetching and updating meet data.
- **Integration**: Full pipeline connecting video annotations, model decisions, and user interactions.

---

Should we proceed to **Step 5: Integration and Orchestration**, or focus further on this step?

You're absolutely right—let's reassess! Here's how we tie everything together in **Step 5: Integration and Orchestration**.

---

### **Step 5: Integration and Orchestration**

#### **Goal**
To connect all components of the system into a cohesive pipeline that efficiently handles data ingestion, preprocessing, inference, explanation generation, and user interface updates, ensuring a seamless workflow during a powerlifting meet.

---

### **5.1. Central Orchestration with AWS Step Functions**

#### **Components**
- **Step Functions**: Coordinate end-to-end workflows.
- **DynamoDB**: Serve as the central state store.
- **AWS Lambda**: Handle logic at each step.

---

#### **Workflow**
1. **Trigger Events**:
   - Preprocessing starts when video is uploaded to **S3**.
   - Inference and explanation generation are triggered when preprocessed data is recorded in **DynamoDB**.
   - The web app is updated as soon as new results are available.

2. **State Management**:
   - Use **DynamoDB** to track:
     - Video ingestion status (uploaded, preprocessed, etc.).
     - Inference status (pending, complete).
     - Explanation status (generated, pending user review).
     - Manual overrides.

3. **End-to-End Step Function**:
   - Define states for the full pipeline:
     1. Video Uploaded → Preprocessing Triggered.
     2. Preprocessed → Inference Triggered.
     3. Inference Complete → Explanation Triggered.
     4. Explanation Complete → Web App Update.

   Example Step Function Definition:
```json
{
 "StartAt": "Preprocessing",
 "States": {
   "Preprocessing": {
     "Type": "Task",
     "Resource": "arn:aws:lambda:region:account:function:PreprocessVideo",
     "Next": "Inference"
   },
   "Inference": {
     "Type": "Task",
     "Resource": "arn:aws:lambda:region:account:function:RunInference",
     "Next": "GenerateExplanation"
   },
   "GenerateExplanation": {
     "Type": "Task",
     "Resource": "arn:aws:lambda:region:account:function:GenerateExplanation",
     "Next": "UpdateWebApp"
   },
   "UpdateWebApp": {
     "Type": "Task",
     "Resource": "arn:aws:lambda:region:account:function:UpdateFrontend",
     "End": true
   }
 }
}
```

---

### **5.2. Real-Time Updates**

#### **Components**
- **AWS AppSync** or **WebSockets**: Push updates to the web app when new data is available.
- **DynamoDB Streams**: Monitor changes in DynamoDB and trigger real-time updates.

#### **Steps**
1. Configure DynamoDB Streams:
   - Monitor specific tables (e.g., "PowerliftingMeet") for changes (e.g., new classifications or explanations).
   - Trigger a Lambda function to publish updates via AppSync or WebSockets.

2. Web App Updates:
   - Push new data to the frontend dashboard, ensuring judges and organizers see real-time results.

---

### **5.3. Error Handling and Retries**

1. **Step Functions**:
- Include retry policies in the workflow for tasks like inference and explanation generation:
```json
"Retry": [
{
  "ErrorEquals": ["States.TaskFailed"],
  "IntervalSeconds": 5,
  "MaxAttempts": 3,
  "BackoffRate": 2.0
}
]
```

2. **DynamoDB Flags**:
   - Mark failed processes with a "status" attribute in DynamoDB (e.g., "failed", "in progress").
   - Use a separate Step Function or Lambda to reprocess failed entries.

3. **Notification System**:
   - Use **Amazon SNS** to alert administrators of critical failures.

---

### **5.4. Testing and Validation**

1. **End-to-End Tests**:
   - Simulate a full workflow, from video ingestion to web app updates, using sample data.
   - Validate correctness at each stage:
     - Preprocessed frames are saved correctly.
     - Inference and explanations match expectations.
     - Web app displays updated results in real-time.

2. **Load Testing**:
   - Stress test the system with multiple simultaneous video streams.
   - Monitor SageMaker, Lambda, and DynamoDB for performance bottlenecks.

3. **Failure Scenarios**:
   - Test system behavior for edge cases, such as:
     - Missing frames or corrupted video segments.
     - Slow inference times.
     - Network interruptions.

---

### **5.5. Optimization**

1. **Cost Optimization**:
   - Enable auto-scaling for SageMaker endpoints and AppSync.
   - Use lifecycle policies for S3 to delete temporary files.

2. **Performance Tuning**:
   - Preprocess video frames in parallel.
   - Use batched inference for faster processing.

3. **Monitoring**:
   - Use **AWS CloudWatch** to track metrics across the pipeline:
     - Step Function execution times.
     - SageMaker endpoint throughput.
     - DynamoDB read/write capacity.

---

### **Deliverables for Step 5**
- **Fully Integrated Pipeline**: Step Functions coordinating the full workflow.
- **Real-Time Updates**: Web app reflects real-time changes via DynamoDB and AppSync/WebSockets.
- **Error Handling**: Robust retry and failure notification mechanisms.
- **Monitoring**: CloudWatch dashboards for system performance.

---

This step ties all components together into a fully operational system. Let me know if you’d like to focus on specific integrations or start building individual elements!

### **Step 6: Testing in the Field**

#### **Goal**
To quietly test the system in real-world conditions during a powerlifting meet, ensuring it performs effectively under full operational load without interfering with the meet.

---

### **6.1. Preparation for Field Testing**

1. **System Readiness**:
   - Verify that all components (video ingestion, preprocessing, inference, explanation generation, web app) are fully functional and integrated.
   - Run a dry simulation using pre-recorded meet videos to ensure no major bugs exist.

2. **Infrastructure Scaling**:
   - Provision additional resources for SageMaker, Lambda, and DynamoDB to handle the full load of a meet.
   - Set up CloudWatch alarms to monitor performance and resource utilization.

3. **Redundancy and Fail-Safe**:
   - Ensure fallback mechanisms are in place for each step of the pipeline.
   - Record all video data for post-meet analysis if something goes wrong.

4. **Non-Interference**:
   - Ensure the system operates entirely in the background:
     - No outputs or decisions will be communicated to judges or athletes during the test.
   - Disable the web app or use a private instance accessible only to your team.

---

### **6.2. Execution During the Meet**

#### **Steps**
1. **Live Video Feed**:
   - Capture video from the competition cameras as usual.
   - Stream the feed to the system for ingestion and processing.

2. **Silent Operation**:
   - Let the pipeline process data without delivering any outputs to the meet organizers or judges.
   - Collect and store all intermediate results (e.g., preprocessed frames, inference results, explanations) for later evaluation.

3. **Monitor Performance**:
   - Use CloudWatch to track:
     - Inference times for each squat.
     - Latency between ingestion and explanation generation.
     - Resource utilization for SageMaker and Lambda.
   - Note any failures or bottlenecks during the meet.

---

### **6.3. Post-Meet Analysis**

1. **Results Comparison**:
   - Compare the system’s squat classifications to the judges' decisions during the meet.
   - Identify discrepancies and analyze their causes (e.g., model errors, camera angles).

2. **Performance Review**:
   - Review resource utilization and costs during the meet.
   - Evaluate latency and throughput under full load.

3. **Feedback for Improvement**:
   - Document any observed issues, such as:
     - Missed frames or delays in processing.
     - Inaccurate explanations or classifications.
   - Plan updates to the system based on findings.

---

### **6.4. Iterative Testing**

1. **Multiple Meets**:
   - Conduct field tests at several meets to ensure robustness across different environments and conditions (e.g., lighting, camera angles, athlete variability).

2. **Gradual Integration**:
   - Once confident in the system’s performance, begin introducing outputs to meet officials for parallel evaluation (without impacting official decisions).

---

### **6.5. Deliverables**

- **Field Test Logs**:
  - Detailed performance data from the meet.
  - Full pipeline outputs for all squats.
- **Post-Test Report**:
  - Comparison of system classifications with judges’ decisions.
  - Identified bottlenecks and proposed fixes.
- **Updated System**:
  - Iterative improvements based on real-world findings.

---

Let me know if you'd like a detailed checklist or tools to assist with field testing. This step is critical for ensuring the system performs reliably in its intended environment!

Here’s a suggested **project structure** for your powerlifting meet automation system using Python. It organizes components by functionality and aligns with the architecture we’ve developed.

---

### **Project Structure**

```plaintext
powerlifting-automation/
├── src/
│   ├── ingestion/
│   │   ├── kinesis_ingest.py        # Handles video ingestion from Kinesis streams.
│   │   ├── preprocessing.py         # Extracts and preprocesses frames from video.
│   └── inference/
│       ├── model_deployment.py      # Deploys and manages SageMaker model endpoints.
│       ├── inference.py             # Sends frames to the SageMaker model for inference.
│   ├── explanation/
│   │   ├── explanation_generator.py # Generates explanations using a language model.
│   └── web/
│       ├── app.py                   # Flask/Streamlit application for judges' dashboard.
│       ├── static/
│       │   ├── css/                 # CSS files for frontend styling.
│       │   ├── js/                  # JavaScript files for dynamic content.
│       ├── templates/
│       │   ├── index.html           # Web app main template.
│   ├── orchestration/
│   │   ├── step_function_setup.py   # Defines Step Functions workflows.
│   │   ├── orchestrator.py          # Lambda functions for pipeline orchestration.
│   ├── tests/
│       ├── test_ingestion.py        # Unit tests for ingestion pipeline.
│       ├── test_inference.py        # Unit tests for inference pipeline.
│       ├── test_explanation.py      # Unit tests for explanation generator.
│       ├── test_end_to_end.py       # Full pipeline integration tests.
│   ├── utils/
│       ├── s3_helpers.py            # Utility functions for interacting with S3.
│       ├── dynamodb_helpers.py      # Utility functions for DynamoDB interactions.
│       ├── logging_setup.py         # Centralized logging configuration.
├── config/
│   ├── aws_config.json              # AWS credentials and configurations.
│   ├── model_config.json            # PoseFormer model hyperparameters.
├── scripts/
│   ├── deploy_sagemaker.sh          # Script to deploy SageMaker endpoint.
│   ├── run_local_tests.sh           # Script to run unit tests locally.
│   ├── deploy_web_app.sh            # Script to deploy the web app.
├── notebooks/
│   ├── fine_tune_poseformer.ipynb   # Jupyter notebook for model fine-tuning.
│   ├── preprocess_analysis.ipynb    # Notebook to analyze preprocessing quality.
├── README.md                        # Project overview and instructions.
├── requirements.txt                 # Python dependencies.
├── .gitignore                       # Ignore unnecessary files in version control.
```

---

### **Description of Key Files**

#### **Ingestion**
- `kinesis_ingest.py`: Manages video streaming from Kinesis.
- `preprocessing.py`: Extracts frames from video, resizes, and stores in S3.

#### **Inference**
- `model_deployment.py`: Deploys PoseFormer to SageMaker and configures endpoints.
- `inference.py`: Handles inference requests and processes model outputs.

#### **Explanation**
- `explanation_generator.py`: Formats input and queries the language model (e.g., OpenAI GPT, AWS Bedrock).

#### **Web**
- `app.py`: Implements the judges’ dashboard using Flask or Streamlit.
- `static/`: Static assets like CSS and JavaScript.
- `templates/`: HTML templates for the web interface.

#### **Orchestration**
- `step_function_setup.py`: Defines AWS Step Functions workflow using the AWS SDK.
- `orchestrator.py`: Handles Lambda functions for triggering pipeline stages.

#### **Utilities**
- `s3_helpers.py`: Encapsulates S3 interactions, e.g., uploading and retrieving data.
- `dynamodb_helpers.py`: Manages DynamoDB read/write operations.
- `logging_setup.py`: Centralized logging configuration for debugging and monitoring.

#### **Testing**
- `test_ingestion.py`: Unit tests for video ingestion and preprocessing.
- `test_inference.py`: Tests for SageMaker inference pipeline.
- `test_explanation.py`: Tests the explanation generator’s outputs.
- `test_end_to_end.py`: Simulates an entire meet pipeline for integration testing.

---

### **Scripts**
- `deploy_sagemaker.sh`: Automates the deployment of the SageMaker model endpoint.
- `run_local_tests.sh`: Runs unit and integration tests locally.
- `deploy_web_app.sh`: Deploys the web application to AWS (e.g., Amplify, ECS).

---

### **Configuration Files**
- `aws_config.json`: Contains credentials and configuration for AWS services.
- `model_config.json`: Stores parameters for PoseFormer (e.g., input size, keypoint mapping).

---

### **Development Notebooks**
- `fine_tune_poseformer.ipynb`: Code for fine-tuning the PoseFormer model.
- `preprocess_analysis.ipynb`: Analyze and visualize preprocessing results.

---

This structure organizes your code into clear, modular components, making it easy to develop, test, and maintain. Would you like help setting up a specific part or expanding any file in detail?

---
marp: true
theme: default
class: lead
paginate: true
---

# Problem statement
In powerlifting and weightlifting competitions, referees make decisions about whether or not a lift is "Good".
This can be contentious, and lifters often disagree with the decisions made by the referees. 
There is no good appeal method for these decisions. The level of unhappiness 
increases with the addition of prize money and world or national records. At 
times this can detract from the sport.

This is a missed opportunity to add some additional drama to the sport and to 
make it more engaging for the audience. 

## Example Video: 

---
# Proposed solution
Create a VAR to provide "video referee", already ubiquitous in sports like 
football, tennis and cricket.

This tool would not replace human referees, but would be used to provide an 
impartial perspective for contentious decisions. I think it could make viewing 
more interesting too, by injecting a bit of drama into the competitions. VR 
appeals would be limited. Each lefter might have one VAR appeal per meet, to 
push them to use their appeal tactically and to prevent meets getting bogged 
down in endless appeals about decisions that are not contentious.

As far as I'm aware, this is a novel application of pose estimation. 
No VAR system currently exists for powerlifting and weight lifting, which makes 
it more exciting for me. Its always fun to work on something novel.

**NB**: I will be avoiding the ML part of this project instead focusing on 
the infrastructure. If you would like to talk about the ML side of the project, 
I'd love to chat. It was the most entertaining part for me.

---
# Why Serverless architecture?
This tool doesn't get used every day, and the serverless PAYG model suits my needs 
in general.

But there is one significant issue with serverless for this application:
- it is not strictly necessary to have GPU support but it sure helps! CPU-only 
  inference is very slow and while this isn't strictly real time inference, its 
  close enough that one needs to seriously question whether CPU only inference 
  is viable
- GPU support required: it goes without saying that heavy GPU resources are 
  required for fine-tuning, but it doesn't end there. Inference for CV models 
  is GPU intensive. While AWS offers serverless inference for LLMs through 
  bedrock, there is no comparable offering for CV applications.
- I am not aware of a "true" serverless solution for GPU supported CV Inference, 
  however AWS has recently announced that Sagemaker instances can now scale to 
  zero. While this is not strictly serverless.
- Combining SageMaker endpoints with with ECS fargate, provides a workable solution.

---
# Overview of the architecture

1. **Video Ingestion**: Kinesis streams live video, saving segments to S3.
2. **Preprocessing**: Lambda preprocesses frames and stores them in S3, recording metadata in DynamoDB.
3. **Video Inference**: Step Functions invoke the model via SageMaker, evaluating squat depth.
4. **Explanation**: Use AWS Bedrock to generate a detailed explanation for each squat.
5. **Results Delivery**:
   - Annotated video is stored in S3.
   - The web app displays results, explanations, and video replays.
6. **Integration and Orchestration**: 

---
# 1. Video Ingestion and Preprocessing
Time is of the essence, so we stream video from the camera to AWS Kinesis Video 
Streams immediately upon capture. The video is then split into chunks and 
saved to S3. As the video is streamed, we preprocess the chunks to extract key 
information for inference.

## Components
- **Local Camera**: Capture video feed from the powerlifting meet.
- **AWS Kinesis Video Streams**: live stream video from cameras during the meet to S3.
- **S3 Bucket**: Store unprocessed video. This is important for future fine-tuning and training
- **DynamoDB**: Record metadata about the video and frame locations. Trigger preprocessing tasks.
- **AWS Lambda**: preprocessing tasks as video is streamed.
- **S3 Bucket**: Store preprocessed video files (split into chunks if needed).

## Workflow
1. Use **Kinesis Video Streams** to ingest the live video feed and stream it to an **S3 bucket** in chunks (e.g., 5-second segments).
2. store metadata about the video and chunks to **DynamoDB**.
3. **Lambda** function triggered by DynamoDB to perform lightweight preprocessing on the video:
   - Extract frames at regular intervals (e.g. 30 fps).
   - Perform any transformations needed (e.g. cropping, resizing).
   - Save the preprocessed frames in S3 in a structure like:
     ```
     s3://meet-id/squat-id/chunk-id_{timestamp}.mp4
     ```
4. Store preprocessed video chunks in S3 and update metadata in DynamoDB.
5. Record metadata for each frame in DynamoDB:

---
# 2. Inference
This is the sexy bit! The key part of the inference pipeline (excluding the ML stuff!) is the data 
engineering. We cannot wait for the streaming and preprocessing to be complete 
before we start inference. Once preprocessed frames/batches arrive in S3, 
we need to start inference

## Components
- **Amazon S3 Events**: Trigger model inference when video segments or frames arrive.
- **ECS Fargate container**: 
  - Pass the video chunks to the PoseFormer model (or similar) for keypoint detection.
  - Perform the non-ML functions like calculating distance from key points to the floor and calculating relative depth of keypoints.
  - apply decision criteria to determine whether the squat is a "Good lift"
  - reassemble video chunks into a single video file with annotations.
- **AWS SageMaker Endpoint**: Host PoseFormer (or similar model) for inference.
- **AWS Step Functions**: Orchestrate inference and post-processing steps.
- **DynamoDB**: Store intermediate results and metadata.
- **S3**: Store annotated video and updated metadata for replay

## Workflow
1. When a video segment or frame is uploaded to S3, an **S3 event notification** triggers a **Step Function** via **DynamoDB**.
   - Example: Record in DynamoDB that "frame-{timestamp}" is ready for inference.
2. The Step Function invokes the **SageMaker Endpoint**, passing in the frame or batch of frames for inference.
   - The PoseFormer model predicts keypoints for each frame 
   - The application in ECS Fargate calculates the relative positions of the hip, knee, and floor.
   - and applys the decision criteria to determine whether the squat is a "Good lift"
3. Store results (keypoints, classification, and raw predictions) in DynamoDB.

---
# 3. Explanation Generation
In testing version 0.1, I learned that I underestimated the importance of 
natural language explanations. I had assumed that the processed video with 
skeleton imposed over the video was sufficient for the audience to understand 
the decision. I was wrong and this was false. So, I added an additional step to 
address that. Fortunately, Bedrock is a fantastic solution that is easily 
integrated.

## **Components**
- **AWS Lambda**: Trigger explanation generation when inference results are ready.
- **AWS Bedrock**: Generate natural language explanations.
- **DynamoDB**: Store generated explanations.

#### **Workflow**
1. Once the vision model produces a result, a **Lambda function** triggers AWS Bedrock.
2. The language model takes input like:
   - Keypoints (hip, knee, floor).
   - Squat classification ("to depth" or "not to depth").
   - Confidence score.
3. Generate an explanation like:
   - "The lifter's squat was judged 'No Lift' because the hip joint reached 2 
   cm above the knee joint relative to the floor."
4. Save the explanation and associated metadata to DynamoDB.

---
# 4. Web-Based Application for UI
## Components
- **S3 Bucket**: stores processed video with markings and updated metadata.
- **Flask**: Serve the user-facing application.
- **AWS CloudFront**: Distribute web content.
- **DynamoDB**: Fetch data for rendering.

## Workflow
1. **Video Replay with Markings**:
   - Processed video frames are overlaid with keypoints and annotations (e.g., lines connecting hip, knee, and floor).
   - Annotated video is saved back to S3 and linked in DynamoDB.
2. **User Interface**:
   - Users access the application to view:
     - Video replays.
     - Squat classification results.
     - Model-generated explanations.
   - Provide functionality for judges to manually override decisions if needed.
3. **Interactive Features**:
   - Show live updates as squats are processed during the meet.
   - Allow users to filter results by lifter, attempt, or squat classification.

---
# 5. Integration and Orchestration
## Central Control via DynamoDB
- DynamoDB acts as the central state management database.
- **Data Structure**:
  - `Meet ID`: Metadata for the competition.
  - `Squat ID`: Links video files, frame data, model results, and explanations.
  - `State`: Tracks the status of each step in the pipeline.

## **Step Functions**
- Orchestrate the workflow for each squat: 
  From preprocessing → inference → explanation → annotated video generation.
- Retry failed steps (e.g., inference or explanation failures) automatically.

---
# 6. Scaling and Cost Optimization
## Key Considerations
- **Preprocessing**:
  - Use Lambda for light preprocessing to keep costs low.
  - Offload heavy tasks like frame extraction to the SageMaker endpoint.
- **Inference**:
  - Enable auto-scaling for the SageMaker endpoint, but configure it to scale to zero when idle.
- **Data Management**:
  - Use lifecycle policies on S3 buckets to delete temporary files (e.g., raw frames) after processing.

---
