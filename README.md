# Autograder for Project-2 Part 1

Make sure that you use the provided autograder and follow the instructions below to test your project submission. **Failure to do so may cause you to lose all the project points and there will be absolutely no second chance.**

- Download the zip file you submitted from Canvas.
- Download the autograder from GitHub: `https://github.com/CSE546-Cloud-Computing/CSE546-SPRING-2026.git`
  - In order to clone the GitHub repository follow the below steps:
  - `git clone https://github.com/CSE546-Cloud-Computing/CSE546-SPRING-2026.git`
  - `cd CSE546-SPRING-2026/`
  - `git checkout project-2-part-1`
- Create a directory `submissions` in the CSE546-SPRING-2026 directory and move your zip file to the submissions directory.

## Prepare to run the autograder
- Install Python: `sudo apt install python3 python3-pip`
- Install dependencies: `pip3 install boto3`
- Populate the `class_roster.csv`
  - If you are a student; replace the given template only with your details.
  - If you are a grader; use the class roster for the entire class
- **Ensure all 10 EC2 worker instances are in the `stopped` state** before running the autograder.
- **Ensure both S3 buckets are empty** before running the autograder.
- **Ensure your Lambda function is deployed and active.**

## Run the autograder
- Run the autograder: `python3 autograder.py`
- The autograder will look for submissions for each entry present in the `class_roster.csv`
- For each submission the autograder will
  - Validate if the zip file adheres to the submission guidelines as mentioned in the project document. Autograder expects case sensitive folder and file names.
    - If Yes; proceed to next step
    - If No; allocate 0 grade points and proceed to the next submission
  - The autograder extracts the `credentials.txt` from the submission and parses the entries.
  - Use the Grader IAM credentials to test the project as per the grading rubrics and allocate grade points.
  - The autograder will dump stdout and stderr in a log file named `autograder.log`

## Sample Output

