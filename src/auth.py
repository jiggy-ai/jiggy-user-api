
from fastapi import HTTPException
import jwt
import os
from sqlmodel import Session, select, or_
from fastapi.security import HTTPBearer 

from db import engine

from models import *


token_auth_scheme = HTTPBearer()
optional_token_auth_scheme = HTTPBearer(auto_error=False)


DOMAIN = "auth.jiggy.ai"
API_AUDIENCE = "https://api.jiggy.ai"
ALGORITHMS = ["RS256"]
ISSUER = "https://"+DOMAIN+"/"

jwks_url = 'https://%s/.well-known/jwks.json' % DOMAIN
jwks_client = jwt.PyJWKClient(jwks_url)



JWT_RSA_PUBLIC_KEY = os.environ['JIGGY_JWT_RSA_PUBLIC_KEY']
JWT_ISSUER = "Jiggy.AI"



def verify_jiggy_api_token(credentials):
    """Perform Jiggy API token verification using PyJWT.  raise HTTPException on error"""

    # This gets the 'kid' from the passed token credentials
    try:
        signing_key = JWT_RSA_PUBLIC_KEY
    except jwt.exceptions.PyJWKClientError as error:
        raise HTTPException(status_code=401, detail=str(error))
    except jwt.exceptions.DecodeError as error:
        raise HTTPException(status_code=401, detail=str(error))
    except Exception as error:
        raise HTTPException(status_code=401, detail=str(error))
    
    try:
        payload = jwt.decode(credentials,
                             signing_key,
                             algorithms=ALGORITHMS,
                             issuer=JWT_ISSUER)
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))
    return payload

    
def verify_auth0_token(credentials):
    """Perform auth0 token verification using PyJWT.  raise HTTPException on error"""
    # This gets the 'kid' from the passed token
    try:
        signing_key = jwks_client.get_signing_key_from_jwt(credentials).key
    except jwt.exceptions.PyJWKClientError as error:
        raise HTTPException(status_code=401, detail=str(error))
    except jwt.exceptions.DecodeError as error:
        raise HTTPException(status_code=401, detail=str(error))
    except Exception as error:
        raise HTTPException(status_code=401, detail=str(error))
    
    try:
        payload = jwt.decode(credentials,
                             signing_key,
                             algorithms=ALGORITHMS,
                             audience=API_AUDIENCE,
                             issuer=ISSUER)
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))
    return payload



def verified_user_id(token):
    """
    verify the supplied token and return the associated user_id
    """
    try:
        # first see if it is a token we issued from an API key
        user_id = verify_jiggy_api_token(token.credentials)['sub']
    except:
        # check if it is an auth0-issued token
        token_payload = verify_auth0_token(token.credentials)
        auth0_id = token_payload['sub']
        with Session(engine) as session:
            statement = select(User).where(User.auth0_userid == auth0_id)
            user = session.exec(statement).first()
            if user is None:
                raise HTTPException(status_code=400, detail="No user object found for auth0 subject. Must first create user.")
            user_id = user.id
    return user_id






user_teams = {}   # XXX expiring dict or a real cache

def verified_user_id_teams(token):
    """
    verify the supplied token and return the associated user id and list of the user's teams_ids
    """
    user_id = verified_user_id(token)
    # XXX cache team ids, or put them in the jwt?
    if user_id in user_teams:
        return user_id, user_teams[user_id]
    with Session(engine) as session:        
        statement = select(TeamMember).where(TeamMember.user_id == user_id)
        team_ids = [m.team_id for m in session.exec(statement)]
    user_teams[user_id] = team_ids
    return user_id, team_ids




    




