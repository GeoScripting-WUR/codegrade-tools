import csv, sys
from github import Github


def load_user_data(filename='roster.csv'):
    with open(filename) as user_data:
        reader = csv.DictReader(user_data)
        try:
            data = [ line for line in reader]
        except csv.Error as e:
            sys.exit('file {}, line {}: {}'.format(filename, reader.line_num, e))
    return data


def invite(token, organization, roster):
    print('Connecting to the organization',organization,'...', end=' ', flush=True)
    g = Github(token)
    org = g.get_organization(organization)
    print('done')
    print('Checking existing members ...', end=' ', flush=True)
    members = [ m.login for m in org.get_members() ]
    print('done')
    print('Loading the roster ...', end=' ', flush=True)
    students = load_user_data(roster)
    print('done\n')
    no_members = 0
    no_invites = 0
    no_errors = 0
    for s in students:
        print('Processing',s['name'],'({})'.format(s['email']),'...')
        if s['github-user'] in members:
            no_members += 1
            print('> Already a member')
        else:
            print('> Sending an invitation to',s['email'])
            try:
                # org.invite_user(email=s['email'])
                no_invites += 1
            except:
                e = sys.exc_info()[0]
                print('>','Error:', e)
                no_errors += 1
    print('\nProcessed',len(students),'student(s);',
          no_members,'member(s) found;',
          no_invites,'invitation(s) sent;',
          no_errors,'error(s).')

    
def main():
    invite(
        token='...',
        organization='...',
        roster='roster.csv'
    )
    

if __name__ == '__main__':
    main()
