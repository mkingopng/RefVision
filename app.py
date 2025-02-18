# app.py - Main entry point for the CDK application
"""
Main entry point for the CDK application
"""
import aws_cdk as cdk
from ref_vision_infrastructure_stack import RefVisionStack

app = cdk.App()

# Instantiate the RefVision stack
RefVisionStack(app, "RefVisionStack")

# Synthesize the CloudFormation template
app.synth()
