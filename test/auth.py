#!/usr/bin/env python3.9

# test auth0 authentication 

import requests
from os import environ
import sys


AUTH0_CLIENT_ID=environ['JIGGY_AUTH0_CLIENT_ID']
AUTH0_CLIENT_SECRET=environ['JIGGY_AUTH0_CLIENT_SECRET']

payload = {"client_id":     AUTH0_CLIENT_ID,
           "client_secret": AUTH0_CLIENT_SECRET,
           "audience":      "https://api.jiggy.ai",
           "grant_type":    "client_credentials"}

resp = requests.post("https://auth.jiggy.ai/oauth/token", json=payload)

token = resp.json()['access_token']
print("Got test token from auth0")
print(token)



class PrefixSession(requests.Session):
    def __init__(self, prefix_url=None, *args, **kwargs):
        super(PrefixSession, self).__init__(*args, **kwargs)
        self.prefix_url = prefix_url

    def request(self, method, url, *args, **kwargs):
        url = self.prefix_url + url
        print("~~~~~~~~~~~~~~~~~~~~~~~~\n", method, url)
        return super(PrefixSession, self).request(method, url, *args, **kwargs)

if 'LOCAL' in sys.argv:
    host = 'http://127.0.0.1:8000'
else:
    host = 'https://api.jiggy.ai'

prefix = "jiggyuser-v0"
    
s = PrefixSession('%s/%s' % (host, prefix))

s.headers.update({"authorization": "Bearer %s" % token})

r = s.get("/users/current")
if r.status_code == 200:
    # delete user
    user_id = r.json()['id']
    print("delete user_id", user_id)
    r = s.delete(f"/users/{user_id}")
    if r.status_code != 200: print(r.content)
    assert(r.status_code==200)


r = s.post("/users", json={'username': "foobar"})
assert(r.status_code == 200)
print(r.json())

r = s.post("/apikey", json={'description':'mykey'})
assert(r.status_code == 200)
apikey = r.json()
assert(apikey['description'] == 'mykey')
key = apikey['key']


r = s.post("/auth", json={'key':key})
assert(r.status_code == 200)
print(r.json())


r = s.get("/apikey")
assert(r.status_code == 200)

for k in r.json()['items']:
    print(k)
    kid = k["id"]
    r = s.delete(f'/apikey/{kid}')
    assert(r.status_code == 200)

r = s.get("/apikey")
assert(r.status_code == 200)
assert(len(r.json()['items']) == 0)


##
## Team
##

r = s.get("/teams")
assert(r.status_code == 200)
teams = r.json()['items']
assert(len(teams) == 1)
assert(teams[0]['id'] == s.get("/users/current").json()['default_team_id'])


# create_team
# delete team (TODO)
# negative test removing solo admin

# todo: need additional test users to fully test teams

##
## Cleanup
##

r = s.get("/users/current")
if r.status_code == 200:
    # delete user
    user_id = r.json()['id']
    print("delete user_id", user_id)
    r = s.delete(f"/users/{user_id}")
    if r.status_code != 200: print(r.content)
    assert(r.status_code==200)

