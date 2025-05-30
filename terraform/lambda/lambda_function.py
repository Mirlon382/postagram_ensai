import json
from urllib.parse import unquote_plus
import boto3
import os
import logging
from datetime import datetime

print('Loading function')
logger = logging.getLogger()
logger.setLevel("INFO")
s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
reckognition = boto3.client('rekognition')
table_name = os.getenv("TABLE")
table = dynamodb.Table(table_name)

def lambda_handler(event, context):
    logger.info(json.dumps(event, indent=2))
    bucket = event["Records"][0]["s3"]["bucket"]["name"]
    
    # Récupération de l'utilisateur et de l'UUID de la tâche
    key = unquote_plus(event["Records"][0]["s3"]["object"]["key"])

    # Ajout des tags user et task_uuid
    user, task_uuid = key.split('/')[:2]

    #url bucket
    expiration=3600
    try:
        response = s3.generate_presigned_url('get_object',
        Params={'Bucket': bucket,
        'Key': key},
        ExpiresIn=expiration)
        url = response
    except ClientError as e:
        logging.error(e)

    # Appel à reckognition
    label_data = reckognition.detect_labels( 
            Image={
                "S3Object": {
                    "Bucket": bucket,
                    "Name": key
                }
            },
            MaxLabels=5,
            MinConfidence=0.75
        )
    logger.info(f"Labels data : {label_data}")

    # Récupération des résultats des labels
    labels = [label["Name"] for label in label_data["Labels"]]
    logger.info(f"Labels detected : {labels}")

    # Mise à jour de la table dynamodb avec label url et key
    table.update_item(
        Key={
        "user": f"USER#{user}",
        "id": f"ID_POST#{task_uuid}"
        },
        UpdateExpression="SET label = :lab, #k = :key, image = :url",
        ExpressionAttributeValues={":lab": labels, ":key": key, ":url": url},
        ExpressionAttributeNames={"#k": "key"}  # 'key' is a reserved word!
        )