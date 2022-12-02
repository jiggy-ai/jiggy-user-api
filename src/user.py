# Jiggy User endpoints
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



###
### Users
###

@app.post('/users', response_model=User)
def post_users(token: str = Depends(token_auth_scheme), body: UserPostRequest = ...) -> User:
    """
    Create new User and associate it with the auth0 token used to authenticate this call.
    This can only be called by a frontend user authenticated via auth0;
    An API Key can not be used to create a new user.
    """
    logger.info(body)

    token_payload = verify_auth0_token(token.credentials)
    auth0_id = token_payload['sub']
    with Session(engine) as session:
        # verify auth0 id does not exist
        statement = select(User).where(User.auth0_userid == auth0_id)
        if session.exec(statement).first():
            raise HTTPException(status_code=400, detail="The authenticated user already exists.")

        statement = select(User).where(User.username == body.username)
        if list(session.exec(statement)):
            raise HTTPException(status_code=409, detail="The specified username is not available.")
        # create user's own team
        team = Team(name=body.username)
        session.add(team)
        session.commit()
        session.refresh(team)

        # create user's object, with default team of his own team        
        user = User(**body.dict(exclude_unset=True),
                    default_team_id=team.id,
                    auth0_userid = auth0_id)
        
        session.add(user)
        session.commit()
        session.refresh(user)
        # Add user as member of his own team
        member = TeamMember(team_id=team.id,
                            user_id=user.id,
                            invited_by=user.id,
                            role=TeamRole.admin,
                            accepted=True)

        session.add(member)

        # create apikey for user
        key = ApiKey(user_id = user.id,
                     key = "jgy-" + "".join([sample(ascii_lowercase,1)[0] for x in range(48)]))
        session.add(key)
        session.commit()
        session.refresh(user)
        return user




@app.get('/users/current', response_model=User)
def get_users_current(token: str = Depends(token_auth_scheme)) -> User:
    """
    return the authenticated user
    """
    user_id = verified_user_id(token)
    with Session(engine) as session:
        return session.get(User, user_id)





@app.delete('/users/{user_id}')
def delete_users_user_id(token: str = Depends(token_auth_scheme),
                         user_id: str = Path(...)):
    """
    Delete specified user
    """
    token_user_id = verified_user_id(token)
    if int(token_user_id) != int(user_id):
        raise HTTPException(status_code=401, detail="Authenticated user does not match the requested user_id")
    
    with Session(engine) as session:
        user = session.get(User, user_id)
        logger.info(user)
        session.exec(delete(TeamMember).where(TeamMember.user_id == user_id))
        session.exec(delete(ApiKey).where(ApiKey.user_id == user_id))
        session.exec(delete(Team).where(Team.name == user.username))
        session.delete(user)
        session.commit()
