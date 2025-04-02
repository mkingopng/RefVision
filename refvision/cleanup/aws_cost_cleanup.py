# scripts/aws_cost_cleanup.py
#!/usr/bin/env python3
"""
This script cleans up AWS resources that are not in use.

- Checks your current AWS spend using Cost Explorer.
- If costs exceed the THRESHOLD, it automatically destroys your CDK stack.
- If costs are below the THRESHOLD, it lists AWS resources (S3, Lambda, Step Functions)
  used by the project.
- Asks if you want to clean up manually before destroying anything.

Usage: poetry run python aws_cost_cleanup.py
"""

import boto3
import datetime
import subprocess
import sys

# Import the centralized logging setup and configure it for cleanup logs.
from refvision.utils.logging_setup import setup_logging

# Set up a logger specifically for cleanup.
logger = setup_logging(log_file="../../logs/cleanup.log")  # DEBUG level

# Configuration
COST_THRESHOLD = 20.00  # Set your AWS budget THRESHOLD in USD
STACK_NAME = "RefVisionStack"  # Update with your CDK stack name

# AWS Clients
ce = boto3.client("ce")
cf = boto3.client("cloudformation")
s3 = boto3.client("s3")
lambda_client = boto3.client("lambda")
stepfunctions = boto3.client("stepfunctions")


def get_monthly_cost():
    """Fetch the current month's AWS cost."""
    today = datetime.date.today()
    start_date = today.replace(day=1).isoformat()
    end_date = today.isoformat()

    try:
        response = ce.get_cost_and_usage(
            TimePeriod={"Start": start_date, "End": end_date},
            Granularity="MONTHLY",
            Metrics=["UnblendedCost"],
        )
        cost = float(response["ResultsByTime"][0]["Total"]["UnblendedCost"]["Amount"])
        logger.debug("Fetched cost data: %s", response)
    except Exception as e:
        logger.error("Error fetching or parsing cost data: %s", e)
        cost = 0.0
    return cost


def destroy_cdk_stack():
    """Destroy the CloudFormation stack using subprocess."""
    logger.info("🚨 Destroying CloudFormation stack: %s...", STACK_NAME)
    try:
        subprocess.check_call(["cdk", "destroy", STACK_NAME, "-f"])
    except subprocess.CalledProcessError as e:
        logger.error("Error destroying stack: %s", e)
        sys.exit(1)


def list_s3_buckets():
    """List S3 buckets used in the project by filtering on bucket name prefix."""
    try:
        response = s3.list_buckets()
        buckets = [
            bucket["Name"]
            for bucket in response.get("Buckets", [])
            if "ref-vision" in bucket["Name"].lower()
        ]
    except Exception as e:
        logger.error("Error listing S3 buckets: %s", e)
        buckets = []
    logger.info("📂 S3 Buckets: %s", ", ".join(buckets) if buckets else "None")
    return buckets


def list_lambda_functions():
    """List deployed Lambda functions used by the project (filter by function name)."""
    try:
        response = lambda_client.list_functions()
        functions = [
            function["FunctionName"]
            for function in response.get("Functions", [])
            if any(
                kw in function["FunctionName"].lower()
                for kw in ["videoingestion", "preprocessing"]
            )
        ]
    except Exception as e:
        logger.error("Error listing Lambda functions: %s", e)
        functions = []
    logger.info(
        "🚀 Lambda Functions: %s", ", ".join(functions) if functions else "None"
    )
    return functions


def list_step_functions():
    """List Step Functions used by the project (filter by state machine name)."""
    try:
        response = stepfunctions.list_state_machines()
        sm_list = [
            f"{sm['name']} ({sm['stateMachineArn']})"
            for sm in response.get("stateMachines", [])
            if "refvision" in sm["name"].lower()
        ]
    except Exception as e:
        logger.error("Error listing Step Functions: %s", e)
        sm_list = []
    logger.info("🔄 Step Functions: %s", ", ".join(sm_list) if sm_list else "None")
    return sm_list


def manual_cleanup():
    """List filtered AWS resources and allow manual cleanup."""
    logger.info("\n🛠️ [Listing AWS Resources for Cleanup Review]")
    list_s3_buckets()
    list_lambda_functions()
    list_step_functions()

    confirm = (
        input("\n❓ Would you like to proceed with `cdk destroy`? (yes/no): ")
        .strip()
        .lower()
    )
    if confirm == "yes":
        destroy_cdk_stack()
    else:
        logger.info("✅ Skipping automatic cleanup.")


if __name__ == "__main__":
    try:
        logger.info("\n================ AWS Cost & Cleanup Check =================")
        cost = get_monthly_cost()
        logger.info("💰 AWS Monthly Cost: $%.2f", cost)

        if cost > COST_THRESHOLD:
            logger.warning("🚨 Cost THRESHOLD exceeded! Running cleanup...")
            destroy_cdk_stack()
        else:
            logger.info("✅ Cost is within budget. Listing resources for review.")
            manual_cleanup()

        logger.info("✅ Session cleanup complete.\n")

    except Exception as e:
        logger.error("❌ Error: %s", e)
        sys.exit(1)
