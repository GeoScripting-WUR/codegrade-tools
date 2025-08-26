_last update: 08-10-2024_

# Implement AutoTests in CodeGrade

AutoTests are used to automatically grade assignments that students submit to CodeGrade. Each task can have a separate test that is linked to the specific rubric in the AutoTest configuration so that partial grading is possible. This documentation gives a brief overview on the current configuration of AutoTests for exercises and assignments of the Geoscripting course at Wageningen University. 

A separate `test` folder in each of the GitLab (solution) repositories of the assignments contains the test scripts, which will be used by CodeGrade to test the student submissions. 

## Helpful links 

- [CodeGrade automatic grading in AutoTest v2](https://help.codegrade.com/faq/automatic-grading-questions/autotest-v2)
- [CodeGrade Roadmap / feature requests](https://www.codegrade.com/roadmap)
- [Fast install of CRAN R packages as Ubuntu Binaries using R2U](https://eddelbuettel.github.io/r2u/)

## Create AutoTest configuration

### Getting started 

The general idea of AutoTests is to run test scripts that execute the student submissions and check the results. If scripts fail or the results do not match the solutions only partial or no points will be given in the rubric. 

1. CodeGrade configurations are accessible via the exercises on Brightspace, which will link to the CodeGrade page. The AutoTest can be implemented or found via the `AutoTest` tab: `Brightspace Exercise 7 > CodeGrade Exercise 07 > AutoTest `.
1. Create new AutoTest v2 from scratch or copy existing configuration from previous assignments.
1. Drag & drop the different cells into the window to build the test. Keep it simple and use `Allow Internet`, `Connect Rubric` and `Script`. The actual tests are bash, R or Python scripts that can be run as bash commands via `Script`. 

### AutoTest - Setup

CodeGrade will build a new testing Ubuntu environment every time the AutoTest `Setup` configuration changes. This means that CodeGrade checks if the code in each cell has changed since the last snapshot and runs the code again if necessary. Once the AutoTest configuration including the setup works, the snapshot is used when students submit assignments. 

Prior to the `Setup` in CodeGrade, certain files required for configuring the VM environment must be created and stored in the exercise's GitLab repository. 


#### R

1. Create `.sh` and `.R` install requirements files that will be used in the next step to set up the CodeGrade Ubuntu environment for R. These files should be uploaded into the `test` folder of each solution repository.

`install_requirements.R`: 
```R
# user R library
UserLib = Sys.getenv("R_LIBS_USER")
dir.create(UserLib, recursive=TRUE)

# list packages to install
pkgs = c('testthat', 'terra', 'sf', 'ranger')

# install packages
install.packages(pkgs, lib=UserLib, repos='https://cloud.r-project.org')
```

`install_requirements.sh`: 

```bash
# set up r2u for focal
# docs: https://eddelbuettel.github.io/r2u/
curl -s https://raw.githubusercontent.com/eddelbuettel/r2u/master/inst/scripts/add_cranapt_focal.sh | sudo bash

# install GDAL
sudo apt install -y gdal-bin python3-gdal
export LC_ALL=C

# install R requirements
Rscript $UPLOADED_FILES/test/install_requirements.R
```

_Important:_ There were major problems installing R packages on the CodeGrade VM, with numerous dependency issues and long setup times of up to half an hour. This could eventually be solved using `r2u` which installs R packages as Ubuntu binaries. Therefore, it is highly advised to stick to the `r2u` setup.

#### Python

1. Create `.sh` install requirements file and `.yaml` environment file containing all necessary python dependencies for the current exercise. These files will be used in the next step to set up the CodeGrade Ubuntu environment for Python. These files should be uploaded into the `test` folder of each solution repository.

`install_requirements.sh`: 
```bash
sudo apt-get update
sudo apt-get install curl

# install micromamba
curl -Ls https://micro.mamba.pm/api/micromamba/linux-64/latest | tar -xvj bin/micromamba

sudo mv bin/micromamba /usr/local/bin/
sudo chmod +x /usr/local/bin/micromamba

eval "$(micromamba shell hook --shell bash)"

# initialize micromamba shell
micromamba shell init -s bash -r ~/micromamba

# create and activate environment 
micromamba env create -f $UPLOADED_FILES/test/environment.yaml -y
micromamba activate environment
```

`environment.yaml`:
```yaml
name: environmnet
channels:
  - conda-forge
dependencies:
  - python=3.12
  - spyder
```

_Important:_ Similarly to R, it is important to think about the compiling time when setting up the Python environment on CodeGrade VM. Therefore, the preferred package manager is micromamba as it is considerably faster than mamba/conda, and the absolute bare minimum of dependencies is recommended.


2. Next, use `Script` to set up the environment on the Ubuntu VM, with setting up the two environment variables: `GITLAB_USER_NAME` and `GITLAB_USER_PAT`. These are needed for [cloning repositories via https using personal access tokens](https://docs.gitlab.com/ee/user/profile/personal_access_tokens.html#clone-repository-using-personal-access-token) in the next step. The cloned repository contains the assignment solution and all tests within a `test` folder.

```
export GITLAB_USER_NAME=geoscripting-<year>
export GITLAB_USER_PAT=<personal_access_token>
```

_Note_: Files are being uploaded into the directory `/home/codegrade/fixtures` that is defined by the CodeGrade environment variable called `$UPLOADED_FILES`. In earlier CodeGrade versions this is the same as `$FIXTURES`. 

3. The next step is to install git and clone solution repository. 
4. Install requirements, defined by `install_requirements.sh`.

CodeGrade `Script` cell: 

```bash
# load setup vars
export GITLAB_USER_NAME=geoscripting-2024
export GITLAB_USER_PAT=example

# set up git and clone solution repo with tests
sudo apt update && sudo apt install -y git
YEAR=`date +%Y`
NR='07'
git clone https://$GITLAB_USER_NAME:$GITLAB_USER_PAT@git.wur.nl/geoscripting-$YEAR/staff/exercise-$NR/exercise-$NR-solution.git $UPLOADED_FILES/tmp
mv $UPLOADED_FILES/tmp/test $UPLOADED_FILES/ && rm -rf $UPLOADED_FILES/tmp

# install requirements
chmod +x $UPLOADED_FILES/test/install_requirements.sh
bash $UPLOADED_FILES/test/install_requirements.sh

# dummy echo command to force CodeGrade to rerun cell
echo "Done." 
```

_Notes_: 

- Unfortunately, there is currently no option to use `ssh` to access the CodeGrade Ubuntu AutoTest VM. A workaround for testing commands is to use a `Script` cell and to build a new snapshot to see if the command works. 
- To speed up debugging and prevent long waiting times new code may be tested in a new `Script` cell. Once everything works fine, the code can be merged into a single cell.
- CodeGrade will not fetch updates from a Git repo if the code within a cell has not changed since the previous snapshot. Simply add an `echo` command to force CodeGrade to clone an updated repository, since this will trigger to re-run the cell. 
- Commands that require `sudo` privileges only work in cells of the `Setup` tab. 

### AutoTest - Tests 

This is where the actual tests are being implemented. To do so just create testing scripts that are being run in a `Script` cell. 

The steps are:

1. Drag & drop a `Rubric` cell into the window so that points are being assigned to a specific rubric. 
1. Make sure to `Allow Internet` if necessary. This could also be outside the `Rubric` cell or in any other order.
1. Place a test script within `Script`. Remember that the base directory of the test scripts is `$UPLOADED_FILES`:

```bash
# use bash test script 
bash $UPLOADED_FILES/test/git_use.sh

# OR

# use a R script 
Rscript $UPLOADED_FILES/test/test_task1.R 

# OR 

# use a Python script
export MAMBA_ROOT_PREFIX='/home/codegrade/micromamba' # all environments and cache of micromamba are created by default under the MAMBA_ROOT_PREFIX environment variable
micromamba run -n environment python  $UPLOADED_FILES/test/test_task1.py # running python test script on the previously written environment
```

_Notes_:

- It is possible to upload e.g. wrong test submission to check if the tests work fine. Upload a `.zip` file containing scripts and subfolders in: `General > Upload submission > Test sumission > <upload_zip_file>`. Note that, the results of different test submissions will be displayed below each other in the same snapshot. 
- Student or test submissions will be uploaded into the directory `/home/codegrade/student`
- The final directory should look something like this: 

For R exercise:
```
/home/codegrade/
|-- fixtures                          # $UPLOADED_FILES
|   |-- test                          # test folder from solution
|       |-- git_use.sh                # test - git use
|       |-- helper.R                  # test - helper functions
|       |-- install_requirements.R    # R requirements
|       |-- install_requirements.sh   # general requirements (e.g. GDAL)
|       |-- task_01.R                 # test - task 1
|       |-- task_02.R
|       |-- task_03.R
|       |-- testRunningOnce.sh
|-- student                          # student or test submission
    |-- output
    |   |-- output_image.png
    |-- LICENSE
    |-- README.md
    |-- main.R
```

For Python exercise:
```
/home/codegrade/
|-- fixtures                          # $UPLOADED_FILES
|   |-- test                          # test folder from solution
|       |-- git_use.sh                # test - git use
|       |-- install_requirements.sh   # install micromamba and python environment
|       |-- environment.yaml          # python environment file
|       |-- task_01.py                # test - task 1
|       |-- task_02.py
|       |-- task_03.py
|       |-- testRunningOnce.sh
|-- student                          # student or test submission
    |-- output
    |   |-- output_image.png
    |-- LICENSE
    |-- README.md
    |-- main.py
```

To check the final AutoTest configuration, just click on `Build Snapshot`. This will set up the Ubuntu VM as configured with `Setup` and run all tests specified in `Tests`. Remember that the `Setup` will be skipped if there are no changes to a previous snapshot. Snapshots can be found and inspected in the `Snapshots` tab.

### AutoTest - Snapshots

This is where all compiled AutoTest configurations can be found. Each snapshot shows the configuration and the output of tests. If everything worked fine and all tests passed, the snapshot may be published to the students by clicking on a specific snapshot and confirming `Publish to students`. Students will now be able to see test results when submitting assignments. 
