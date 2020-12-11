import pprint

import sys
import csv
import getpass
from urllib.parse import urljoin
from github import Github

import requests
import re

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

def load_user_data(filename='github_webhooks.csv'):
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
    group_info = load_user_data(roster)
    print('done')
    no_groups = 0
    no_errors = 0
    for group in group_info:
        groupname = re.sub(r'[^\w.-_]', '_', group['group_name'])
        print('Processing', assignment['github-name'] + '-' + group['group_name'],'...')
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
    print('\nProcessed',no_groups,'group(s);',no_errors,'error(s).')


def main():
    with open("secrets.txt", "r") as secretfile:
        secrets = secretfile.read().splitlines()
    sync(
        access={
            'codegrade': {
                'subdomain': 'wur',
                'username': secrets[0],
                'password': secrets[1],
            },
            'github': {
                'token': secrets[2]
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
