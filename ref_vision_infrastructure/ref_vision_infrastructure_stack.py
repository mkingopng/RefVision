# ref_vision_infrastructure/ref_vision_infrastructure_stack.py
"""
CDK code for deploying the RefVision infrastructure.
"""
import aws_cdk as cdk
from aws_cdk import Stack
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_lambda as _lambda
from aws_cdk import aws_stepfunctions as sfn
from aws_cdk import aws_stepfunctions_tasks as tasks
from aws_cdk import aws_kinesis as kinesis
from aws_cdk import aws_iam as iam
from aws_cdk import aws_kinesisfirehose as firehose
from aws_cdk import aws_sqs as sqs
from aws_cdk import aws_logs as logs
from constructs import Construct

class RefVisionStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        """
        Initialize the RefVisionStack infrastructure.
        :param scope (Construct): The scope of this stack.
        :param id: (str) The ID of this stack.
        :param **kwargs: Additional keyword arguments.
        """
        super().__init__(scope, id, **kwargs)

        # Log group for Video Ingestion Lambda
        logs.LogGroup(
            self,
            "VideoIngestionLogGroup",
            log_group_name=f"/aws/lambda/VideoIngestionFunction",
            retention=logs.RetentionDays.ONE_WEEK
            )

        # Log group for Preprocessing Lambda
        logs.LogGroup(
            self,
            "PreprocessingLogGroup",
            log_group_name=f"/aws/lambda/PreprocessingFunction",
            retention=logs.RetentionDays.ONE_WEEK
            )

        # S3 Bucket for video ingestion
        video_bucket = s3.Bucket(self, "RefVisionVideoBucket")

        # Kinesis Data Stream for video ingestion
        video_stream = kinesis.Stream(self, "VideoStream",
            stream_name="RefVisionVideoStream",
            shard_count=1,
            retention_period=cdk.Duration.hours(24)
        )

        # Kinesis Firehose Delivery Stream to S3
        firehose_role = iam.Role(self, "FirehoseRole",
            assumed_by=iam.ServicePrincipal("firehose.amazonaws.com")
        )

        firehose_role.add_to_policy(iam.PolicyStatement(
            actions=["s3:PutObject", "s3:PutObjectAcl"],
            resources=[f"{video_bucket.bucket_arn}/*"]
        ))

        delivery_stream = firehose.CfnDeliveryStream(self, "DeliveryStream",
            delivery_stream_type="DirectPut",
            s3_destination_configuration=firehose.CfnDeliveryStream.S3DestinationConfigurationProperty(
                bucket_arn=video_bucket.bucket_arn,
                role_arn=firehose_role.role_arn
            )
        )

        # Dead Letter Queue for Lambda functions
        dlq = sqs.Queue(
            self,
            "DLQ",
            queue_name="DLQ"  # Explicitly set queue name
            )

        # Lambda function for video ingestion
        ingestion_lambda = _lambda.Function(
            self, "VideoIngestionFunction",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="handler.lambda_handler",
            code=_lambda.Code.from_asset("functions/video_ingestion"),
            environment={
                "STREAM_NAME": video_stream.stream_name,
                "DELIVERY_STREAM_NAME": delivery_stream.ref
            },
            dead_letter_queue=dlq,
            log_retention=logs.RetentionDays.ONE_WEEK
        )

        # Grant the ingestion Lambda permission to write to Kinesis
        video_stream.grant_write(ingestion_lambda)

        # Lambda function for preprocessing
        preprocessing_lambda = _lambda.Function(
            self, "PreprocessingFunction",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="handler.lambda_handler",
            code=_lambda.Code.from_asset("functions/preprocessing"),
            dead_letter_queue=dlq,
            log_retention=logs.RetentionDays.ONE_WEEK
        )

        # Step Functions workflow definition
        definition = tasks.LambdaInvoke(
            self, "PreprocessingTask",
            lambda_function=preprocessing_lambda,
            result_path="$.PreprocessingResult"
        ).next(
            sfn.Pass(self, "ModelInferenceTask")
        )

        state_machine = sfn.StateMachine(
            self, "ProcessingPipeline",
            definition_body=sfn.DefinitionBody.from_chainable(definition)
        )