```
+++++++++++++++++++++++++++++++ CSE546 Autograder  +++++++++++++++++++++++++++++++
- 1) Extract the credentials from the credentials.txt
- 2) Execute the test cases as per the Grading Rubrics
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
++++++++++++++++++++++++++++ Autograder Configurations ++++++++++++++++++++++++++++
Project Path: /home/ubuntu/CSE546-SPRING-2026
Grade Project: Project-2-Part-1
Class Roster: class_roster.csv
Zip folder path: /home/ubuntu/CSE546-SPRING-2026/submissions
Autograder Results: Project-2-Part-1-grades.csv
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
The file Project-2-Part-1-grades.csv does NOT exist.
++++++++++++++++++ Grading for Doe John ASUID: 1234567890 +++++++++++++++++++++
Extracted /home/ubuntu/CSE546-SPRING-2026/submissions/Project2-1234567890.zip to extracted
File: extracted/credentials/credentials.txt has values ('XXXXXXXXXXXXXXXXXXXXXXXXX', 'XXXXXXXXXXXXXXXXXXXXXXXXX')
Sanity Test Passed: credentials.txt, worker/worker.py, aggregator/aggregator.py found.
Credentials parsing complete.
------------------------------------------------------------
IAM ACCESS KEY ID: XXXXXXXXXXXXXXXXXXXXXXXXX
IAM SECRET ACCESS KEY: XXXXXXXXXXXXXXXXXXXXXXXXX
------------------------------------------------------------
Following policies are attached with IAM user:cse546-AutoGrader: ['AmazonEC2FullAccess', 'IAMReadOnlyAccess', 'AmazonS3FullAccess', 'AWSLambda_ReadOnlyAccess']
[IAM-log] IAMReadOnlyAccess policy attached with grading IAM
[IAM-log] AmazonEC2FullAccess policy attached with grading IAM
[IAM-log] AmazonS3FullAccess policy attached with grading IAM
[IAM-log] Lambda ReadOnlyAccess policy attached with grading IAM
-------------- CSE546 Cloud Computing Grading Console -----------
IAM ACCESS KEY ID: XXXXXXXXXXXXXXXXXXXXXXXXX
ASUID: 1234567890
------------------------------------------------------------
----------------- Checking The Initial State ----------------

  === TC-1: Validate Initial State ===

  TC-1a: S3 Buckets
  --------------------------------------------------
    local-bucket (1234567890-local-bucket): EXISTS, empty
    global-bucket (1234567890-global-bucket): EXISTS, empty

  TC-1b: EC2 Instances
  --------------------------------------------------
    Found 10 1234567890-fl-worker instances
    1234567890-fl-worker-0 (i-0abc123def456) — stopped (t3.micro)
    1234567890-fl-worker-1 (i-0abc123def457) — stopped (t3.micro)
    1234567890-fl-worker-2 (i-0abc123def458) — stopped (t3.micro)
    1234567890-fl-worker-3 (i-0abc123def459) — stopped (t3.micro)
    1234567890-fl-worker-4 (i-0abc123def460) — stopped (t3.micro)
    1234567890-fl-worker-5 (i-0abc123def461) — stopped (t3.micro)
    1234567890-fl-worker-6 (i-0abc123def462) — stopped (t3.micro)
    1234567890-fl-worker-7 (i-0abc123def463) — stopped (t3.micro)
    1234567890-fl-worker-8 (i-0abc123def464) — stopped (t3.micro)
    1234567890-fl-worker-9 (i-0abc123def465) — stopped (t3.micro)

  TC-1c: Lambda Function
  --------------------------------------------------
    Lambda 'fl-aggregator': ARN=arn:aws:lambda:us-west-2:123456789012:function:fl-aggregator
    State: Active
    Memory: 2048 MB
    Env: NUM_CLIENTS=10, TOTAL_ROUNDS=5

  TC-1 Deductions: -0
  TC-1 Total Deductions: -0
----------------- Executing FL Training ----------------

  === TC-2: FL Execution ===

  Step 1 — Verify local data files
  --------------------------------------------------
    labels.csv: 195.3 KB
    test.tar.gz: 249.3 KB
    initial_model.npz: 243.5 KB

  Step 2 — Clean S3 buckets
  --------------------------------------------------
    1234567890-global-bucket:metrics/ — already clean
    1234567890-global-bucket:models/ — already clean
    1234567890-local-bucket:updates/ — already clean

  Step 3 — Upload data files
  --------------------------------------------------
    Uploaded 1234567890-global-bucket:labels.csv
    Uploaded 1234567890-global-bucket:archives/test.tar.gz
    Uploaded 1234567890-global-bucket:models/global_model_round_0.npz

  Step 4 — Start client instances
  --------------------------------------------------
    1234567890-fl-worker-0 (i-0abc123def456)
    1234567890-fl-worker-1 (i-0abc123def457)
    ...
    1234567890-fl-worker-9 (i-0abc123def465)
    Starting 10 instances ...
    All instances running.

  Step 5 — Monitor training (5 rounds, timeout 100s)
  --------------------------------------------------
    Round 0: accuracy=0.8986, loss=0.3213 (20.5s)
    Round 1: accuracy=0.9568, loss=0.1277 (25.6s)
    Round 2: accuracy=0.9679, loss=0.1016 (30.7s)
    Round 3: accuracy=0.9729, loss=0.0866 (35.8s)
    Round 4: accuracy=0.9769, loss=0.0795 (35.9s)
    Training complete in 35.9s

  Step 6 — Stop instances
  --------------------------------------------------
    Stopping 10 instances ...
    All instances stopped.
----------------- Checking Training Artifacts ----------------

  === TC-3: Validate FL Artifacts ===

  Round 0:
  --------------------------------------------------
    Global model (round 1): FOUND
    Local models: 10/10
    Metrics (round_0.json): FOUND
    All artifacts present

  Round 1:
  --------------------------------------------------
    Global model (round 2): FOUND
    Local models: 10/10
    Metrics (round_1.json): FOUND
    All artifacts present

  Round 2:
  --------------------------------------------------
    Global model (round 3): FOUND
    Local models: 10/10
    Metrics (round_2.json): FOUND
    All artifacts present

  Round 3:
  --------------------------------------------------
    Global model (round 4): FOUND
    Local models: 10/10
    Metrics (round_3.json): FOUND
    All artifacts present

  Round 4:
  --------------------------------------------------
    Global model (round 5): FOUND
    Local models: 10/10
    Metrics (round_4.json): FOUND
    All artifacts present

  TC-3 Deductions: -0
----------------- Checking Model Accuracy ----------------

  === TC-4: Validate Model Accuracy ===

  TC-4a: Final Accuracy
  --------------------------------------------------
    Final Accuracy: 0.9769
    Final Loss:     0.0795
    Score: 50/50

  TC-4b: Accuracy Progression
  --------------------------------------------------
    Round-by-round accuracy:
      Round 0: acc=0.8986, loss=0.3213
      Round 1: acc=0.9568, loss=0.1277
      Round 2: acc=0.9679, loss=0.1016
      Round 3: acc=0.9729, loss=0.0866
      Round 4: acc=0.9769, loss=0.0795

  TC-4 Score: 50/50, Deductions: -0
----------------- Checking Training Speed ----------------

  === TC-5: Validate Training Speed ===
  --------------------------------------------------
    Training time: 35.9s
    Score: 50/50
    Tier: < 50s

  ==================================================
  SCORE BREAKDOWN:
    Accuracy:   50/50
    Speed:      50/50
    Deductions: -0
    ---
    TOTAL: 100/100
Total Grade Points: 100
Removed extracted folder: extracted
Total time taken to grade for Doe John ASUID: 1234567890: 137.59 seconds
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
Grading complete for Project-2-Part-1. Check the Project-2-Part-1-grades.csv file.
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
```
