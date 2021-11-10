import csv
import sys
from urllib.parse import urljoin

import requests

class CGSession(requests.Session):
    def __init__(self, base_url, access_token, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.base_url = base_url

        self.headers.update({
            'Authorization': 'Bearer {}'.format(access_token),
        })

    def request(self, method, url, *args, **kwargs):
        url = urljoin(self.base_url, url)
        return self.handle_response(super().request(method, url, *args, **kwargs))

    @classmethod
    def login(cls, subdomain, username, password):
        base_url = 'https://{}.codegra.de'.format(subdomain)
        r = cls.handle_response(
            requests.post(
                base_url + '/api/v1/login',
                json={ 'username': username, 'password': password },
            ),
        )
        return cls(base_url, r['access_token'])

    @staticmethod
    def handle_response(res):
        if res.status_code >= 400:
            msg = res.json()['message']
            print(
                'A CodeGrade request went wrong: {}\n{}'.format(
                    res.url,
                    msg,
                ),
                file=sys.stderr,
            )
            exit(1)
        return res.json()


def get_webhook(session, assignment_id, user):
    return session.post(
        '/api/v1/assignments/{}/webhook_settings?webhook_type=git&author={}'.format(
            assignment_id,
            user['username'],
        ),
    )


def get_nonempty_groups(session, assignment_id, github_ids):
    assignment = session.get('/api/v1/assignments/{}'.format(assignment_id))
    group_set_id = assignment['group_set']['id']
    groups = session.get('/api/v1/group_sets/{}/groups/'.format(group_set_id))

    return [
        {
            'group': g,
            'webhook': get_webhook(session, assignment_id, g['members'][0]),
            'github_ids': [
                github_ids[m['username']]
                for m in g['members']
            ],
        }
        for g in groups if g['members'] and all(u['username'] in github_ids for u in g['members'])
    ]

def get_users(session, assignment_id, github_ids, course_id):
    assignment = session.get('/api/v1/assignments/{}'.format(assignment_id))
    users = session.get('/api/v1/courses/{}/users/'.format(course_id))

    return [
        {
            'group': user['User'],
            'webhook': get_webhook(session, assignment_id, user['User']),
            'github_ids': [ github_ids[user['User']['username']] ],
        }
        for user in users if user['User']['username'] in github_ids
    ]

def read_github_ids(in_file):
    github_ids = {}
    with open(in_file, 'r') as f:
        for row in csv.reader(f, delimiter=','):
            github_ids[row[0]] = row[1]
    return github_ids


def get_user(groups, username):
    for g in groups:
        for u in g['members']:
            if u['username'] == username:
                return u
    return None


def init_roster(access, organization, in_file, out_file, individual=False):
    print('Reading roster ...', end=' ', flush=True)

    github_ids = read_github_ids(in_file)
    print('done')

    print('Retrieving CodeGrade data ...', end=' ', flush=True)

    session = CGSession.login(
        subdomain=access['codegrade']['subdomain'],
        username=access['codegrade']['username'],
        password=access['codegrade']['password'],
    )

    if individual:
        groups = get_users(session=session,
            assignment_id=organization['assignment-id'],
            github_ids=github_ids,
            course_id=organization['codegrade-id'])
    else:
        groups = get_nonempty_groups(
            session=session,
            assignment_id=organization['assignment-id'],
            github_ids=github_ids,
        )

    print('done')

    print('Writing', out_file, '...', end=' ', flush=True)

    with open(out_file, mode='w', newline='') as out:
        writer = csv.writer(out)
        writer.writerow(['group_name', 'github_ids', 'payload_url', 'secret', 'public_key'])
        for group_data in groups:
            webhook = group_data['webhook']
            ids = group_data['github_ids']

            writer.writerow([
                group_data['group']['name'],
                ' '.join(group_data['github_ids']),
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
                'subdomain': 'wur',
                'username': secrets[0],
                'password': secrets[1],
            },
        },
        organization={
            'assignment-id': '75',
            'codegrade-id': 14,
        },
        in_file='github_ids.csv',
        out_file='github_webhooks.csv',
        individual=True
    )


if __name__ == '__main__':
    main()
