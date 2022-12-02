# Jiggy API Key endpoints
# Copyright (C) 2022 William S. Kish


from __future__ import annotations
from loguru import logger
from sqlmodel import Session, select, delete
from string import ascii_lowercase
from random import sample
from fastapi import Path, Query, Depends, HTTPException

from main import app
from auth import *
from db import engine
from models import *



JWT_RSA_PUBLIC_KEY = os.environ['JIGGY_JWT_RSA_PUBLIC_KEY']
JWT_RSA_PRIVATE_KEY = os.environ['JIGGY_JWT_RSA_PRIVATE_KEY']
JWT_ISSUER = "Jiggy.AI"


@app.post('/auth', response_model=Jwt)
def post_auth(body: AuthRequest = ...) -> Jwt:
    """
    trade an API key for a JWT Bearer token that can be used to authenticate subsequent API operations.
    """
    with Session(engine) as session:    
        apikey = session.get(ApiKey, body.key)
        if not apikey:
            logger.info("invalid API key")
            raise HTTPException(status_code=401, detail="Invalid Key")

        apikey.last_used = time()
        session.add(apikey)
        session.commit()
        iat = int(time())
        token_info = {'iat':  iat,
                      'exp':  iat + 15*60, 
                      'iss':  JWT_ISSUER,
                      'sub':  apikey.user_id}

        token = jwt.encode(token_info, JWT_RSA_PRIVATE_KEY, algorithm='RS256')
        return Jwt(jwt=token)


    
def create_apikey(user_id, description=None):
    """
    create an API key for the specified username
    """
    key = ApiKey(key = "jgy-" + "".join([sample(ascii_lowercase,1)[0] for x in range(48)]),
                 user_id = user_id,
                 description = description)
    
    with Session(engine) as session:
        session.add(key)
        session.commit()
        session.refresh(key)                
    return ApiKeyResponse(**key.dict())
    

@app.post("/apikey", response_model=ApiKeyResponse)
def post_apikey(token: str = Depends(token_auth_scheme),
                body: ApiKeyRequest = ...) -> ApiKeyResponse:
    """
    create an API key for an authenticated user
    """
    user_id = verified_user_id(token)        
    return create_apikey(user_id, body.description)



@app.get("/apikey", response_model=AllApiKeyResponse)
def get_apikey(token: str = Depends(token_auth_scheme)) -> AllApiKeyResponse:
    """
    return all of the user's API keys
    """
    user_id = verified_user_id(token)        
    with Session(engine) as session:
        statement = select(ApiKey).where(ApiKey.user_id == user_id)
        keys = list(session.exec(statement))
        return AllApiKeyResponse(items=keys)




@app.delete('/apikey/{api_key}')
def delete_apikey(token: str = Depends(token_auth_scheme),
                  api_key: str = Path(...)):
    """
    delete the specified api key.
    """
    user_id = verified_user_id(token)        
    
    with Session(engine) as session:    
        apikey = session.get(ApiKey, body.key)
        if not apikey or apikey.user_id != user_id:
            raise HTTPException(status_code=404, detail="Invalid Key")
        session.delete(apikey)
        session.commit()


