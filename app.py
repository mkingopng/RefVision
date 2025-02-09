# app.py - Main entry point for the CDK application
#!/usr/bin/env python3
import aws_cdk as cdk
from infrastructure.ref_vision_infrastructure_stack import RefVisionStack

app = cdk.App()

# Instantiate the RefVision stack
RefVisionStack(app, "RefVisionStack")

# Synthesize the CloudFormation template
app.synth()
