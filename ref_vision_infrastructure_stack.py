# ref_vision_infrastructure/ref_vision_infrastructure_stack.py
"""
Infrastructure stack for the RefVision application.

clean up:
aws cloudformation delete-stack --stack-name RefVisionStack --region ap-southeast-2

check status:
aws cloudformation describe-stacks --stack-name RefVisionStack --region ap-southeast-2
"""
import aws_cdk as cdk
from aws_cdk import (
    aws_s3 as s3,
    aws_iam as iam,
    aws_logs as logs,
    aws_lambda as _lambda,
    aws_stepfunctions as sfn,
    aws_stepfunctions_tasks as tasks,
    aws_kinesis as kinesis,
    aws_kinesisfirehose as firehose,
    aws_sqs as sqs,
    aws_logs_destinations as logs_destinations,
    App,
    Stack,
    RemovalPolicy,
    Duration,
    Environment,
    Tags,
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

        # global tags to all resources in the app
        Tags.of(app).add("Project", "RefVision")
        Tags.of(app).add("Environment", "Development")
        Tags.of(app).add("Owner", "MichaelKingston")

        # S3 bucket for raw videos (bucket_1)
        video_bucket_1 = s3.Bucket(
            self,
            "RefVisionVideoBucket1",
            bucket_name="refvision-raw-videos",
            versioned=True,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=cdk.RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        video_bucket_1.add_to_resource_policy(
            iam.PolicyStatement(
                actions=["s3:PutObject"],
                resources=[f"{video_bucket_1.bucket_arn}/*"],
                principals=[iam.AccountRootPrincipal()],
            )
        )

        # S3 bucket for the annotated videos
        video_bucket_2 = s3.Bucket(
            self,
            "RefVisionVideoBucket2",
            bucket_name="refvision-annotated-videos",
            versioned=True,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=cdk.RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        video_bucket_2.add_to_resource_policy(
            iam.PolicyStatement(
                actions=["s3:PutObject"],
                resources=[f"{video_bucket_2.bucket_arn}/*"],
                principals=[iam.AccountRootPrincipal()],
            )
        )

        # Combined log groups for application
        combined_log_group = logs.LogGroup(
            self,
            "RefVisionCombinedLogGroup",
            log_group_name="/aws/refvision/combined",
            removal_policy=RemovalPolicy.DESTROY,
        )

        video_ingestion_log_group = logs.LogGroup(
            self,
            "VideoIngestionLogGroup",
            log_group_name="/aws/lambda/VideoIngestionFunction",
            removal_policy=RemovalPolicy.DESTROY,
        )

        preprocessing_log_group = logs.LogGroup(
            self,
            "PreprocessingLogGroup",
            log_group_name="/aws/lambda/PreprocessingFunction",
            removal_policy=RemovalPolicy.DESTROY,
        )

        # Create the Lambda log forwarder function.
        log_forwarder = _lambda.Function(
            self,
            "LogForwarderFunction",
            function_name="LogForwarderFunction",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="log_forwarder.handler",
            code=_lambda.Code.from_asset("refvision/functions/log_forwarder"),
            timeout=Duration.seconds(30),
            environment={
                "COMBINED_LOG_GROUP": combined_log_group.log_group_name,
            },
        )

        # Grant the log forwarder permission to write to the combined log group.
        combined_log_group.grant_write(log_forwarder)

        # Add subscription filters to individual log groups to forward logs to the log forwarder.
        video_ingestion_log_group.add_subscription_filter(
            "VideoIngestionSubscription",
            destination=logs_destinations.LambdaDestination(log_forwarder),
            filter_pattern=logs.FilterPattern.all_events(),
        )
        preprocessing_log_group.add_subscription_filter(
            "PreprocessingSubscription",
            destination=logs_destinations.LambdaDestination(log_forwarder),
            filter_pattern=logs.FilterPattern.all_events(),
        )

        # Kinesis data stream for video ingestion events
        video_stream = kinesis.Stream(
            self,
            "VideoStream",
            stream_name="RefVisionVideoStream",
            shard_count=1,
            retention_period=cdk.Duration.hours(24),
        )

        kinesis_stream_arn = f"arn:aws:kinesis:{cdk.Aws.REGION}:{cdk.Aws.ACCOUNT_ID}:stream/RefVisionVideoStream"

        # IAM role for video ingestion Lambda
        video_ingestion_role = iam.Role(
            self,
            "VideoIngestionFunctionServiceRole",
            role_name="VideoIngestionFunctionServiceRole",
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
                                "kinesis:ListShards",
                            ],
                            resources=[kinesis_stream_arn],
                        )
                    ]
                )
            },
        )

        video_stream.apply_removal_policy(cdk.RemovalPolicy.DESTROY)

        # IAM role for Firehose (preprocessing)
        firehose_role = iam.Role(
            self,
            "RefVisionFirehoseRole",
            role_name="RefVisionFirehoseRole",
            assumed_by=iam.ServicePrincipal("firehose.amazonaws.com"),
        )

        firehose_role.add_to_policy(
            iam.PolicyStatement(
                actions=["s3:PutObject", "s3:PutObjectAcl"],
                resources=[f"{video_bucket_1.bucket_arn}/*"],
            )
        )

        # Kinesis Firehose Delivery Stream for video preprocessing.
        delivery_stream = firehose.CfnDeliveryStream(
            self,
            "DeliveryStream",
            delivery_stream_name=f"RefVisionFirehoseStream-{cdk.Aws.ACCOUNT_ID}-{cdk.Aws.REGION}",
            delivery_stream_type="DirectPut",
            s3_destination_configuration=firehose.CfnDeliveryStream.S3DestinationConfigurationProperty(
                bucket_arn=video_bucket_1.bucket_arn, role_arn=firehose_role.role_arn
            ),
        )

        delivery_stream.node.add_dependency(video_bucket_1)
        delivery_stream.node.add_dependency(firehose_role)

        # SQS Dead Letter Queue for Lambda failures.
        dlq = sqs.Queue(
            self, "DLQ", queue_name="DLQ", removal_policy=cdk.RemovalPolicy.DESTROY
        )

        # Video Ingestion Lambda: triggers on local file upload (or later on a camera event)
        ingestion_lambda = _lambda.Function(
            self,
            "VideoIngestionFunction",
            function_name="VideoIngestionFunction",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="handler.lambda_handler",
            code=_lambda.Code.from_asset("refvision/functions/video_ingestion"),
            role=video_ingestion_role,
            environment={
                "STREAM_NAME": video_stream.stream_name,
                "DELIVERY_STREAM_NAME": delivery_stream.ref,
            },
            dead_letter_queue=dlq,
        )

        video_stream.grant_write(ingestion_lambda)

        # Preprocessing Lambda: processes raw video, then triggers inference
        preprocessing_lambda = _lambda.Function(
            self,
            "PreprocessingFunction",
            function_name="PreprocessingFunction",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="handler.lambda_handler",
            code=_lambda.Code.from_asset("refvision/functions/preprocessing"),
            dead_letter_queue=dlq,
        )

        # Step Functions State Machine: Orchestrates the overall workflow.
        definition = tasks.LambdaInvoke(
            self,
            "PreprocessingTask",
            lambda_function=preprocessing_lambda,
            result_path="$.PreprocessingResult",
        ).next(
            sfn.Pass(
                self, "ModelInferenceTask"
            )  # Placeholder for the model inference step.
        )

        sfn.StateMachine(
            self,
            "ProcessingPipeline",
            state_machine_name="RefVisionProcessingPipeline",
            definition_body=sfn.DefinitionBody.from_chainable(definition),
        )

        # -------------------------------
        # Future considerations (placeholders):
        # - VPC, ECS cluster, ALB, Route 53, ACM for custom domains.
        # - SageMaker endpoints for inference using inf2.
        # - DynamoDB for state storage.
        # - EventBridge rules to trigger Lambdas on S3 events or other custom events.
        # - Scaling and autoscaling policies.
        # -------------------------------


# create the App instance
app = App()

# create the RefVisionStack instance
# todo: save these values somewhere safe
env = Environment(account="001499655372", region="ap-southeast-2")

# define the stack
RefVisionStack(
    app, "RefVisionStack", description="RefVision Infrastructure Stack", env=env
)

# synthesize the stack
app.synth()
