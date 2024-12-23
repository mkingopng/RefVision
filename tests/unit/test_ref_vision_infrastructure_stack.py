import aws_cdk as core
import aws_cdk.assertions as assertions

from ref_vision_infrastructure.ref_vision_infrastructure_stack import RefVisionInfrastructureStack

# example tests. To run these tests, uncomment this file along with the example
# resource in ref_vision_infrastructure/ref_vision_infrastructure_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = RefVisionInfrastructureStack(app, "ref-vision-infrastructure")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
