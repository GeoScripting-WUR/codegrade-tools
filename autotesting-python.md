_last update: 22-07-2025_

# Implement python AutoTests in CodeGrade

## Why are there 2 autotest descriptions? 
This text is largely similar to the [R AutoTests documentation](AUTOTESTS.md), but adapted for Python specifically. The main difference will be calling the test in Python instead of R. It will also show the helper functions that are defined so the python tests will run more cleanly. 

AutoTests are used to automatically grade assignments that students submit to CodeGrade. Each task can have a separate test that is linked to the specific rubric in the AutoTest configuration so that partial grading is possible. This documentation gives a brief overview on the current configuration of AutoTests for exercises and assignments of the Geoscripting course at Wageningen University. 

In each exercise and assignment there is a separate `test` folder that contains the test scripts, which will be used by CodeGrade to test the student submissions. 

## Helpful links 

- [CodeGrade automatic grading in AutoTest v2](https://help.codegrade.com/faq/automatic-grading-questions/autotest-v2)
- [CodeGrade Roadmap / feature requests](https://www.codegrade.com/roadmap)

## Create AutoTest configuration

### Getting started 

The general idea of AutoTests is to run test scripts that execute the student submissions and check the results. If scripts fail or the results do not match the solutions only partial or no points will be given in the rubric. 


### AutoTest - Setup in codegrade 

1. CodeGrade configurations are accessible via the exercises on Brightspace, which will link to the CodeGrade page. The AutoTest can be implemented or found via the `AutoTest` tab: `Brightspace Exercise 7 > CodeGrade Exercise 07 > AutoTest `.
1. Create new AutoTest v2 from scratch or copy existing configuration from previous assignments.
1. Drag & drop the different cells into the window to build the test. Keep it simple and use `Upload Files`, `Allow Internet`, `Connect Rubric` and `Script`. The actual tests are bash, R or Python scripts that can be run as bash commands via `Script`.

CodeGrade will build a new testing Ubuntu environment every time the AutoTest `Setup` configuration changes. This means that CodeGrade checks if the code in each cell has changed since the last snapshot and runs the code again if necessary. Once the AutoTest configuration including the setup works, the snapshot is used when students submit assignments. 

Use `Upload Files` to upload configuration files and `Script` to set up the environment on the Ubuntu VM. 

1. Use `Upload Files` to upload `setup.zip` that contains a `.bash_profile`, which sets the two environment variables `GITLAB_USER_NAME` and `GITLAB_USER_PATH`. These are needed for [cloning repositories via https using personal access tokens](https://docs.gitlab.com/ee/user/profile/personal_access_tokens.html#clone-repository-using-personal-access-token) in the next step. The cloned repository contains the assignment solution and all tests within a `test` folder.
2. 
```
export GITLAB_USER_NAME=geoscripting-<year>-september
export GITLAB_USER_PAT=<personal_access_token>
```

1. Install git 
2. Get the requirements for the relevant language. These are cloned from gitlab.
3. Move the relevant files from the temporary location to the `$UPLOADED_FILES` directory.
4. Run the install_requirements script to install the requirements. 


```bash
# install GDAL
sudo apt update && sudo apt install -y git
# set up git and clone solution repo with tests

YEAR=`date +%Y`
NR='08'
git clone https://$GITLAB_USER_NAME:$GITLAB_USER_PAT@git.wur.nl/geoscripting-$YEAR/staff/exercise-$NR/exercise-$NR-solution.git $UPLOADED_FILES/tmp
mv $UPLOADED_FILES/tmp/environment.yml $UPLOADED_FILES/environment.yaml
mv $UPLOADED_FILES/tmp/test $UPLOADED_FILES/ && rm -rf $UPLOADED_FILES/tmp

# install requirements
chmod +x $UPLOADED_FILES/test/install_requirements.sh
$UPLOADED_FILES/test/install_requirements.sh

echo "Done!!!" 
```

### AutoTest - Tests 

This is where the actual tests are being implemented. This section is the main difference with how tests are run in R. 

The steps are:

1. Drag & drop a `Rubric` cell into the window so that points are being assigned to a specific rubric. 
1. Make sure to `Allow Internet` if necessary. This could also be outside the `Rubric` cell or in any other order.
1. Create a bash script with the code that will run the tests that corresponds to the rubric item. 

The next section will explain this in more detail. 

Some tests are the same for all exercises, for example checking the git useage. This is done using a bash script. this can be called using: 

```bash
# use bash test script 
bash $UPLOADED_FILES/test/git_use.sh
``` 


# How to set up tests for geoscripting?!

In geoscripting we make use of codegrade to do some testing before we even start grading. 
In `./test_exc08.py` you will find an example of how to set up tests for [exercise 8]()https://git.wur.nl/geoscripting-2025/staff/exercise-8/exercise-8-solution. 
We will go through the code in this markdown for your understanding. Since it is copied it might contain some duplicate text... Sorry :) 

## Argparse
In the following code we set up the test so it can be easily called from the command line in codegrade. We need to do this because in codegrade we need to specify the correct path to the student answer directory,  we need to make sure the code that is run is not the answer but the actual answer of the student.

```python
# append student path
import sys
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--student_path', type=str, default='/home/codegrade/student',
                   help='Path to student answer directory')
parser.add_argument('--test', type=int, choices=[1, 2], help='Select test to run (1: geolocator, 2: calc_distances)')
args = parser.parse_args()

sys.path.append(args.student_path)
```
 For this we use Argparse. Argparse is a useful package to set up command line arguments. In this example argparse makes the python file to be called with 2 command line arguments, `--student_path` and `--test`. This makes it easy to configure the test as we want. After setting it up like this we can call the test file like this:

```bash
python test_exc08.py --student_path /home/codegrade/student --test 1
```
The first test will be run on the answer saved in the path `/home/codegrade/student`, the path where the code will be stored in codegrade. Selecting the correct test is important, because we can then select only part of the tests to be run, specifically the test that corresponds to the rubric item.

For testing locally while developing you might want to create a local folder with some answers in it. By changing the answers to something wrong you can see if the test catches it. 

## Try function
The try function as defined below is a simple way to run a function and catch any assertion errors that might occur: 
```python
def try_function(fun):
    try:
        fun()
    except AssertionError as E:
        print(E)
        sys.exit(1)
```
It does several things. We don't want to show the student an ugly error stack trace, but rather we want to show a nice error message 
that we can define ourselves. In this way we also make sure we don't give away the answer, and we might in the future want to use this
to give some hints for specific mistakes. 

## Actual testing 
The following code now imports the students answers: 
```python
# import student module
import distanceCalculator
```

And now finally the actual testing. Below are 2 tests that test some functionality.  

```python
def test_geolocator():
    # g = Nominatim(user_agent='geocoder')
    assert distanceCalculator.geolocator(cityname = "Wageningen") == (51.9685817, 5.668298061827958), "The location Wageningen was not geocoded correctly, there is an issue somewhere."

def test_calc_distances():
    # Round to nearest 10 km
    distance = round(distanceCalculator.calc_distances(cities = ['Wageningen','Brussels', 'London']), -1)
    assert  distance == 7102, "The distance from Wageningen to Brussels to London is not correct there is an issue somewhere."
```
The first function tests if the geolocator function returns the correct coordinates for Wageningen. Note that we 
define the coordinate manually instead of running the answer. We can do this because we know Wageningen will not move soon. 

The second function tests if the distance calculation is correct for the route Wageningen - Brussels - London. The distance is rounded to the nearest 10 km,
different geocoding services might return slightly different distances. 

Finally we run the tests, we wrap the functions in the `try_function` function so we can catch any assertion errors and print a nice error message as explained above: 

```python
if args.test is None or args.test == 1:
    try_function(test_geolocator)
if args.test is None or args.test == 2:
    try_function(test_calc_distances)
```
 
I hope all is clear! if not, reach out! 



_Notes_:
- CodeGrade will not fetch updates from a Git repo if the code within a cell has not changed since the previous snapshot. Simply add an `echo` command to force CodeGrade to clone an updated repository, since this will trigger to re-run the cell. 
- Commands that require `sudo` privileges only work in cells of the `Setup` tab.
- It is possible to upload e.g. wrong test submission to check if the tests work fine. Upload a `.zip` file containing scripts and subfolders in: `General > Upload submission > Test sumission > <upload_zip_file>`. Note that, the results of different test submissions will be displayed below each other in the same snapshot. 
- Student or test submissions will be uploaded into the directory `/home/codegrade/student`
- The final directory should look something like this: 

```
/home/codegrade/
|-- fixtures                          # $UPLOADED_FILES
|   |-- test                          # test folder from solution
|       |-- git_use.sh                # test - git use
|       |-- helper.R                  # test - helper functions
|       |-- install_requirements.R    # R requirements
|       |-- install_requirements.sh   # general requirements (e.g. GDAL)
|       |-- test_exc08.py             # tests
|-- student                           # student or test submission
    |-- output
    |   |-- output_image.png
    |--distanceCalculator
    |   |-- __init_.py               # This is where the students python answers  are
    |-- LICENSE
    |-- README.md
```

1. To check the final AutoTest configuration, just click on `Build Snapshot`. This will set up the Ubuntu VM as configured with `Setup` and run all tests specified in `Tests`. Remember that the `Setup` will be skipped if there are no changes to a previous snapshot. Snapshots can be found and inspected in the `Snapshots` tab.

### AutoTest - Snapshots

This is where all compiled AutoTest configurations can be found. Each snapshot shows the configuration and the output of tests. If everything worked fine and all tests passed, the snapshot may be published to the students by clicking on a specific snapshot and confirming `Publish to students`. Students will now be able to see test results when submitting assignments. 



