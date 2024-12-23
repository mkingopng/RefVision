# functions/cleanup/handler.py
"""

"""
import boto3
import json

s3 = boto3.client("s3")


def lambda_handler(event, context):
    """
    Lambda function to empty an S3 bucket before destruction.
    """
    print("Received event: " + json.dumps(event))

    try:
        bucket_name = event['ResourceProperties']['BucketName']

        # List and delete all objects
        paginator = s3.get_paginator("list_object_versions")
        pages = paginator.paginate(Bucket=bucket_name)

        for page in pages:
            if "Versions" in page:
                for version in page["Versions"]:
                    s3.delete_object(
                        Bucket=bucket_name, Key=version["Key"], VersionId=version["VersionId"]
                    )
            if "DeleteMarkers" in page:
                for marker in page["DeleteMarkers"]:
                    s3.delete_object(
                        Bucket=bucket_name, Key=marker["Key"], VersionId=marker["VersionId"]
                    )

        # Signal success back to CloudFormation
        return {"Status": "SUCCESS", "PhysicalResourceId": bucket_name}

    except Exception as e:
        print("Error cleaning up bucket: ", e)
        return {"Status": "FAILED", "Reason": str(e)}
