import gitlab
import os

with open("../gitlab/secrets.txt", "r") as secretfile:
    secrets = secretfile.read().splitlines()

token = secrets[2]
gl = gitlab.Gitlab(url='https://git.wur.nl/', private_token=token)
gl.auth()

id_old = "geoscripting-2023-september"
id_new = "geoscripting-2024"

def update_namespace(old_namespace):
    return old_namespace.replace(id_old, id_new)

# Main Group has subgroups staff and student
for group in gl.groups.get(id_old).subgroups.list(iterator=True):

    # Staff and students have groups excercises, assignments etc
    for subgroup in gl.groups.get(group.id).subgroups.list(iterator=True):

        # Each assignment has projects (=repos). Student group projects from last year
        # and Assignment/Solutions. These last onces are of interest.
        for project in gl.groups.get(subgroup.id).projects.list(iterator=True):

            # relevant assignments etc have been forked by each student team.
            if project.forks_count > 30 or " solution" in project.name.lower():
                print(f"fork: {project.name} ?")
                ns = update_namespace(project.namespace["full_path"])
                try:
                    fork = gl.projects.get(project.id).forks.create({"namespace": ns})
                except gitlab.exceptions.GitlabCreateError as E:
                    print(E)

                # Delete fork relation?
                # gl.projects.get(project.id).delete_fork_relation()
