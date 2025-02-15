Now, we need to do more work on our infrastructure. Lets review the app concept so we can understand what resources need to be created:

- we have a camera set up at the competition venue. Because we're still in the development phase we will upload a pre-recorded file from local. I guess we need some sort of trigger for this in real life application. probably a lambda function
- we use firehose to preprocess the video on the fly
- the raw but preprocessed video is streamed to an S3 bucket called refvision-raw-videos aka bucket_1, it triggers the inference process to begin. I guess we need another lambda to trigger this.
- because there is no serverless option for sagemaker inference with a GPU or other accelerator, the closest serverless-like solution i can think of is ACS with GPU or accelerator support. I would like to use the new inf2 chip as the accelerator if its available in my region.
- The annotated video is then saved to the second bucket called refvision-annotated-videos aka bucket_2
- The annotated video along with the decision is then replayed on the flask app
- we will use dynamodb as a store of state
- we will use a step function to orchestrate the process and handle any failures