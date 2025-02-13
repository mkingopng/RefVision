# scripts/aws_cost_cleanup.py
"""
This script is used to cleanup the AWS cost by deleting the resources which are
not in use.

- Checks your current AWS spend using Cost Explorer.
- If costs exceed the threshold, it automatically destroys your CDK stack.
- If costs are below the threshold, it lists AWS resources (S3, Lambda, Step Functions).
- Asks if you want to clean up manually before destroying anything.

Usage: poetry run python scripts/aws_cost_cleanup.py
"""
import boto3
import datetime
import os
import sys

# Configuration
COST_THRESHOLD = 20.00  # Set your AWS budget threshold in USD
STACK_NAME = "RefVisionStack"  # Update with your CDK stack name
LOG_FILE = "logs/aws_cost_log.txt"

# AWS Clients
ce = boto3.client("ce")
cf = boto3.client("cloudformation")
s3 = boto3.client("s3")
lambda_client = boto3.client("lambda")
stepfunctions = boto3.client("stepfunctions")


def log_message(message):
	"""Write a message to the log file with a timestamp."""
	timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
	log_entry = f"[{timestamp}] {message}\n"
	with open(LOG_FILE, "a") as log_file:
		log_file.write(log_entry)
	print(log_entry.strip())  # Print for visibility in CLI


def get_monthly_cost():
	"""Fetch the current month's AWS cost."""
	today = datetime.date.today()
	start_date = today.replace(day=1).isoformat()
	end_date = today.isoformat()

	response = ce.get_cost_and_usage(
		TimePeriod={"Start": start_date, "End": end_date},
		Granularity="MONTHLY",
		Metrics=["UnblendedCost"],
	)

	cost = float(
		response["ResultsByTime"][0]["Total"]["UnblendedCost"]["Amount"])
	return cost


def destroy_cdk_stack():
	"""Destroy the CloudFormation stack."""
	log_message(f"🚨 Destroying CloudFormation stack: {STACK_NAME}...")
	os.system(f"cdk destroy {STACK_NAME} -f")


def list_s3_buckets():
	"""List S3 buckets used in the project."""
	response = s3.list_buckets()
	buckets = [bucket["Name"] for bucket in response["Buckets"]]
	log_message(f"📂 S3 Buckets: {', '.join(buckets) if buckets else 'None'}")
	return buckets


def list_lambda_functions():
	"""List deployed Lambda functions."""
	response = lambda_client.list_functions()
	functions = [function["FunctionName"] for function in
				 response["Functions"]]
	log_message(
		f"🚀 Lambda Functions: {', '.join(functions) if functions else 'None'}")
	return functions


def list_step_functions():
	"""List Step Functions used in the project."""
	response = stepfunctions.list_state_machines()
	sm_list = [f"{sm['name']} ({sm['stateMachineArn']})" for sm in
			   response["stateMachines"]]
	log_message(
		f"🔄 Step Functions: {', '.join(sm_list) if sm_list else 'None'}")
	return sm_list


def manual_cleanup():
	"""List all resources and allow manual cleanup."""
	log_message("\n🛠️ [Listing AWS Resources for Cleanup Review]")
	list_s3_buckets()
	list_lambda_functions()
	list_step_functions()

	confirm = input(
		"\n❓ Would you like to proceed with `cdk destroy`? (yes/no): ").strip().lower()
	if confirm == "yes":
		destroy_cdk_stack()
	else:
		log_message("✅ Skipping automatic cleanup.")


if __name__ == "__main__":
	try:
		log_message(
			"\n================ AWS Cost & Cleanup Check =================")

		cost = get_monthly_cost()
		log_message(f"💰 AWS Monthly Cost: ${cost:.2f}")

		if cost > COST_THRESHOLD:
			log_message("🚨 Cost threshold exceeded! Running cleanup...")
			destroy_cdk_stack()
		else:
			log_message(
				"✅ Cost is within budget. Listing resources for review.")
			manual_cleanup()

		log_message("✅ Session cleanup complete.\n")

	except Exception as e:
		log_message(f"❌ Error: {str(e)}")
		sys.exit(1)
