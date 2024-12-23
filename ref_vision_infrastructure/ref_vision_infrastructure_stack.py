# ref_vision_infrastructure/ref_vision_infrastructure_stack.py
"""
CDK code for deploying the RefVision infrastructure.
"""
import aws_cdk as cdk
from aws_cdk import (
    Stack,
    aws_s3 as s3,
    aws_lambda as _lambda,
    aws_stepfunctions as sfn,
    aws_stepfunctions_tasks as tasks,
    aws_kinesis as kinesis,
    aws_iam as iam,
    aws_kinesisfirehose as firehose,
    aws_sqs as sqs,
    aws_logs as logs
)
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

        video_bucket = s3.Bucket(
            self,
            "RefVisionVideoBucket",
            bucket_name="ref-vision-video-bucket",
            versioned=True,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=cdk.RemovalPolicy.DESTROY,
            auto_delete_objects=True  # Removes all objects on 'cdk destroy'
        )

        # Allows the AWS Account Root to put objects (if needed)
        video_bucket.add_to_resource_policy(
            iam.PolicyStatement(
                actions=["s3:PutObject"],
                resources=[f"{video_bucket.bucket_arn}/*"],
                principals=[iam.AccountRootPrincipal()]
            )
        )

        logs.LogGroup(
            self,
            "VideoIngestionLogGroup",
            log_group_name="/aws/lambda/VideoIngestionFunction",
            retention=logs.RetentionDays.ONE_WEEK,
            removal_policy=cdk.RemovalPolicy.DESTROY
        )

        logs.LogGroup(
            self,
            "PreprocessingLogGroup",
            log_group_name="/aws/lambda/PreprocessingFunction",
            retention=logs.RetentionDays.ONE_WEEK,
            removal_policy=cdk.RemovalPolicy.DESTROY
        )

        video_stream = kinesis.Stream(
            self,
            "VideoStream",
            stream_name="RefVisionVideoStream",  # match test
            shard_count=1,
            retention_period=cdk.Duration.hours(24)
        )

        # Then reference that same name in the inline policy.
        # The test expects arn:aws:kinesis:<REGION>:<ACCOUNT_ID>:stream/RefVisionVideoStream
        # so let's build exactly that:
        kinesis_stream_arn = f"arn:aws:kinesis:{cdk.Aws.REGION}:{cdk.Aws.ACCOUNT_ID}:stream/RefVisionVideoStream"

        video_ingestion_role = iam.Role(
            self,
            "VideoIngestionFunctionServiceRole",
            role_name="VideoIngestionFunctionServiceRole",  # matches test
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                )
            ],
            inline_policies={
                "KinesisPermissions": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            actions=[
                                "kinesis:PutRecord",
                                "kinesis:PutRecords",
                                "kinesis:ListShards"
                            ],
                            resources=[kinesis_stream_arn],
                        )
                    ]
                )
            }
        )
        video_stream.apply_removal_policy(cdk.RemovalPolicy.DESTROY)

        firehose_role = iam.Role(
            self,
            "RefVisionFirehoseRole",
            role_name="RefVisionFirehoseRole",  # MUST match test
            assumed_by=iam.ServicePrincipal("firehose.amazonaws.com")
        )

        firehose_role.add_to_policy(
            iam.PolicyStatement(
                actions=["s3:PutObject", "s3:PutObjectAcl"],
                resources=[f"{video_bucket.bucket_arn}/*"]
            )
        )

        delivery_stream = firehose.CfnDeliveryStream(
            self,
            "DeliveryStream",
            delivery_stream_name=f"RefVisionFirehoseStream-{cdk.Aws.ACCOUNT_ID}-{cdk.Aws.REGION}",
            delivery_stream_type="DirectPut",
            s3_destination_configuration=firehose.CfnDeliveryStream.S3DestinationConfigurationProperty(
                bucket_arn=video_bucket.bucket_arn,
                role_arn=firehose_role.role_arn
            )
        )

        delivery_stream.node.add_dependency(video_bucket)
        delivery_stream.node.add_dependency(firehose_role)

        dlq = sqs.Queue(
            self,
            "DLQ",
            queue_name="DLQ",
            removal_policy=cdk.RemovalPolicy.DESTROY
        )

        ingestion_lambda = _lambda.Function(
            self,
            "VideoIngestionFunction",
            function_name="VideoIngestionFunction",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="handler.lambda_handler",
            code=_lambda.Code.from_asset("functions/video_ingestion"),
            role=video_ingestion_role,
            environment={
                "STREAM_NAME": video_stream.stream_name,
                "DELIVERY_STREAM_NAME": delivery_stream.ref
            },
            dead_letter_queue=dlq,
            log_retention=logs.RetentionDays.ONE_WEEK
        )

        # Grant the ingestion Lambda permission to write to Kinesis
        video_stream.grant_write(ingestion_lambda)

        preprocessing_lambda = _lambda.Function(
            self,
            "PreprocessingFunction",
            function_name="PreprocessingFunction",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="handler.lambda_handler",
            code=_lambda.Code.from_asset("functions/preprocessing"),
            dead_letter_queue=dlq,
            log_retention=logs.RetentionDays.ONE_WEEK
        )

        # --------------------------------------------------------------------
        # Simple Step Functions workflow definition
        # --------------------------------------------------------------------
        definition = tasks.LambdaInvoke(
            self,
            "PreprocessingTask",
            lambda_function=preprocessing_lambda,
            result_path="$.PreprocessingResult"
        ).next(
            sfn.Pass(self, "ModelInferenceTask")
        )

        sfn.StateMachine(
            self,
            "ProcessingPipeline",
            state_machine_name="RefVisionProcessingPipeline",
            definition_body=sfn.DefinitionBody.from_chainable(definition)
        )
