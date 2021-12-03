import codegrade
import csv
import json

def get_webhook(session, assignment_id, user):
    webhook = session.assignment.get_webhook_settings(assignment_id = assignment_id, webhook_type = "git", author_id = user)
    return {'id': webhook.id, 'public_key': webhook.public_key, 'secret': webhook.secret}

def get_nonempty_groups(session, assignment_id, git_ids, access):
    assignment = session.assignment.get(assignment_id = assignment_id)
    group_set_id = assignment.group_set.id
    # Workaround a missing client function
    groups_request = session.http.request("get", "https://wur.codegra.de/api/v1/group_sets/" + str(group_set_id) + "/groups/")
    groups = json.loads(groups_request.content)
    # End workaround

    return [
        {
            'name': g["name"],
            'webhook': get_webhook(session, assignment_id, g['members'][0]["id"]),
            'git_ids': [
                git_ids[m['username']]
                for m in g['members']
            ],
        }
        for g in groups if g['members'] and all(u['username'] in git_ids for u in g['members'])
    ]

def get_users(session, assignment_id, git_ids, course_id):
    users = session.course.get_all_users(course_id = course_id)

    return [
        {
            'name': user.user.name,
            'git_ids': [ git_ids[user.user.username] ],
            'webhook': get_webhook(session, assignment_id, user.user.id)
        }
        for user in users if user.user.username in git_ids
    ]

def read_gitlab_ids(in_file):
    gitlab_ids = {}
    with open(in_file, 'r') as f:
        for row in csv.reader(f, delimiter=','):
            gitlab_ids[row[1]] = row[3]
    return gitlab_ids


def get_user(groups, username):
    for g in groups:
        for u in g['members']:
            if u['username'] == username:
                return u
    return None
    

def init_roster(access, organization, in_file, out_file, individual=False):
    print('Reading roster ...', end=' ', flush=True)

    gitlab_ids = read_gitlab_ids(in_file)
    print('done')

    print('Retrieving CodeGrade data ...', end=' ', flush=True)

    with codegrade.login(
        username=access['codegrade']['username'],
        password=access['codegrade']['password'],
        tenant=access['codegrade']['tenant'],
        host=access['codegrade']['host']
    ) as session:
        #pass
    
        if individual:
            groups = get_users(session=session,
                assignment_id=organization['assignment-id'],
                git_ids=gitlab_ids,
                course_id=organization['codegrade-id'])
        else:
            groups = get_nonempty_groups(
                session=session,
                assignment_id=organization['assignment-id'],
                git_ids=gitlab_ids,
                access=access
            )

        print('done')

        print('Writing', out_file, '...', end=' ', flush=True)

        with open(out_file, mode='w', newline='') as out:
            writer = csv.writer(out)
            writer.writerow(['name', 'git_ids', 'payload_url', 'secret', 'public_key'])
            for group_data in groups:
                webhook = group_data['webhook']
                ids = group_data['git_ids']

                writer.writerow([
                    group_data['name'],
                    ' '.join(group_data['git_ids']),
                    '{}/api/v1/webhooks/{}'.format(session.base_url, webhook['id']),
                    webhook['secret'],
                    webhook['public_key'],
                ])

        print('done')


def main():
    # CodeGrade username, CodeGrade password, GitHub API key
    with open("secrets.txt", "r") as secretfile:
        secrets = secretfile.read().splitlines()
        
    init_roster(
        access={
            'codegrade': {
                'host': "https://wur.codegra.de",
                'tenant': "Wageningen University",
                'username': secrets[0],
                'password': secrets[1],
            },
        },
        organization={
            'assignment-id': '98',
            'codegrade-id': 33,
        },
        in_file='usernames.csv',
        out_file='webhooks.csv',
        individual=False
    )


if __name__ == '__main__':
    main()
