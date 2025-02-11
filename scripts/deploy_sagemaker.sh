#!/bin/bash

set -e  # Exit on error

echo "Deploying Sagemaker on LocalStack..."
awslocal s3 mb s3://refvision-models

awslocal sagemaker create-model \
    --model-name refvision-inference \
    --primary-container Image=763104351884.dkr.ecr.us-east-1.amazonaws.com/pytorch-inference:1.12.0-cpu-py38 \
    --execution-role-arn arn:aws:iam::000000000000:role/SageMakerExecutionRole

awslocal sagemaker create-endpoint-config \
    --endpoint-config-name refvision-config \
    --production-variants VariantName=AllTraffic,ModelName=refvision-inference,InitialInstanceCount=1,InstanceType=ml.m5.large

awslocal sagemaker create-endpoint \
    --endpoint-name refvision-inference \
    --endpoint-config-name refvision-config

echo "Sagemaker deployed successfully."
