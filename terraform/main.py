#!/usr/bin/env python
from constructs import Construct
from cdktf import App, TerraformStack
from imports.aws.s3_bucket import S3Bucket
from imports.aws.dynamodb_table import DynamodbTable, DynamodbTableAttributef


class MyStack(TerraformStack):
    def __init__(self, scope: Construct, id: str):
        super().__init__(scope, id)

        # define resources here
        bucket = S3Bucket(
            self, "s3_bucket",
            bucket_prefix="bucket_image",
            force_destroy=True
            )
        DB_post = DynamodbTable(self,"DynamoDB-post",
            name = "postagram_post",
            hash_key="user",
            range_key="title",
            attribute=[
                DynamodbTableAttribute(name="user",type="S" ),
                DynamodbTableAttribute(name="id",type="S" ),
                DynamodbTableAttribute(name="title",type="S" ),
                DynamodbTableAttribute(name="body",type="S" ),
                DynamodbTableAttribute(name="image",type="S" ),
                DynamodbTableAttribute(name="label",type="S" )
                ],
            billing_mode="PROVISIONED",
            read_capacity=5,
            write_capacity=5
            )

app = App()
MyStack(app, "ter")

app.synth()
