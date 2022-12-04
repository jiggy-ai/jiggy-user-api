# Jiggy Team endpoints
# Copyright (C) 2022 William S. Kish


from __future__ import annotations
from loguru import logger
from sqlmodel import Session, select, delete
from string import ascii_lowercase
from random import sample
from fastapi import Path, Query, Depends, HTTPException
from time import time

from main import app
from auth import *
from db import engine
from models import *



@app.get('/teams')
def get_teams(token: str = Depends(token_auth_scheme)) -> UserTeams:
    """
    return all of the user's teams
    """
    user_id, user_team_ids = verified_user_id_teams(token)
    with Session(engine) as session:
        items = session.exec(select(Team).where(Team.id.in_(user_team_ids))).all()
        return UserTeams(items = items)
    
              
@app.post('/teams', response_model=Team)
def post_team(token: str = Depends(token_auth_scheme),
              body: TeamPostRequest = ...) -> Team:
    """
    Create a Team with the specified name.  Names must currently be unique.
    """
    logger.info(body)    
    user_id, user_team_ids = verified_user_id_teams(token)
    with Session(engine) as session:    
        statement = select(Team).where(Team.name == body.name)
        if list(session.exec(statement)):
            raise HTTPException(status_code=409, detail="The specified team name is not available.")
        
        team = Team(name=body.name, description=body.description)
        session.add(team)
        session.commit()
        session.refresh(team)

        member = TeamMember(team_id=team.id,
                            user_id=user_id,
                            invited_by=user_id,
                            role=TeamRole.admin,
                            accepted=False)
        session.add(member)
        session.commit()
        session.refresh(team)
        return team



@app.patch('/teams/{team_id}', response_model=Team)
def patch_team(token:   str = Depends(token_auth_scheme),
               team_id: int = Path(...),
               body: TeamPatchRequest = ...) -> Team:
    """
    Update Team
    """
    logger.info(body)
    user_id, user_team_ids = verified_user_id_teams(token)
    if team_id not in user_team_ids:
        raise HTTPException(status_code=404, detail="Team not found")
    with Session(engine) as session:    
        team = session.get(Team, team_id)
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")            

        for key, value in body.dict(exclude_unset=True).items():
            setattr(team, key, value)
        team.updated_at = time()
        session.add(team)
        session.commit()
        session.refresh(team)
        return team
    



@app.get('/teams/{team_id}/members', response_model=GetTeamMembersResponse)
def get_team_team_id_member(token: str = Depends(token_auth_scheme),
                            team_id: int = Path(...)) -> GetTeamMembersResponse:
    """
    Get all members of the specified team
    """
    user_id, user_team_ids = verified_user_id_teams(token)
    if team_id not in user_team_ids:
        raise HTTPException(status_code=404, detail="Team not found")
    with Session(engine) as session:
        members = []
        for member in session.exec(select(TeamMember).where(TeamMember.team_id == team_id)):
            tmr = TeamMemberResponse(**member.dict(),
                                     username            = session.get(User, member.user_id).username,
                                     invited_by_username = session.get(User, member.invited_by).username)
            members.append(tmr)
        return GetTeamMembersResponse(items=members)

    
    
        
@app.post('/teams/{team_id}/members', response_model=TeamMemberResponse)
def post_team_member(token: str = Depends(token_auth_scheme),
                     team_id: int = Path(...),
                     body: TeamMemberPostRequest = ...) -> TeamMemberResponse:

    logger.info(body)
    user_id, user_team_ids = verified_user_id_teams(token)
    if team_id not in user_team_ids:
        raise HTTPException(status_code=404, detail="Team not found")
    with Session(engine) as session:    
        team = session.get(Team, team_id)
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")
        
        # verify calling user is a member of the specified team
        statement = select(TeamMember).where(TeamMember.user_id == user_id, TeamMember.team_id == team_id)
        user_member = session.exec(statement).first()
        if not user_member:
            raise HTTPException(status_code=404, detail="Team not found")

        # verify user has sufficient permissions to add new user 
        if user_member.role not in [TeamRole.admin, TeamRole.member]:
            raise HTTPException(status_code=403, detail="Insufficient permissions to add member to the specified team.")

        # verify new user exists
        new_user = session.exec(select(User).where(User.username == body.username)).first()
        if not new_user:
            raise HTTPException(status_code=404, detail="User not found")

        # Verify new user is not already a member of the team
        statement = select(TeamMember).where(TeamMember.user_id == new_user.id, TeamMember.team_id == team_id)
        if list(session.exec(statement)):
            raise HTTPException(status_code=409, detail="User is already a member of the specified team.") 
        
        new_member = TeamMember(team_id=team.id,
                                user_id=new_user.id,
                                invited_by=user_id,
                                role=TeamRole.admin,
                                accepted=True)
        session.add(new_member)
        session.commit()
        session.refresh(new_member)
        return TeamMemberResponse(**new_member.dict(),
                                  username            = new_user.username,
                                  invited_by_username = session.get(User, user_id).username)


