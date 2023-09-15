# 1) Script for generating a roster table that maps CodeGrade and GitLab accounts.
# This is a helper script, you can also create this yourself.

import codegrade
import gitlab
import csv
from unidecode import unidecode

def init_roster(gitlab_host,
                codegrade_tenant, codegrade_host, codegrade_course, codegrade_nonstudent_role = "Teacher",
                secrets_file = "secrets.txt", output_file = "usernames.csv"):
    
    # Read secrets. First line is codegrade user, second is codegrade password, third is GitLab access token
    with open(secrets_file, "r") as secretfile:
        secrets = secretfile.read().splitlines()
    
    students = get_cg_students(secrets, codegrade_tenant, codegrade_host, codegrade_course, codegrade_nonstudent_role)
    students = add_gl_students(students, secrets, gitlab_host) # Try to automatically match students to GitLab users via username/name
    write_roster(students, output_file)

def get_cg_students(secrets, codegrade_tenant, codegrade_host, codegrade_course, codegrade_nonstudent_role):
    # Log into Codegrade
    with codegrade.login(
        username=secrets[0],
        password=secrets[1],
        tenant=codegrade_tenant,
        host=codegrade_host
    ) as client:
        pass

    # Get users
    cg_users = client.course.get_all_users(course_id=codegrade_course)
    cg_students = [[user.user.name, user.user.username] for user in cg_users if user.course_role.name != codegrade_nonstudent_role]
    return cg_students


def add_gl_students(cg_students, secrets, gitlab_host):
    # Log into GitLab
    gl = gitlab.Gitlab(gitlab_host, private_token=secrets[2])

    # Get our group that has the students
    #groups = gl.groups.list(search=gitlab_student_group_name, order_by="similarity")
    #student_group = groups[0]
    #print("Using group " + student_group.web_url)

    # Search for matching students
    # First search by username, then search by name
    for student in cg_students:
        gl_user = gl.users.list(search=unidecode(student[1]))
        if len(gl_user) > 0:
            student.extend([gl_user[0].name, gl_user[0].username])
        else:
            gl_user = gl.users.list(search=unidecode(student[0]))
            if len(gl_user) > 0:
                student.extend([gl_user[0].name, gl_user[0].username])
            else:
                student.extend(["", ""])
                print(f'WARNING! {student[0]} not found. Check what is going on!')
    return cg_students

def write_roster(cg_students, output_file):
    # Write roster to file
    with open(output_file, mode='w', newline='') as out:
        w = csv.writer(out)
        w.writerow(['cg_name','cg_user','gl_name','gl_user'])
        for student in cg_students:
            w.writerow(student)
    print("File " + output_file + " written successfully! Please check the file and adjust as needed.")

# Get all students in group
#gl_students = student_group.members.list()
#for student in gl_students:
#    print(student.username)

def main():
    init_roster(
        # Global variables
        secrets_file = "secrets.txt",
        codegrade_tenant = "Wageningen University",
        codegrade_host = "https://wur.codegra.de",
        codegrade_course = 5027,
        codegrade_nonstudent_role = "Teacher",
        gitlab_host = 'https://git.wur.nl',
        output_file = "usernames.csv"
    )
    
if __name__ == '__main__':
    main()
