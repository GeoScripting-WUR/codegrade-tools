import pprint

import sys
import csv
import getpass
from urllib.parse import urljoin
from github import Github

import requests

class CGSession(requests.Session):
    def __init__(self, prefix_url, access_token, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.prefix_url = prefix_url

        self.headers.update({
            'Authorization': 'Bearer {}'.format(access_token),
        })

    def request(self, method, url, *args, **kwargs):
        url = urljoin(self.prefix_url, url)
        return super().request(method, url, *args, **kwargs)


def handle_response(res):
    if res.status_code >= 400:
        print(
            'A CodeGrade request went wrong: {}'.format(res.json()['message']),
            file=sys.stderr)
        exit(1)
    return res.json()


def get_webhook_data_per_user(
    subdomain=None,
    username=None,
    password=None,
    course_id=None,
    assig_id=None,
):
    """Get the webhook data for an assignment for each student.
    """

    if subdomain is None:
        subdomain = input('Subdomain: ')
    if username is None:
        username = input('Username: ')
    if password is None:
        password = getpass.getpass('Password: ')
    if course_id is None:
        course_id = input('Course ID: ')
    if assig_id is None:
        assig_id = input('Assignment ID: ')

    base_url = 'https://{}.codegra.de'.format(subdomain)

    r = handle_response(requests.post(
        base_url + '/api/v1/login',
        json = { 'username': username, 'password': password },
    ))

    ses = CGSession(base_url, r['access_token'])
    
    users = handle_response(
        ses.get('/api/v1/courses/{}/users/'.format(course_id)),
    )
    
    webhook_data = [
        handle_response(
            ses.post(
                '/api/v1/assignments/{}/webhook_settings?webhook_type=git&author={}'.format(
                    assig_id,
                    user['User']['username'],
                ),
            ),
        ) for user in users
    ]

    return [
        {
            'id': user['User']['id'],
            'username': user['User']['username'],
            'fullname': user['User']['name'],
            'webhook_url': 'https://{}.codegra.de/api/v1/webhooks/{}?branch={}'.format(
                subdomain,
                webhook['id'],
                webhook['default_branch'],
            ),
            'secret': webhook['secret'],
            'deploy_key': webhook['public_key'],
        }
        for user, webhook in zip(users, webhook_data)
    ]


def load_user_data(filename='roster.csv'):
    with open(filename) as user_data:
        reader = csv.DictReader(user_data)
        try:
            data = [ line for line in reader]
        except csv.Error as e:
            sys.exit('file {}, line {}: {}'.format(filename, reader.line_num, e))
    return data


def sync(access, organization, roster, assignment):
    print('Connecting to the organization',organization['github-name'],'...', end=' ', flush=True)
    g = Github(access['github']['token'])
    org = g.get_organization(organization['github-name'])
    print('done')
    print('Loading the roster ...', end=' ', flush=True)
    students = load_user_data(roster)
    sids = [ s['codegrade-user'] for s in students ]
    print('done')
    print('Retrieving CodeGrade data ...', end=' ', flush=True)
    whdata = get_webhook_data_per_user(
        subdomain=access['codegrade']['subdomain'],
        username=access['codegrade']['username'],
        password=access['codegrade']['password'],
        course_id=organization['codegrade-id'],
        assig_id=assignment['codegrade-id']
    )
    print('done\n')
    no_users = 0
    no_errors = 0
    for user in whdata:
        if user['username'] in sids:
            student = next(s for s in students if s['codegrade-user'] == user['username'])
            print('Processing', assignment['github-name'] + '-' + student['github-user'],'...')
            try:
                repo = org.get_repo(assignment['github-name'] + '-' + student['github-user'])
                if 'codegrade-key' not in [ key.title for key in repo.get_keys() ]:
                    print('>','Adding deploy key for', user['fullname'])
                    repo.create_key(title='codegrade-key', key=user['deploy_key'])
                else:
                    print('>','Deploy key found for', user['fullname'])
                if user['webhook_url'] not in [ hook.config['url'] for hook in repo.get_hooks() ]:
                    print('>','Adding webhook for', user['fullname'])
                    repo.create_hook(
                        'web',
                        config={
                            'url': user['webhook_url'],
                            'content_type': 'json',
                            'secret': user['secret']
                        },
                        events=['push'],
                        active=True
                    )
                else:
                    print('>','Webhook found for', user['fullname'])
                no_users += 1
            except:
                e = sys.exc_info()[0]
                print('>','Error:', e)
                no_errors += 1
    print('\nProcessed',no_users,'student(s);',no_errors,'error(s).')


def main():
    sync(
        access={
            'codegrade': {
                'subdomain': 'wur',
                'username': '',
                'password': '',
            },
            'github': {
                'token': ''
            }
        },
        organization={
            'codegrade-id': 14,
            'github-name': 'geoscripting-2021'
        },
        roster='github_webhooks.csv',
        assignment={
            'codegrade-id': 32,
            'github-name': 'Exercise_1_Starter'
        }
    )

    
if __name__ == '__main__':
    main()
