import codegrade

secrets_file = "gitlab/secrets.txt"
codegrade_tenant = "Wageningen University"
codegrade_host = "https://wur.codegra.de"
codegrade_course = 5027

with open(secrets_file, "r") as secretfile:
    secrets = secretfile.read().splitlines()

with codegrade.login(
        username=secrets[0],
        password=secrets[1],
        tenant=codegrade_tenant,
        host=codegrade_host
) as client:
    pass

groupsets = client.course.get_group_sets(course_id=codegrade_course)
groupsets

# Define source groupset
source_groupset = groupsets[0]

# Create a new target one, or select an existing target group
target_groupset = client.course.create_group_set({"minimum_size": 1, "maximum_size": 2}, course_id=codegrade_course)
#target_groupset = groupsets[2]

# Groups in the target groupset
source_groups = client.group_set.get_all_groups(group_set_id=source_groupset.id)

for source_group in source_groups:
    member_ids = [member.id for member in source_group.members]
    client.group_set.create_group({"member_ids":member_ids, "name":source_group.name}, group_set_id=target_groupset.id)
