#!/usr/bin/env python
from constructs import Construct
from cdktf import App, TerraformStack
from imports.aws.s3_bucket import S3Bucket
from imports.aws.dynamodb_table import DynamodbTable, DynamodbTableAttributef


class MyStack(TerraformStack):
    def __init__(self, scope: Construct, id: str):
        super().__init__(scope, id)

app = App()
MyStack(app, "ter")

app.synth()
