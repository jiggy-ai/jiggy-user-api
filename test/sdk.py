import jiggy

print("current_user", jiggy.authenticated_user())

print("all_teams", jiggy.all_teams())

#jiggy.delete_team("jiggy-test")

#jt = jiggy.create_team("jiggy-test")

jt = jiggy.team("jiggy-test")
print(jt)
jt.delete_member('why812')

tm = jt.add_member('why812', 'admin')
print(tm)

print(jt.members())
