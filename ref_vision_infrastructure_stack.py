# ref_vision_infrastructure/ref_vision_infrastructure_stack.py
"""
Infrastructure stack for the RefVision application.

Clean up:
  aws cloudformation delete-stack --stack-name RefVisionStack --region ap-southeast-2

Check status:
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
    aws_ec2 as ec2,  # noqa: F401
    aws_elasticloadbalancingv2 as elbv2,  # noqa: F401
    aws_certificatemanager as acm,  # noqa: F401
    aws_dynamodb as dynamodb,
    aws_sagemaker as sagemaker,
    aws_ecs as ecs,
    App,
    Stack,
    RemovalPolicy,
    Duration,  # noqa: F401
    Environment,
    Tags,
    Aws,
    Fn,
    CfnOutput,
)
from aws_cdk.aws_s3_notifications import LambdaDestination
from constructs import Construct


class RefVisionStack(Stack):
    def __init__(self, scope: Construct, stack_id: str, **kwargs) -> None:
        """
        Initialize the RefVisionStack infrastructure.
        :param scope: The scope of this stack.
        :param stack_id: The ID of this stack.
        :param kwargs: Additional keyword arguments.
        """
        super().__init__(scope, stack_id, **kwargs)

        # global tags to all resources in the app
        Tags.of(self).add("Project", "RefVision")
        Tags.of(self).add("Environment", "Development")
        Tags.of(self).add("Owner", "MichaelKingston")

        # networking and ALB Setup
        vpc = ec2.Vpc(
            self,
            "RefVisionVPC",
            max_azs=2,
        )

        # reference existing ACM certificate.
        certificate_arn = "arn:aws:acm:ap-southeast-2:001499655372:certificate/0dc3aff3-c586-419d-9a63-885ad3ecc41f"
        certificate = acm.Certificate.from_certificate_arn(
            self, "RefVisionCertificate", certificate_arn
        )

        # create an internet-facing Application Load Balancer in the VPC.
        alb = elbv2.ApplicationLoadBalancer(
            self,
            "RefVisionALB",
            vpc=vpc,
            internet_facing=True,
            load_balancer_name="RefVisionALB",
        )

        # add an HTTPS listener on port 443 using the ACM certificate.
        https_listener = alb.add_listener(
            "HttpsListener",
            port=443,
            certificates=[certificate],
            default_action=elbv2.ListenerAction.fixed_response(
                status_code=404,
                message_body="Not Found",
            ),  # noqa: F841
        )

        # add an HTTP listener that redirects to HTTPS.
        http_listener = alb.add_listener("HttpListener", port=80)

        http_listener.add_action(
            "HttpToHttpsRedirect",
            action=elbv2.ListenerAction.redirect(
                protocol="HTTPS",
                port="443",
                permanent=True,
            ),
        )

        cluster = ecs.Cluster(self, "RefVisionCluster", vpc=vpc)

        task_definition = ecs.FargateTaskDefinition(
            self, "RefVisionTaskDefinition", cpu=512, memory_limit_mib=1024
        )

        _container = task_definition.add_container(
            "FlaskContainer",
            image=ecs.ContainerImage.from_asset("."),
            port_mappings=[ecs.PortMapping(container_port=80)],
        )

        service = ecs.FargateService(
            self,
            "RefVisionService",
            cluster=cluster,
            task_definition=task_definition,
            desired_count=1,
        )

        # Target group linking
        target_group = elbv2.ApplicationTargetGroup(
            self,
            "RefVisionTargetGroup",
            vpc=vpc,
            port=80,
            targets=[service],
            health_check=elbv2.HealthCheck(path="/"),
        )

        https_listener.add_target_groups(
            "DefaultTargetGroup", target_groups=[target_group]
        )

        # output the ALB DNS name for easy access.
        cdk.CfnOutput(self, "ALBDNS", value=alb.load_balancer_dns_name)

        # create a DynamoDB table for storing processing state
        state_table = dynamodb.Table(
            self,
            "ProcessingStateTable",
            table_name="RefVisionProcessingState",
            partition_key=dynamodb.Attribute(
                name="videoId", type=dynamodb.AttributeType.STRING
            ),
            removal_policy=RemovalPolicy.DESTROY,
            # only for dev; change for production
        )

        # S3 bucket for raw videos.
        # noinspection PyTypeChecker
        video_bucket_1 = s3.Bucket(
            self,
            "RefVisionVideoBucket1",
            bucket_name="refvision-raw-videos",
            versioned=True,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        video_bucket_1.add_to_resource_policy(
            iam.PolicyStatement(
                actions=["s3:PutObject"],
                resources=[f"{video_bucket_1.bucket_arn}/*"],
                principals=[iam.AccountRootPrincipal()],
            )
        )

        # S3 bucket for annotated videos.
        # noinspection PyTypeChecker
        video_bucket_2 = s3.Bucket(
            self,
            "RefVisionVideoBucket2",
            bucket_name="refvision-annotated-videos",
            versioned=True,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        video_bucket_2.add_to_resource_policy(
            iam.PolicyStatement(
                actions=["s3:PutObject"],
                resources=[f"{video_bucket_2.bucket_arn}/*"],
                principals=[iam.AccountRootPrincipal()],
            )
        )

        # reference the existing model bucket
        model_bucket = s3.Bucket.from_bucket_name(
            self, "RefVisionYoloModelBucket", "refvision-yolo-model"
        )

        # Dead Letter Queue
        # noinspection PyTypeChecker
        dlq: sqs.IQueue = sqs.Queue(
            self, "DLQ", queue_name="DLQ", removal_policy=RemovalPolicy.DESTROY
        )

        # preprocessing Lambda: processes raw video, then triggers inference.
        # noinspection PyTypeChecker
        preprocessing_lambda: _lambda.IFunction = _lambda.Function(
            self,
            "PreprocessingFunction",
            function_name="PreprocessingFunction",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="handler.lambda_handler",
            code=_lambda.Code.from_asset("refvision/functions/preprocessing"),
            dead_letter_queue=dlq,
        )

        # ingestion Lambda for uploading a video
        video_stream = kinesis.Stream(
            self,
            "VideoStream",
            stream_name="RefVisionVideoStream",
            shard_count=1,
            retention_period=Duration.hours(24),
        )

        kinesis_stream_arn = f"arn:aws:kinesis:{cdk.Aws.REGION}:{cdk.Aws.ACCOUNT_ID}:stream/RefVisionVideoStream"

        video_ingestion_role = iam.Role(
            self,
            "VideoIngestionFunctionServiceRole",
            role_name="RefVisionVideoIngestionFunctionServiceRole",
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

        video_stream.apply_removal_policy(RemovalPolicy.DESTROY)

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
                "DELIVERY_STREAM_NAME": f"RefVisionFirehoseStream-{cdk.Aws.ACCOUNT_ID}-{cdk.Aws.REGION}",
            },
            dead_letter_queue=dlq,
        )
        video_stream.grant_write(ingestion_lambda)

        bedrock_policy_statement = iam.PolicyStatement(
            actions=["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"],
            resources=[
                "arn:aws:bedrock:ap-southeast-2::foundation-model/anthropic.claude-v2"
            ],
        )

        # explanation Generator Lambda
        explanation_lambda_role = iam.Role(
            self,
            "ExplanationLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                )
            ],
        )

        # explicitly grant DynamoDB read access to the Lambda
        state_table.grant_read_data(explanation_lambda_role)

        # attach Bedrock permissions to Lambda role
        explanation_lambda_role.add_to_policy(bedrock_policy_statement)

        # define the Lambda function
        # noinspection PyTypeChecker
        explanation_generator_lambda: _lambda.IFunction = _lambda.Function(
            self,
            "ExplanationGeneratorFunction",
            function_name="ExplanationGeneratorFunction",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="explanation_generator.handler",
            code=_lambda.Code.from_asset("refvision/explanation"),
            role=explanation_lambda_role,
            timeout=Duration.seconds(60),
            environment={
                "MODEL_ID": "anthropic.claude-v2",
                "REGION": "ap-southeast-2",
                "DECISION_TABLE": state_table.table_name,
            },
        )

        # inference trigger Lambda Setup
        # noinspection PyTypeChecker
        inference_trigger_lambda: _lambda.IFunction = _lambda.Function(
            self,
            "InferenceTriggerFunction",
            function_name="InferenceTriggerFunction",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="inference_trigger.handler",
            code=_lambda.Code.from_asset("refvision/functions/inference_trigger"),
            timeout=Duration.seconds(30),
        )

        # step Function State Machine Setup - define the state machine
        definition = (
            tasks.LambdaInvoke(
                self,
                "PreprocessingTask",
                lambda_function=preprocessing_lambda,
                result_path="$.PreprocessingResult",
            )
            .next(
                tasks.CallAwsService(
                    self,
                    "InferenceTask",
                    service="sagemaker",
                    action="invokeEndpoint",
                    parameters={
                        "EndpointName": "RefVisionSageMakerEndpoint",
                        "Body": sfn.TaskInput.from_json_path_at(
                            "$.PreprocessingResult"
                        ),
                        "ContentType": "application/json",
                    },
                    iam_resources=[
                        f"arn:aws:sagemaker:{Aws.REGION}:{Aws.ACCOUNT_ID}:endpoint/RefVisionSageMakerEndpoint"
                    ],
                    result_path="$.InferenceResult",
                )
            )
            .next(
                tasks.LambdaInvoke(
                    self,
                    "ExplanationTask",
                    lambda_function=explanation_generator_lambda,
                    result_path="$.ExplanationResult",
                )
            )
        )

        processing_pipeline = sfn.StateMachine(
            self,
            "ProcessingPipeline",
            state_machine_name="RefVisionProcessingPipeline",
            definition_body=sfn.DefinitionBody.from_chainable(definition),
        )

        # create an IAM role for SageMaker with required permissions
        sagemaker_role = iam.Role(
            self,
            "SageMakerExecutionRole",
            role_name="RefVisionSageMakerExecutionRole",
            assumed_by=iam.ServicePrincipal("sagemaker.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "AmazonS3ReadOnlyAccess"
                ),
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "AmazonSageMakerFullAccess"
                ),
            ],
        )
        sagemaker_role.add_to_policy(
            iam.PolicyStatement(
                actions=["s3:GetObject"],
                resources=[f"{model_bucket.bucket_arn}/*"],
            )
        )

        model_bucket.add_to_resource_policy(
            iam.PolicyStatement(
                actions=["s3:GetObject"],
                resources=[f"{model_bucket.bucket_arn}/*"],
                principals=[iam.ArnPrincipal(sagemaker_role.role_arn)],
            )
        )

        # set environment variable for the state machine ARN.
        inference_trigger_lambda.add_environment(
            "STATE_MACHINE_ARN", processing_pipeline.state_machine_arn
        )

        # todo: ensure preprocessing_lambda, inference_trigger_lambda, and other lambdas exist
        preprocessing_lambda.add_to_role_policy(bedrock_policy_statement)
        inference_trigger_lambda.add_to_role_policy(bedrock_policy_statement)

        lambda_role = iam.Role(
            self,
            "RefVisionLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                )
            ],
        )  # todo: tighten up policies so that only the bedrock lambda has permissions to invoke bedrock models
        lambda_role.add_to_policy(bedrock_policy_statement)

        # todo: output the state machine ARN for easy access.

        explanation_generator_lambda.add_to_role_policy(bedrock_policy_statement)

        state_table.grant_read_data(explanation_generator_lambda)

        # create the SageMaker Model
        sagemaker_model = sagemaker.CfnModel(
            self,
            "SageMakerModel",
            execution_role_arn=sagemaker_role.role_arn,
            primary_container=sagemaker.CfnModel.ContainerDefinitionProperty(
                image="001499655372.dkr.ecr.ap-southeast-2.amazonaws.com/my-yolo-inference:latest",
                model_data_url="s3://refvision-yolo-model/yolo11x-pose.tar.gz",
                environment={"EXAMPLE_ENV": "value"},
            ),
        )

        # create the sagemaker endpoint configuration.
        endpoint_config = sagemaker.CfnEndpointConfig(
            self,
            "SageMakerEndpointConfig",
            production_variants=[
                {
                    "initialInstanceCount": 1,
                    "instanceType": "ml.g4dn.xlarge",
                    "modelName": sagemaker_model.attr_model_name,
                    "variantName": "AllTraffic",
                }
            ],
        )

        # create the SageMaker Endpoint.
        sagemaker_endpoint = sagemaker.CfnEndpoint(
            self,
            "SageMakerEndpoint",
            endpoint_config_name=endpoint_config.attr_endpoint_config_name,
            endpoint_name="RefVisionSageMakerEndpoint",
        )

        endpoint_arn = Fn.join(
            ":",
            [
                "arn",
                Aws.PARTITION,
                "sagemaker",
                Aws.REGION,
                Aws.ACCOUNT_ID,
                f"endpoint/{sagemaker_endpoint.attr_endpoint_name}",
            ],
        )

        # optionally, output the endpoint ARN or URL.
        CfnOutput(
            self,
            "SageMakerEndpointName",
            value=endpoint_arn,
        )

        # grant permission to start the state machine execution.
        processing_pipeline.grant_start_execution(inference_trigger_lambda)

        # grant read/write access to the state table.
        state_table.grant_read_write_data(preprocessing_lambda)
        state_table.grant_read_write_data(ingestion_lambda)
        state_table.grant_read_write_data(inference_trigger_lambda)

        # trigger when a new object is created in the raw video bucket
        video_bucket_1.add_event_notification(
            s3.EventType.OBJECT_CREATED,
            LambdaDestination(inference_trigger_lambda),
        )

        # logging setup
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
        #
        log_forwarder = _lambda.Function(
            self,
            "LogForwarderFunction",
            function_name="LogForwarderFunction",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="log_forwarder.handler",
            code=_lambda.Code.from_asset("refvision/functions/log_forwarder"),
            timeout=Duration.seconds(30),
            environment={"COMBINED_LOG_GROUP": combined_log_group.log_group_name},
        )

        # noinspection PyTypeChecker
        combined_log_group.grant_write(log_forwarder)

        # noinspection PyTypeChecker
        video_ingestion_log_group.add_subscription_filter(
            "VideoIngestionSubscription",
            destination=logs_destinations.LambdaDestination(log_forwarder),
            filter_pattern=logs.FilterPattern.all_events(),
        )

        # noinspection PyTypeChecker
        preprocessing_log_group.add_subscription_filter(
            "PreprocessingSubscription",
            destination=logs_destinations.LambdaDestination(log_forwarder),
            filter_pattern=logs.FilterPattern.all_events(),
        )

        # firehose Setup
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
        delivery_stream = firehose.CfnDeliveryStream(
            self,
            "DeliveryStream",
            delivery_stream_name=f"RefVisionFirehoseStream-{cdk.Aws.ACCOUNT_ID}-{cdk.Aws.REGION}",
            delivery_stream_type="DirectPut",
            s3_destination_configuration=firehose.CfnDeliveryStream.S3DestinationConfigurationProperty(
                bucket_arn=video_bucket_1.bucket_arn,
                role_arn=firehose_role.role_arn,
            ),
        )

        delivery_stream.node.add_dependency(video_bucket_1)
        delivery_stream.node.add_dependency(firehose_role)


# create the App instance.
app = App()

# define the stack environment.
env = Environment(account="001499655372", region="ap-southeast-2")

# instantiate the stack.
RefVisionStack(
    app, "RefVisionStack", description="RefVision Infrastructure Stack", env=env
)

# synthesize the stack.
app.synth()


# todo: Future considerations (placeholders):
#  - Route 53,
#  - EventBridge rules to trigger Lambdas on S3 events or other custom events.
#  - Scaling and autoscaling policies.
#  - Bedrock for natural language explanation of the decisions made by the model.
#  - hosting
