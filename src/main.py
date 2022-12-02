# Jiggy API
# Copyright (C) 2022 William S. Kish
#

from __future__ import annotations
from fastapi import FastAPI
import os

from loguru import logger

API_PATH = os.environ.get("API_PATH", "jiggyuser-v0")
API_HOST = os.environ.get("API_HOST", "api.jiggy.ai")

app = FastAPI( title='jiggyuser-api',
               version='0.1',
               summary='Jiggy User API',
               description='',
               contact={},
               servers=[{'url': f'https://{API_HOST}/{API_PATH}'}], )


app.mount(f"/{API_PATH}", app)

# import endpoints
import user
import apikey
import team

logger.info(f"{API_HOST}/{API_PATH}")
