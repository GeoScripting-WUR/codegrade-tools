import csv
import gitlab
import codegrade
import re

def load_user_data(filename='webhooks.csv'):
    with open(filename) as user_data:
        reader = csv.DictReader(user_data)
        try:
            data = [ line for line in reader]
        except csv.Error as e:
            sys.exit('file {}, line {}: {}'.format(filename, reader.line_num, e))
    return data


def sync(access, organization, roster, assignment, student_readable=False):
    print('Connecting to the group',organization['gitlab-group'],'...', end=' ', flush=True)
    g = gitlab.Gitlab(access["gitlab"]["host"], private_token=access["gitlab"]["token"])
    g.auth()
    me = g.users.get(g.user.id)
    groups = g.groups.list(search=organization["gitlab-group"], order_by="similarity")
    root_group = groups[0]
    print("Using root group: " + root_group.web_url)
    student_group = g.groups.get(root_group.subgroups.list(search=organization["subgroup-students"], order_by="similarity")[0].id, lazy=True) 
    print("Using student group: " + student_group.web_url)
    staff_group = g.groups.get(root_group.subgroups.list(search=organization["subgroup-staff"], order_by="similarity")[0].id, lazy=True)
    print("Using staff group: " + staff_group.web_url)
    print('done')
    print('Loading the roster ...', end=' ', flush=True)
    group_info = load_user_data(roster)
    print('done')
    no_groups = 0
    no_errors = 0
    for group in group_info:
        groupname = re.sub(r'[^\w\-_]', '_', group['group_name'], flags=re.ASCII)
        reponame = assignment['gitlab-name'] + '-' + groupname
        group_members = group["git_ids"].split()
        print('Processing', reponame,'...')
        try:
            if reponame not in [ repo.path for repo in me.projects.list(all=True) ]:
                print(">", "Repository", reponame, "does not exist yet, cloning...")
                template = None
                for repo in staff_group.projects.list(include_subgroups=True, all=True):
                    if repo.path == assignment["gitlab-name"]:
                        template = g.projects.get(repo.id, lazy=True)
                        break
                if template is None:
                    raise LookupError("Did not find the template to clone, please check the spelling of assignment.gitlab-name!")
                fork = template.forks.create({'name': reponame, 'path': reponame})
                print(">", "Repository", fork.path_with_namespace, "created successfully")
            repo = None
            for proj in me.projects.list(all=True):
                if proj.path == reponame:
                    repo = g.projects.get(proj.id, lazy=True)
                    break
            if repo is None:
                raise LookupError("Did not find the template repository, check whether forking actually worked")
            
            for member in group_members:
                print(">", "Processing collaborators:", member)
                if repo.has_in_collaborators(member):
                    print('>', 'Collaborator', member, 'already present')
                else:
                    print('>', 'Adding collaborator', member)
                    try:
                        repo.add_to_collaborators(member, "maintain")
                        print('>', 'Collaborator', member, 'added to the repository')
                    except:
                        e = sys.exc_info()[0]
                        print('>','Error:', e)
                        no_errors += 1
            if staff_team.has_in_repos(repo):
                print(">", "Staff already owns", reponame)
            else:
                print(">", "Adding staff permission to maintain", reponame)
                staff_team.add_to_repos(repo)
                staff_team.set_repo_permission(repo, "admin")
                print(">", "Staff can now maintain", reponame)
            if student_readable:
                print(">","Checking if students can read the repo")
                if student_team.has_in_repos(repo):
                    print(">", "Students can already see", reponame)
                else:
                    print(">", "Adding students permission to read", reponame)
                    student_team.add_to_repos(repo)
                    print(">", "Students can now read", reponame)
            
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
            no_groups += 1
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
                'host': "https://wur.codegra.de",
                'tenant': "Wageningen University",
                'username': secrets[0],
                'password': secrets[1],
            },
            'gitlab': {
                'host': "https://git.wur.nl",
                #'user': "masil001",
                'token': secrets[2]
            }
        },
        organization={
            'codegrade-id': 33,
            'gitlab-group': 'geoscripting-2022',
            'subgroup-staff': 'Staff',
            'subgroup-students': 'Students'
        },
        roster='webhooks.csv',
        assignment={
            'codegrade-id': 98,
            'gitlab-name': 'Exercise_1_Starter'
        },
        student_readable=False
    )

    
if __name__ == '__main__':
    main()
