#################################################################################################
##                                                                                             ##
##                                 NE PAS TOUCHER CETTE PARTIE                                 ##
##                                                                                             ##
## 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 ##

import boto3
from botocore.config import Config
import os
import uuid
from dotenv import load_dotenv
from typing import Union
import logging
from fastapi import FastAPI, Request, status, Header
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from boto3.dynamodb.conditions import Key #Ajout perso

from getSignedUrl import getSignedUrl

load_dotenv()

app = FastAPI()
logger = logging.getLogger("uvicorn")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
	exc_str = f'{exc}'.replace('\n', ' ').replace('   ', ' ')
	logger.error(f"{request}: {exc_str}")
	content = {'status_code': 10422, 'message': exc_str, 'data': None}
	return JSONResponse(content=content, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)


class Post(BaseModel):
    title: str
    body: str


my_config = Config(
    region_name='us-east-1',
    signature_version='v4',
)

dynamodb = boto3.resource('dynamodb', config=my_config)
table = dynamodb.Table(os.getenv("DYNAMO_TABLE"))
s3_client = boto3.client('s3', config=boto3.session.Config(signature_version='s3v4'))
bucket = os.getenv("BUCKET")

## ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ##
##                                                                                                ##
####################################################################################################




@app.post("/posts")
async def post_a_post(post: Post, authorization: str | None = Header(default=None)):
    """
    Poste un post ! Les informations du poste sont dans post.title, post.body et le user dans authorization
    """

    try:
        logger.info(f"Creation post {post.title} pour {authorization}")

        str_id = str(uuid.uuid4())
        user = str(authorization)

        # Ajout dans la table
        return table.put_item(Item={
            'user': f"USER#{user}",
            'id': f"ID_POST#{str_id}",
            'title': post.title,
            'body': post.body,
            'image': None,
            'label': None,
            'key': None
        })

    except Exception as e:
        logger.error(f"Erreur POST: {e}")
        return JSONResponse(content={"error": "Erreur interne du serveur"}, status_code=500)


@app.get("/posts")
async def get_all_posts(user: Union[str, None] = None):
    """
    Récupère tout les postes. 
    - Si un user est présent dans le requête, récupère uniquement les siens
    - Si aucun user n'est présent, récupère TOUS les postes de la table !!
    """
    
    try:
        if user:

            logger.info(f"Récupération post {user}")
            res = table.query(
                KeyConditionExpression=Key('user').eq(f"USER#{user}")
            )
        else:

            logger.info("Récupération tous les posts")
            res = table.scan()

        return res.get("Items", [])
    except Exception as e:
        logger.error(f"Erreur GET: {e}")
        return JSONResponse(content={"error": "Erreur interne du serveur"}, status_code=500)


    
@app.delete("/posts/{post_id}")
async def delete_post(post_id: str, authorization: str | None = Header(default=None)):
    """
    doc?
    """

    try:
        logger.info(f"Suppression de {post_id} pour {authorization}")

        # Récupération de la ligne dans la table
        response = table.get_item(
            Key={
                'user': f"USER#{authorization}",
                'id': f"ID_POST#{post_id}"
            }
        )
        item = response.get("Item")
        
        if not item:
            return JSONResponse(content={"error": "Pas de post"}, status_code=404)

        # Verifie si image S3 par presence de key voire la lambda
        if item.get("key"):
            try:
                s3_client.delete_object(Bucket=bucket, Key=item["key"])
                logger.info(f"Image supprimée de S3: {item['key']}")
            except Exception as image_e:
                logger.warning(f"Échec suppression image S3: {image_e}")

        return table.delete_item(
            Key={
                'user': f"USER#{authorization}",
                'id': f"ID_POST#{post_id}"
            }
        )

    except Exception as e:
        logger.error(f"Erreur DELETE : {e}")
        return JSONResponse(content={"error": "Erreur interne du serveur"}, status_code=500)




#################################################################################################
##                                                                                             ##
##                                 NE PAS TOUCHER CETTE PARTIE                                 ##
##                                                                                             ##
## 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 ##
@app.get("/signedUrlPut")
async def get_signed_url_put(filename: str,filetype: str, postId: str,authorization: str | None = Header(default=None)):
    return getSignedUrl(filename, filetype, postId, authorization)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="debug")

## ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ##
##                                                                                                ##
####################################################################################################