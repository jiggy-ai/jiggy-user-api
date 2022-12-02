Jiggy is an collection of opensource components.

jiggy-user-api contains the User, Team, and API Key management endpoints common to all Jiggy components.

Currently a demo version of this is running at api.jiggy.ai (see https://api.jiggy.ai/jiggyuser-v0/docs#/ for API doc).


**Dependencies**

This Jiggy service depends on a PostgreSQL "jiggyuser" database.


Configuration for these services is passed via the following environment variables:


- JIGGY_POSTGRES_USER
- JIGGY_POSTGRES_PASS
- JIGGY_POSTGRES_HOST

In addition it needs the following environment variables for generating jwt keys:

- JIGGY_JWT_RSA_PRIVATE_KEY
- JIGGY_JWT_RSA_PUBLIC_KEY
