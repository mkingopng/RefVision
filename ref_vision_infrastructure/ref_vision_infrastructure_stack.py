import aws_cdk as cdk
from aws_cdk import Stack
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_lambda as _lambda
from aws_cdk import aws_stepfunctions as sfn
from aws_cdk import aws_stepfunctions_tasks as tasks
from constructs import Construct

class RefVisionStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # S3 Bucket for video ingestion
        video_bucket = s3.Bucket(self, "RefVisionVideoBucket")

        # Lambda function for video ingestion
        ingestion_lambda = _lambda.Function(
            self, "VideoIngestionFunction",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="handler.lambda_handler",
            code=_lambda.Code.from_asset("functions/video_ingestion")
        )

        # Lambda function for preprocessing
        preprocessing_lambda = _lambda.Function(
            self, "PreprocessingFunction",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="handler.lambda_handler",
            code=_lambda.Code.from_asset("functions/preprocessing")
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
