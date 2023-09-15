# GitHub/GitLab integration for CodeGrade

This repository has scripts that automatically precreate GitHub/GitLab repositories for students/groups with the keys and hooks that CodeGrade requires.

## Required software

* Python 3
* GitLab: python-gitlab
* GitHub: PyGitHub [with support for cloning template repositories](https://github.com/PyGithub/PyGithub/pull/1395):

You can create an environment using the [`environment.yml`]() using:
```bash
mamba env create --file environments.yml
```
This will create an environment containing all python packages available from conda. You will need to install codegrade using pip:

```bash
python3 -m pip install codegrade
```

```bash
python -m pip install git+https://github.com/isouza-daitan/PyGithub@create-from-template
```

## Setup

We need to link CodeGrade users to GitHub/GitLab users, for that create a file called `github_ids.csv` (GitHub) / `usernames.csv` (GitLab) that has columns `CGUsername`, `GHUsername` for CodeGrade and GitHub respectively, or `cg_name`, `cg_user`, `gl_name`, `gl_user` for CodeGrade and GitLab (the `name` columns are not used but useful for readability).
The CodeGrade username is generally the institution email address, but you can find out by looking at your user settings (profile).
Admins are likely to have some other username.
For GitLab, this "roster" file you can create automatically using the script `1_get_usernames.py` (see below).

For any of the scripts to run and do anything useful, we need login details to both CodeGrade and GitHub / GitLab.
For that, create a `secrets.txt` file, in which put three lines: your CodeGrade username, your CodeGrade password (reset password on CodeGrade if you don't have one set) and GitHub/GitLab developer access token (generate one via your settings in GitHub/GitLab), in that order.
This file should be put into the respective directory (GitLab/GitHub).

In each script you have several parameters that you need to tweak, which are available in the `main()` function. Check it before running the scripts.
After you have your roster CSV, run `2_get_webhooks.py` to generate a `webhooks.csv` file that has webhook information from CodeGrade.
`'subdomain'` is your CodeGrade subdomain (subdomain.codegra.de), `'codegrade-id'` is your course ID from the URL of the course/assignment, `'assignment-id'` is the assignment number from the URL of the assignment.
`individual` determines whether the assignment is individual or group, i.e. whether to create group repositories and add all students as collaborators, or individual student repositories only.
After running the script, verify that the resulting `webhooks.csv` looks correct. Remove any rows for persons/groups you don't want to precreate a repository for.

Lastly, edit `installKeysAndHooks.py`.
Edit the `'subdomain'` and the two fields of `'codegrade-id'` to match the ones above.
Edit `'github-name'` for both the GitHub organization name and the starter repository name that will be cloned.
Finally, `student_readable` determines whether *other* students will also be able to see other students' repositories.
You generally don't want that before the submission deadline.
After the submission you might want to set that to `True` so that the students can do peer review (unless you are using CodeGrade's peer review capabilities).

Next, go to the repository to clone on GitHub, go to settings, and set the repository as a template repository.
That allows it to be cloned.

## Cloning all repositories

Running the `installKeysAndHooks.py` script creates the requested repositories with the requested permissions.
Do that when you actually want to start the assignment: students will see the repository with assignment instructions.
Rerunning the script will synchronise any repositories that are out of sync, so it's safe to rerun it several times.
You need to rerun the script if you change the `student_readable` flag to apply the changes.
