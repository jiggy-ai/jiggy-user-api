from typing import Optional, List

from sqlmodel import Field, SQLModel, Column, ARRAY, Float, Enum
from pydantic import BaseModel, ValidationError, validator
from array import array
from pydantic import condecimal
import json
from time import time
import enum
import re

timestamp = condecimal(max_digits=14, decimal_places=3)


    

###
## API Key
###

class ApiKey(SQLModel, table=True):
    id:          int           = Field(primary_key=True, description='ID for this key')
    key:         str           = Field(index=True, description='Unique secret api key')
    user_id:     int           = Field(index=True, foreign_key='user.id', description='The user_id that owns this key.')
    description: Optional[str] = Field(default=None, description='Optional user supplied description of the key.')
    created_at:  timestamp     = Field(default_factory=time, description='The epoch timestamp when the vector was created.')
    last_used :  timestamp     = Field(default_factory=time, description='The epoch timestamp when the key was last used to create a JWT.')

class  ApiKeyRequest(BaseModel):
    description: Optional[str] = Field(default=None, description='Optional user supplied description of the key.')

class AllApiKeyResponse(BaseModel):
    items: list[ApiKey] = Field(description="List of all Api Keys")

###
##  Auth
###

class AuthRequest(BaseModel):
    key : str = Field(description = "The API key")
    
class Jwt(BaseModel):
    jwt: str = Field(description='The JWT to used as bearer token')


###
## User
###

class User(SQLModel, table=True):
    id:              int           = Field(primary_key=True, description="Internal user_id")
    username:        str           = Field(index=True, min_length=3, max_length=39, description='Unique name for the user.')
    auth0_userid :   Optional[str] = Field(default=None, index=True, description='Auth0 userid.')
    default_team_id: int           = Field(description="The default team for this user")


class UserPostRequest(BaseModel):
    username: str = Field(min_length=3, max_length=39, description='Unique name for the user.')
    

class UserPostPatchRequest(BaseModel):
    default_team_id: Optional[int] = Field(description="The default team for this user")
    username:        Optional[str] = Field(min_length=3, max_length=39, description='Unique name for the user.')

    
###
## Team
###

class Team(SQLModel, table=True):
    id:          int           = Field(primary_key=True, description="Internal team id")
    name:        str           = Field(index=True, min_length=3, max_length=39, description='Unique name for this team.')
    description: Optional[str] = Field(default=None, description='Optional user supplied description.')
    created_at:  timestamp     = Field(default_factory=time, description='The epoch timestamp when the team was created.')
    updated_at:  timestamp     = Field(default_factory=time, description='The epoch timestamp when the team was updated.')


class TeamPostRequest(BaseModel):
    name:        str           = Field(min_length=3, max_length=39, description='Unique name for this team.')
    description: Optional[str] = Field(default=None, max_length=255, description='Optional user supplied description.')

class TeamPatchRequest(BaseModel):
    name:        Optional[str] = Field(default=None, min_length=3, max_length=39, description='Unique name for this team.')
    description: Optional[str] = Field(default=None, max_length=255, description='Optional user supplied description.')
    
    
class TeamRole(str, enum.Enum):
    admin   = 'admin'
    member  = 'member'
    service = 'service'
    view    = 'view'


class TeamMember(SQLModel, table=True):
    id:         int       = Field(primary_key=True, description="Internal membership id")
    team_id:    int       = Field(index=True, description="The team_id that the associated user is a member of.")
    user_id:    int       = Field(index=True, description="The user_id that is  a member of the associated team.")
    created_at: timestamp = Field(default_factory=time, description='The epoch timestamp when the membership was created.')
    updated_at: timestamp = Field(default_factory=time, description='The epoch timestamp when the membership was updated.')
    invited_by: int       = Field(index=True, description="The user that invited this member to the team.")
    role:       TeamRole  = Field(sa_column=Column(Enum(TeamRole)), description="The user's role in the team")
    accepted:   bool      = Field(default=False, description='True if the user has accepted the team membership.')


class TeamMemberPostRequest(BaseModel):
    username: str      = Field(description="The user_name of a member to invite to the team.")
    role:     TeamRole = Field(description="The user's role in the team")


class TeamMemberPatchRequest(BaseModel):
    role:       TeamRole  = Field(sa_column=Column(Enum(TeamRole)), description="The user's role in the team")
    accepted:   bool      = Field(default=False, description='True if the user has accepted the team membership.')

    
class UserTeams(BaseModel):
    items: List[Team] = Field(description="The list of all of the user's teams")

    
class TeamMemberResponse(BaseModel):
    id:                  int       = Field(description="Internal membership id")
    username:            str       = Field(description="Member username")
    created_at:          timestamp = Field(description='The epoch timestamp when the membership was created.')
    updated_at:          timestamp = Field(description='The epoch timestamp when the membership was updated.')
    invited_by_username: str       = Field(description="The username that invited this member to the team.")
    role:                TeamRole  = Field(description="The user's role in the team")
    accepted:            bool      = Field(description='True if the user has accepted the team membership.')
    
    
class GetTeamMembersResponse(BaseModel):
    items: List[TeamMemberResponse] = Field(description="List of Team Members")
