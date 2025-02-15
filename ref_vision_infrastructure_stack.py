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
    # aws_ec2 as ec2,
    # aws_ecs as ecs,
    # aws_ecs_patterns as ecs_patterns,
    # aws_elasticloadbalancingv2 as elbv2,
    # aws_certificatemanager as acm,
    # aws_events as events,
    # aws_events_targets as targets,
    # aws_route53 as route53,
    # aws_route53_targets as route53_targets,
    App,
    Stack,
    # RemovalPolicy,
    # Duration,
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

        # i need to tag everything so that i can manage costs and track resources. how?

        # Do i need a vpc?

        # do i need an ECS cluster for the sagemaker endpoints?

        # Do i need certificates? I think i do because the app will be on a domain hosed on sqaurespace

        # do i need an application load balancer?

        # do i need a security group?

        # do a need a route53 hosted zone or subdomain?

        # do i need an eventbridge rule to trigger lambda functions when:
        # - to start streaming;
        # - an unprocessed video arrives in the unprocessed video bucket to trigger start inference?
        # - other steps in the process

        # how do i use the step function to orchestrate the process?

        # how do i save the information from each step in the process to DynamomDb as a store of state?

        # Do i need an eventbridge to capture scaling activities?

        # I need to scale to 0

        # how do i add an autoscaling group to the ecs cluster?

        # how do i add a target tracking scaling policy?

        # how do i create a sagemaker end point for the model?

        # how to i use sagemaker to run inference on the video? I would like to use inf2

        video_bucket_1 = s3.Bucket(
            self,
            "RefVisionVideoBucket1",
            bucket_name="refvision-raw-videos",
            versioned=True,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=cdk.RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        # Allows the AWS Account Root to save the raw videos to the first bucket
        video_bucket_1.add_to_resource_policy(
            iam.PolicyStatement(
                actions=["s3:PutObject"],
                resources=[f"{video_bucket_1.bucket_arn}/*"],
                principals=[iam.AccountRootPrincipal()],
            )
        )

        # Create a second bucket for the annotated videos
        # video_bucket_2 = s3.Bucket(
        #     self,
        #     "RefVisionVideoBucket2",
        #     bucket_name="refvision-annotated-videos",
        #     versioned=True,
        #     block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
        #     removal_policy=cdk.RemovalPolicy.DESTROY,
        #     auto_delete_objects=True  # Removes all objects on 'cdk destroy'
        # )

        # Allows the AWS Account Root to save videos to the second bucket after processing
        # video_bucket_2.add_to_resource_policy(
        #     iam.PolicyStatement(
        #         actions=["s3:PutObject"],
        #         resources=[f"{video_bucket_2.bucket_arn}/*"],
        #         principals=[iam.AccountRootPrincipal()]
        #     )
        # )

        # todo: shouldn't we have a single log group with sub-groups for each lambda function, anme accordingly?
        logs.LogGroup(
            self,
            "VideoIngestionLogGroup",
            log_group_name="/aws/lambda/VideoIngestionFunction",
            retention=logs.RetentionDays.ONE_WEEK,
            removal_policy=cdk.RemovalPolicy.DESTROY,
        )

        # why don't we have a specific name for this?
        logs.LogGroup(
            self,
            "PreprocessingLogGroup",
            log_group_name="/aws/lambda/PreprocessingFunction",
            retention=logs.RetentionDays.ONE_WEEK,
            removal_policy=cdk.RemovalPolicy.DESTROY,
        )

        video_stream = kinesis.Stream(
            self,
            "VideoStream",
            stream_name="RefVisionVideoStream",  # match test
            shard_count=1,
            retention_period=cdk.Duration.hours(24),
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
                                "kinesis:ListShards",
                            ],
                            resources=[kinesis_stream_arn],
                        )
                    ]
                )
            },
        )

        video_stream.apply_removal_policy(cdk.RemovalPolicy.DESTROY)

        firehose_role = iam.Role(
            self,
            "RefVisionFirehoseRole",
            role_name="RefVisionFirehoseRole",  # MUST match test
            assumed_by=iam.ServicePrincipal("firehose.amazonaws.com"),
        )

        firehose_role.add_to_policy(
            iam.PolicyStatement(
                actions=["s3:PutObject", "s3:PutObjectAcl"],
                resources=[f"{video_bucket_1.bucket_arn}/*"],
            )
        )

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

        dlq = sqs.Queue(
            self, "DLQ", queue_name="DLQ", removal_policy=cdk.RemovalPolicy.DESTROY
        )

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
            log_retention=logs.RetentionDays.ONE_WEEK,
        )

        # Grant the ingestion Lambda permission to write to Kinesis
        video_stream.grant_write(ingestion_lambda)

        preprocessing_lambda = _lambda.Function(
            self,
            "PreprocessingFunction",
            function_name="PreprocessingFunction",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="handler.lambda_handler",
            code=_lambda.Code.from_asset("refvision/functions/preprocessing"),
            dead_letter_queue=dlq,
            log_retention=logs.RetentionDays.ONE_WEEK,
        )

        # --------------------------------------------------------------------
        # Simple Step Functions workflow definition
        # --------------------------------------------------------------------
        definition = tasks.LambdaInvoke(
            self,
            "PreprocessingTask",
            lambda_function=preprocessing_lambda,
            result_path="$.PreprocessingResult",
        ).next(sfn.Pass(self, "ModelInferenceTask"))

        sfn.StateMachine(
            self,
            "ProcessingPipeline",
            state_machine_name="RefVisionProcessingPipeline",
            definition_body=sfn.DefinitionBody.from_chainable(definition),
        )


# create the App instance
app = App()

# create the RefVisionStack instance
# todo: save these values somewhere safe
env = Environment(account="001499655372", region="ap-southeast-2")

# apply tags to all resources in the app
Tags.of(app).add("Project", "RefVision")
Tags.of(app).add("Environment", "Development")
Tags.of(app).add("Owner", "MichaelKingston")

# define the stack
RefVisionStack(
    app, "RefVisionStack", description="RefVision Infrastructure Stack", env=env
)

# synthesize the stack
app.synth()
