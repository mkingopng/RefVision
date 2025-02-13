# ref_vision_infrastructure/ref_vision_infrastructure_stack.py
"""
Infrastructure stack for the RefVision application.

clean up:
aws cloudformation delete-stack --stack-name RefVisionStack --region ap-southeast-2

check status
aws cloudformation describe-stacks --stack-name RefVisionStack --region ap-southeast-2
"""
import os
import aws_cdk as cdk
from aws_cdk import (
    Stack,
    Duration,
    aws_s3 as s3,
    aws_lambda as _lambda,
    aws_stepfunctions as sfn,
    aws_stepfunctions_tasks as tasks,
    aws_kinesis as kinesis,
    aws_iam as iam,
    aws_logs as logs
)
from constructs import Construct
from dotenv import load_dotenv

load_dotenv()

class RefVisionStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Load environment variables
        stream_name = os.getenv("STREAM_NAME", "RefVisionVideoStream")
        s3_bucket_name = os.getenv("TEST_S3_BUCKET", "refvision-video-bucket")
        region = os.getenv("AWS_DEFAULT_REGION", "ap-southeast-2")

        # ✅ Define Explicit IAM Role for CloudFormation Execution
        cloudformation_role = iam.Role(
            self, "CloudFormationExecutionRole",
            assumed_by=iam.ServicePrincipal("cloudformation.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("AdministratorAccess")
            ]
        )

        # ✅ Define IAM Role for Lambda Functions
        lambda_execution_role = iam.Role(
            self, "LambdaExecutionRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AWSLambdaExecute"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonKinesisFullAccess")
            ]
        )

        # ✅ Define IAM Role for Step Functions
        step_function_role = iam.Role(
            self, "StepFunctionExecutionRole",
            assumed_by=iam.ServicePrincipal("states.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "AWSStepFunctionsFullAccess"),
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "AWSLambdaExecute")  # ✅ Use a valid policy
            ]
        )

        # ✅ Define IAM Role for Kinesis
        kinesis_role = iam.Role(
            self, "KinesisExecutionRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonKinesisFullAccess")
            ]
        )

        # ✅ Create an S3 Bucket for storing videos
        video_bucket = s3.Bucket.from_bucket_name(
            self,
            "RefVisionVideoBucket",
            bucket_name=s3_bucket_name
        )

        # ✅ Define a Kinesis Video Stream
        video_stream = kinesis.Stream.from_stream_arn(
            self,
            "VideoStream",
            stream_arn=f"arn:aws:kinesis:{region}:{os.getenv('ACCOUNT_ID')}:stream/{stream_name}"
        )

        # ✅ Define a Video Ingestion Lambda
        video_ingestion_lambda = _lambda.Function(
            self,
            "VideoIngestionFunction",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="handler.lambda_handler",
            code=_lambda.Code.from_asset("refvision/functions/video_ingestion"),
            role=lambda_execution_role,
            environment={
                "STREAM_NAME": stream_name,
                "S3_BUCKET": s3_bucket_name
            },
            log_retention=logs.RetentionDays.ONE_WEEK
        )

        # Grant Permissions to Lambda & Kinesis
        video_bucket.grant_read_write(video_ingestion_lambda)
        video_stream.grant_write(video_ingestion_lambda)

        # ✅ Define a Step Function for processing video
        definition = tasks.LambdaInvoke(
            self,
            "PreprocessingTask",
            lambda_function=video_ingestion_lambda,
            result_path="$.PreprocessingResult"
        ).next(
            sfn.Pass(self, "ModelInferenceTask")
        )

        processing_pipeline = sfn.StateMachine(
            self,
            "ProcessingPipeline",
            state_machine_name="RefVisionProcessingPipeline",
            definition_body=sfn.DefinitionBody.from_chainable(definition),
            role=step_function_role
        )

        # ✅ Define IAM Policy for S3 Access
        video_bucket.add_to_resource_policy(
            iam.PolicyStatement(
                actions=["s3:GetObject", "s3:PutObject"],
                resources=[f"{video_bucket.bucket_arn}/*"],  # ✅ Correct
                principals=[iam.ServicePrincipal("lambda.amazonaws.com")]
            )
        )

        # ✅ Output IAM role ARNs for debugging
        cdk.CfnOutput(self, "CloudFormationExecutionRoleArn", value=cloudformation_role.role_arn)
        cdk.CfnOutput(self, "LambdaExecutionRoleArn", value=lambda_execution_role.role_arn)
        cdk.CfnOutput(self, "StepFunctionExecutionRoleArn", value=step_function_role.role_arn)
        cdk.CfnOutput(self, "KinesisExecutionRoleArn", value=kinesis_role.role_arn)