@app.delete('/teams/{team_id}/members/{member_id}')
def delete_team_member(token: str = Depends(token_auth_scheme),
                       team_id: int = Path(...),
                       member_id: int = Path(...)):
    """
    remove  the specified member from the team
    """
    user_id, user_team_ids = verified_user_id_teams(token)    
    if team_id not in user_team_ids:
        raise HTTPException(status_code=404, detail="Team not found")    
    with Session(engine) as session:    
        team = session.get(Team, team_id)
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")

        # verify calling user is a member of the specified team
        statement = select(TeamMember).where(TeamMember.user_id == user_id, TeamMember.team_id == team_id)
        user_member = session.exec(statement).first()
        if not user_member:
            raise HTTPException(status_code=404, detail="Team not found")  

        # get user membership entry that is the target of the request
        target_member = session.get(TeamMember, member_id)

        # determine if the requesting user is the target of the membership entry
        requesting_user_is_target = target_member.user_id == user_id
    
        # determine if the requesting user is an admin of the target collection
        requesting_user_is_admin = user_member.role == TeamRole.admin
    
        # reject the delete operation unless the requesting user is the target of the entry (removing himself from the collection)
        # or an admin of the target collection
        if not requesting_user_is_target and not requesting_user_is_admin:
            raise HTTPException(status_code=403, detail="Insufficient permission.")

        # prevent removal of admin unless there is another admin specified for the team
        if requesting_user_is_target and user_member.role == TeamRole.admin:
            statement = select(TeamMember).where(TeamMember.role == TeamRole.admin, TeamMember.team_id == team_id)
            num_admins = len(session.exec(statement))
            if num_admins == 1:
                raise HTTPException(status_code=403, detail="Team admin must designate another admin before removal.")
        session.delete(target_member)
        session.commit()



@app.patch('/teams/{team_id}/members/{member_id}', response_model=TeamMember)
def patch_team_member(token:     str = Depends(token_auth_scheme),
                      team_id:   int = Path(...),
                      member_id: int = Path(...),
                      body: TeamMemberPatchRequest = ...) -> TeamMember:
    
    """
    Change the role (admin only) or user's own accepted flag
    """
    logger.info(body)
    user_id, user_team_ids = verified_user_id_teams(token)    
    if team_id not in user_team_ids:
        raise HTTPException(status_code=404, detail="Team not found")    
    with Session(engine) as session:    
        team = session.get(Team, team_id)
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")

        # verify calling user is a member of the specified team
        statement = select(TeamMember).where(TeamMember.user_id == user_id, TeamMember.team_id == team_id)
        user_member = session.exec(statement).first()
        if not user_member:
            raise HTTPException(status_code=404, detail="Team not found")

        # get user membership entry that is the target of the request
        target_member = session.get(TeamMember, member_id)

        # reject change to role unless request made by admin
        requesting_user_is_admin = user_member.role == TeamRole.admin        
        if body.role is not None and not requesting_user_is_admin:
            raise HTTPException(status_code=403, detail="Insufficient permission.")

        # determine if the requesting user is the target of the membership entry
        requesting_user_is_target = target_member.user_id == user_id

        # disallow non-admin to change entries other than their own
        if not requesting_user_is_target and not requesting_user_is_admin:
            raise HTTPException(status_code=403, detail="Insufficient permission.")

        target_member.update(body.dict(exclude_unset=True))
        target_member.updated_at = time()
        
        session.commit()
        session.refresh(target_member)
        return(target_member)
        
