# functions/cleanup/handler.py
"""

"""
import boto3
import json
import os

s3 = boto3.client('s3')


def lambda_handler(event, context):
	"""

	:param event:
	:param context:
	:return:
	"""
	bucket_name = event['ResourceProperties']['BucketName']

	# List all object versions and delete them
	paginator = s3.get_paginator('list_object_versions')
	for page in paginator.paginate(Bucket=bucket_name):
		versions = page.get('Versions', []) + page.get('DeleteMarkers', [])
		for version in versions:
			s3.delete_object(
				Bucket=bucket_name,
				Key=version['Key'],
				VersionId=version['VersionId']
			)

	return {'Status': 'SUCCESS'}
