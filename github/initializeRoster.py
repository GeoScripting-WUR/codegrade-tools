import pprint

import sys, ast
import csv
import json
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


def get_users(subdomain, username, password, course_id):
    base_url = 'https://{}.codegra.de'.format(subdomain)

    r = handle_response(requests.post(
        base_url + '/api/v1/login',
        json = { 'username': username, 'password': password },
    ))

    ses = CGSession(base_url, r['access_token'])
    
    users = handle_response(
        ses.get('/api/v1/courses/{}/users/'.format(course_id)),
    )

    return users


def init_roster(access, organization, roster):
    print('Retrieving CodeGrade data ...', end=' ', flush=True)
    users = get_users(
        subdomain=access['codegrade']['subdomain'],
        username=access['codegrade']['username'],
        password=access['codegrade']['password'],
        course_id=organization['codegrade-id']
    )
    print('done')
    print('Writing',roster,'...', end=' ', flush=True)
    with open(roster, mode='w', newline='') as out:
        w = csv.writer(out)
        w.writerow(['name','email','codegrade-user','github-user'])
        for u in users:
            w.writerow([u['User']['name'], '?', u['User']['username'], '?'])
    print('done')


def main():
    init_roster(
        access={
            'codegrade': {
                'subdomain': 'wur',
                'username': '',
                'password': ''
            }
        },
        organization={
            'codegrade-id': 14,
            'github-name': 'geoscripting-2021'
        },
        roster='roster.csv'
    )
    
    
if __name__ == '__main__':
    main()
