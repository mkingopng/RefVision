Now, we need to do more work on our infrastructure. Lets review the app concept so we can understand what resources need to be created:

- we have a camera set up at the competition venue. Because we're still in the development phase we will upload a pre-recorded file from local. I guess we need some sort of trigger for this in real life application. probably a lambda function
- we use firehose to preprocess the video on the fly
- the raw but preprocessed video is streamed to an S3 bucket called refvision-raw-videos aka bucket_1, it triggers the inference process to begin. I guess we need another lambda to trigger this.
- because there is no serverless option for sagemaker inference with a GPU or other accelerator, the closest serverless-like solution i can think of is ACS with GPU or accelerator support. I would like to use the new inf2 chip as the accelerator if its available in my region.
- The annotated video is then saved to the second bucket called refvision-annotated-videos aka bucket_2
- The annotated video along with the decision is then replayed on the flask app
- we will use dynamodb as a store of state
- we will use a step function to orchestrate the process and handle any failures

# Future considerations (placeholders/comments):
- VPC: If you need network isolation, create a VPC here.
- ECS & Auto Scaling: If you move inference to containers with GPU/inf2 support,
  create an ECS cluster, add an auto scaling group, and target tracking policies.
- SageMaker: Integrate a SageMaker endpoint for model inference with inf2 instances.
- Certificates & ALB: For a production web app, create an ACM certificate, an ALB,
  security groups, and Route 53 DNS records.
- DynamoDB: Use a DynamoDB table to store state across steps if needed.
- EventBridge: Create rules to trigger Lambdas on S3 events or other custom events.
- Logging: Consider a unified logging strategy with sub-log groups per Lambda if desired.

# Questions:
- Do i need a vpc? 
- do i need an ECS cluster for the sagemaker endpoints?
- Do i need certificates? I think i do because the app will be on a domain hosed on sqaurespace 
- do i need an application load balancer?
- do i need a security group?
- do a need a route53 hosted zone or subdomain?
- do i need an eventbridge rule to trigger lambda functions when:
  - to start streaming;
  - an unprocessed video arrives in the unprocessed video bucket to trigger start inference?
  - other steps in the process
- how do i use the step function to orchestrate the process?
- how do i save the information from each step in the process to DynamomDb as a store of state?
- Do i need an eventbridge to capture scaling activities?
- I need to scale to 0
- how do i add an autoscaling group to the ecs cluster?
- how do i add a target tracking scaling policy?
- how do i create a sagemaker end point for the model?
- how to i use sagemaker to run inference on the video? I would like to use inf2
----

```bash
docker run -p 5000:5000 -e FLASK_APP_MODE=local my-yolo-inference
```

```bash
docker run -p 8080:8080 -e FLASK_APP_MODE=cloud my-yolo-inference
```