import pprint

import sys
import csv
import getpass
from urllib.parse import urljoin
from github import Github
# Requires a version with template cloning support:
# https://github.com/PyGithub/PyGithub/pull/1395

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
        reponame = assignment['github-name'] + '-' + group['group_name']
        group_members = group["github_ids"].split().append(organization['github-name']+"/staff")
        print('Processing', reponame,'...')
        try:
            if reponame not in [ repo.name for repo in org.get_repos() ]:
                print(">", "Repository", reponame, "does not exist yet, cloning...")
                template = org.get_repo(assignment['github-name'])
                org.create_repo_from_template(reponame, template, private=True)
                print(">", "Repository", reponame, "created successfully")
            
            repo = org.get_repo(reponame)
            if 'codegrade-key' not in [ key.title for key in repo.get_keys() ]:
                print('>','Adding deploy key for', group['group_name'])
                repo.create_key(title='codegrade-key', key=group['public_key'])
            else:
                print('>','Deploy key found for', group['group_name'])
            if group['payload_url'] not in [ hook.config['url'] for hook in repo.get_hooks() ]:
                print('>','Adding webhook for', group['group_name'])
                repo.create_hook(
                    'web',
                    config={
                        'url': group['payload_url'],
                        'content_type': 'json',
                        'secret': group['secret']
                    },
                    events=['push'],
                    active=True
                )
            else:
                print('>','Webhook found for', group['group_name'])
            for member in group_members:
                if repo.has_in_collaborators(member):
                    print('>', 'Collaborator', member, 'already present')
                else:
                    repo.add_to_collaborators(member, "maintain")
                    print('>', 'Collaborator', member, 'added to the repository')
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
