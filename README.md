# Autograder for Project-2 Part 2

Make sure that you use the provided autograder and follow the instructions below to test your project submission. **Failure to do so may cause you to lose all the project points and there will be absolutely no second chance.**

- Download the zip file you submitted from Canvas.
- Download the autograder from GitHub: `https://github.com/CSE546-Cloud-Computing/CSE546-SPRING-2026.git`
  - In order to clone the GitHub repository follow the below steps:
  - `git clone https://github.com/CSE546-Cloud-Computing/CSE546-SPRING-2026.git`
  - `cd CSE546-SPRING-2026/`
  - `git checkout project-2-part-2`
- Create a directory `submissions` in the CSE546-SPRING-2026 directory and move your zip file to the submissions directory.


## Prepare to run the autograder
- Install Python: `sudo apt install python3 python3-pip`
- Install dependencies: `pip3 install boto3 pandas`
- Populate the `class_roster.csv`
  - If you are a student; replace the given template only with your details.
  - If you are a grader; use the class roster for the entire class
- **Ensure all 10 EC2 worker instances are named `<ASU-ID>-fl-worker-0` through `<ASU-ID>-fl-worker-9` and are in the `stopped` state** before running the autograder.
- **Ensure both S3 buckets (`<ASU-ID>-local-bucket`, `<ASU-ID>-global-bucket`) are empty** before running the autograder.
- **Ensure your Lambda function (`fl-aggregator`) is deployed and Active.**
- **Ensure all 10 Greengrass core devices `<ASU-ID>-fl-worker-<0-9>-gg` are registered and HEALTHY** in AWS IoT Greengrass.
- **Ensure the 10 IoT Things `<ASU-ID>-fl-worker-<0-9>-gg` exist** and the MQTT policy allows workers to subscribe to `fl/<ASU-ID>/next-round`.


## Run the autograder
- Run the autograder: `python3 autograder.py --num_rounds 5`
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

2026-04-10 23:25:55,654 - INFO - +++++++++++++++++++++++++++++++ CSE546 Autograder  +++++++++++++++++++++++++++++++
2026-04-10 23:25:55,654 - INFO - - 1) Extract the credentials from the credentials.txt
2026-04-10 23:25:55,655 - INFO - - 2) Execute the test cases as per the Grading Rubrics
2026-04-10 23:25:55,655 - INFO - ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
2026-04-10 23:25:55,655 - INFO - ++++++++++++++++++++++++++++ Autograder Configurations ++++++++++++++++++++++++++++
2026-04-10 23:25:55,655 - INFO - Project Path: /home/local/ASURITE/qlin36/CSE546-Cloud-Computing/ta
2026-04-10 23:25:55,655 - INFO - Grade Project: Project-2-Part-2
2026-04-10 23:25:55,655 - INFO - Class Roster: class_roster.csv
2026-04-10 23:25:55,655 - INFO - Zip folder path: /home/local/ASURITE/qlin36/CSE546-Cloud-Computing/ta/submissions
2026-04-10 23:25:55,655 - INFO - Autograder Results: Project-2-Part-2-grades.csv
2026-04-10 23:25:55,655 - INFO - Num Rounds: 5
2026-04-10 23:25:55,655 - INFO - ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
2026-04-10 23:25:55,657 - INFO - ++++++++++++++++++ Grading for Test Student ASUID: 9876543210 +++++++++++++++++++++
2026-04-10 23:25:55,659 - INFO - Extracted /home/local/ASURITE/qlin36/CSE546-Cloud-Computing/ta/submissions/Project2-9876543210.zip to extracted
2026-04-10 23:25:55,659 - INFO - File: extracted/credentials/credentials.txt has values ('xx', 'xx')
2026-04-10 23:25:55,659 - INFO - Credentials parsing complete.
2026-04-10 23:25:55,729 - INFO - ------------------------------------------------------------
2026-04-10 23:25:55,729 - INFO - IAM ACCESS KEY ID: xx
2026-04-10 23:25:55,729 - INFO - IAM SECRET ACCESS KEY: xx
2026-04-10 23:25:55,729 - INFO - ------------------------------------------------------------
2026-04-10 23:25:56,093 - INFO - Following policies are attached with IAM user:cse546-AutoGrader: ['AWSGreengrassReadOnlyAccess', 'AWSIoTFullAccess', 'AmazonEC2FullAccess', 'IAMReadOnlyAccess', 'AmazonS3FullAccess', 'AWSLambda_ReadOnlyAccess']
2026-04-10 23:25:56,093 - INFO - [IAM-log] IAMReadOnlyAccess policy attached
2026-04-10 23:25:56,093 - INFO - [IAM-log] AmazonEC2FullAccess policy attached
2026-04-10 23:25:56,093 - INFO - [IAM-log] AmazonS3FullAccess policy attached
2026-04-10 23:25:56,093 - INFO - [IAM-log] Lambda ReadOnlyAccess policy attached
2026-04-10 23:25:56,093 - INFO - [IAM-log] AWSIoTFullAccess policy attached
2026-04-10 23:25:56,093 - INFO - [IAM-log] AWSGreengrassReadOnlyAccess policy attached
2026-04-10 23:25:56,341 - INFO - -------------- CSE546 Cloud Computing Grading Console -----------
2026-04-10 23:25:56,341 - INFO - IAM ACCESS KEY ID: xx
2026-04-10 23:25:56,341 - INFO - ASUID: 9876543210
2026-04-10 23:25:56,342 - INFO - ------------------------------------------------------------
2026-04-10 23:25:56,342 - INFO - ----------------- Checking The Initial State ----------------
2026-04-10 23:25:56,342 - INFO - 
  === TC-1: Validate Initial State ===
2026-04-10 23:25:56,342 - INFO - 
  TC-1a: S3 Buckets
2026-04-10 23:25:56,342 - INFO -   --------------------------------------------------
2026-04-10 23:25:56,635 - INFO -     local-bucket (9876543210-local-bucket): EXISTS, empty
2026-04-10 23:25:56,974 - INFO -     global-bucket (9876543210-global-bucket): EXISTS, empty
2026-04-10 23:25:56,974 - INFO - 
  TC-1b: EC2 Instances
2026-04-10 23:25:56,974 - INFO -   --------------------------------------------------
2026-04-10 23:25:57,597 - INFO -     Found 10 9876543210-fl-worker instances
2026-04-10 23:25:57,597 - INFO -     9876543210-fl-worker-0 (i-08706f1dfb48ed662) — stopped (t3.micro)
2026-04-10 23:25:57,597 - INFO -     9876543210-fl-worker-1 (i-01d6189041f8a81ca) — stopped (t3.micro)
2026-04-10 23:25:57,597 - INFO -     9876543210-fl-worker-2 (i-076a7dbe205ea84e7) — stopped (t3.micro)
2026-04-10 23:25:57,597 - INFO -     9876543210-fl-worker-3 (i-00e7288b3ace06303) — stopped (t3.micro)
2026-04-10 23:25:57,598 - INFO -     9876543210-fl-worker-4 (i-053bdfc44f63ef9e4) — stopped (t3.micro)
2026-04-10 23:25:57,598 - INFO -     9876543210-fl-worker-5 (i-0add873528e958e2e) — stopped (t3.micro)
2026-04-10 23:25:57,598 - INFO -     9876543210-fl-worker-6 (i-07f92158f5456ab83) — stopped (t3.micro)
2026-04-10 23:25:57,598 - INFO -     9876543210-fl-worker-7 (i-0a70734e653cc3cc3) — stopped (t3.micro)
2026-04-10 23:25:57,598 - INFO -     9876543210-fl-worker-8 (i-033dc581e20c497f6) — stopped (t3.micro)
2026-04-10 23:25:57,598 - INFO -     9876543210-fl-worker-9 (i-081b5deb26175e371) — stopped (t3.micro)
2026-04-10 23:25:57,598 - INFO - 
  TC-1c: Lambda Function
2026-04-10 23:25:57,598 - INFO -   --------------------------------------------------
2026-04-10 23:25:57,950 - INFO -     Lambda 'fl-aggregator': ARN=arn:aws:lambda:us-west-2:049323679197:function:fl-aggregator
2026-04-10 23:25:57,950 - INFO -     State: Active
2026-04-10 23:25:57,951 - INFO -     Memory: 2048 MB
2026-04-10 23:25:57,951 - INFO - 
  TC-1d: Greengrass Core Devices
2026-04-10 23:25:57,951 - INFO -   --------------------------------------------------
2026-04-10 23:25:58,258 - INFO -     Greengrass API accessible — found 10 core devices:
2026-04-10 23:25:58,259 - INFO -       - 9876543210-fl-worker-8-gg: HEALTHY
2026-04-10 23:25:58,259 - INFO -       - 9876543210-fl-worker-1-gg: HEALTHY
2026-04-10 23:25:58,259 - INFO -       - 9876543210-fl-worker-0-gg: HEALTHY
2026-04-10 23:25:58,259 - INFO -       - 9876543210-fl-worker-3-gg: HEALTHY
2026-04-10 23:25:58,259 - INFO -       - 9876543210-fl-worker-7-gg: HEALTHY
2026-04-10 23:25:58,259 - INFO -       - 9876543210-fl-worker-6-gg: HEALTHY
2026-04-10 23:25:58,259 - INFO -       - 9876543210-fl-worker-5-gg: HEALTHY
2026-04-10 23:25:58,259 - INFO -       - 9876543210-fl-worker-2-gg: HEALTHY
2026-04-10 23:25:58,259 - INFO -       - 9876543210-fl-worker-4-gg: HEALTHY
2026-04-10 23:25:58,259 - INFO -       - 9876543210-fl-worker-9-gg: HEALTHY
2026-04-10 23:25:58,259 - INFO -     All 10 core devices HEALTHY
2026-04-10 23:25:58,259 - INFO - 
  TC-1e: IoT Things
2026-04-10 23:25:58,259 - INFO -   --------------------------------------------------
2026-04-10 23:25:58,529 - INFO -     9876543210-fl-worker-0-gg: EXISTS
2026-04-10 23:25:58,593 - INFO -     9876543210-fl-worker-1-gg: EXISTS
2026-04-10 23:25:58,655 - INFO -     9876543210-fl-worker-2-gg: EXISTS
2026-04-10 23:25:58,716 - INFO -     9876543210-fl-worker-3-gg: EXISTS
2026-04-10 23:25:58,778 - INFO -     9876543210-fl-worker-4-gg: EXISTS
2026-04-10 23:25:58,844 - INFO -     9876543210-fl-worker-5-gg: EXISTS
2026-04-10 23:25:58,903 - INFO -     9876543210-fl-worker-6-gg: EXISTS
2026-04-10 23:25:58,969 - INFO -     9876543210-fl-worker-7-gg: EXISTS
2026-04-10 23:25:59,031 - INFO -     9876543210-fl-worker-8-gg: EXISTS
2026-04-10 23:25:59,078 - INFO -     9876543210-fl-worker-9-gg: EXISTS
2026-04-10 23:25:59,079 - INFO - 
  TC-1 Deductions: -0
2026-04-10 23:25:59,079 - INFO - ----------------- Executing FL Training ----------------
2026-04-10 23:25:59,079 - INFO - 
  === TC-2: FL Execution ===
2026-04-10 23:25:59,079 - INFO - 
  Step 1 — Verify local data files
2026-04-10 23:25:59,079 - INFO -   --------------------------------------------------
2026-04-10 23:25:59,079 - INFO -     labels.csv: 195.3 KB
2026-04-10 23:25:59,079 - INFO -     test.tar.gz: 249.3 KB
2026-04-10 23:25:59,080 - INFO -     initial_model.npz: 243.5 KB
2026-04-10 23:25:59,080 - INFO - 
  Step 2 — Clean S3 buckets
2026-04-10 23:25:59,080 - INFO -   --------------------------------------------------
2026-04-10 23:25:59,170 - INFO -     9876543210-global-bucket:metrics/ — already clean
2026-04-10 23:25:59,225 - INFO -     9876543210-global-bucket:models/ — already clean
2026-04-10 23:25:59,281 - INFO -     9876543210-local-bucket:updates/ — already clean
2026-04-10 23:25:59,281 - INFO - 
  Step 3 — Upload data files
2026-04-10 23:25:59,281 - INFO -   --------------------------------------------------
2026-04-10 23:25:59,586 - INFO -     Uploaded 9876543210-global-bucket:labels.csv
2026-04-10 23:25:59,767 - INFO -     Uploaded 9876543210-global-bucket:archives/test.tar.gz
2026-04-10 23:25:59,906 - INFO -     Uploaded 9876543210-global-bucket:models/global_model_round_0.npz
2026-04-10 23:25:59,906 - INFO - 
  Step 4 — Start client instances
2026-04-10 23:25:59,906 - INFO -   --------------------------------------------------
2026-04-10 23:26:00,275 - INFO -     9876543210-fl-worker-0 (i-08706f1dfb48ed662)
2026-04-10 23:26:00,275 - INFO -     9876543210-fl-worker-1 (i-01d6189041f8a81ca)
2026-04-10 23:26:00,275 - INFO -     9876543210-fl-worker-2 (i-076a7dbe205ea84e7)
2026-04-10 23:26:00,275 - INFO -     9876543210-fl-worker-3 (i-00e7288b3ace06303)
2026-04-10 23:26:00,275 - INFO -     9876543210-fl-worker-4 (i-053bdfc44f63ef9e4)
2026-04-10 23:26:00,275 - INFO -     9876543210-fl-worker-5 (i-0add873528e958e2e)
2026-04-10 23:26:00,275 - INFO -     9876543210-fl-worker-6 (i-07f92158f5456ab83)
2026-04-10 23:26:00,275 - INFO -     9876543210-fl-worker-7 (i-0a70734e653cc3cc3)
2026-04-10 23:26:00,275 - INFO -     9876543210-fl-worker-8 (i-033dc581e20c497f6)
2026-04-10 23:26:00,275 - INFO -     9876543210-fl-worker-9 (i-081b5deb26175e371)
2026-04-10 23:26:01,444 - INFO -     Starting 10 instances ...
2026-04-10 23:26:17,072 - INFO -     All instances running.
2026-04-10 23:26:17,072 - INFO - 
  Step 5 — Wait for Greengrass init (60s)
2026-04-10 23:26:17,072 - INFO -   --------------------------------------------------
2026-04-10 23:27:17,077 - INFO -     Greengrass init wait complete
2026-04-10 23:27:17,077 - INFO - 
  Step 6 — Publish MQTT trigger for round 0
2026-04-10 23:27:17,078 - INFO -   --------------------------------------------------
2026-04-10 23:27:17,609 - INFO -     Published to fl/9876543210/next-round: {"round_number": 0, "num_rounds": 5}
2026-04-10 23:27:17,609 - INFO - 
  Step 7 — Monitor training (5 rounds, timeout 300s)
2026-04-10 23:27:17,609 - INFO -   --------------------------------------------------
2026-04-10 23:27:28,041 - INFO -     Round 0: accuracy=0.9026, loss=0.3277 (11.0s)
2026-04-10 23:27:33,189 - INFO -     Round 1: accuracy=0.9558, loss=0.1258 (16.1s)
2026-04-10 23:27:43,380 - INFO -     Round 2: accuracy=0.9719, loss=0.0961 (26.3s)
2026-04-10 23:27:53,581 - INFO -     Round 3: accuracy=0.9739, loss=0.0885 (36.5s)
2026-04-10 23:28:03,770 - INFO -     Round 4: accuracy=0.9739, loss=0.0830 (46.7s)
2026-04-10 23:28:03,770 - INFO -     Training complete in 46.7s
2026-04-10 23:28:03,770 - INFO - 
  Step 8 — Stop instances
2026-04-10 23:28:03,771 - INFO -   --------------------------------------------------
2026-04-10 23:28:04,797 - INFO -     Stopping 10 instances ...
2026-04-10 23:28:50,847 - INFO -     All instances stopped.
2026-04-10 23:28:50,848 - INFO - ----------------- Checking Training Artifacts ----------------
2026-04-10 23:28:50,848 - INFO - 
  === TC-3: Validate FL Artifacts ===
2026-04-10 23:28:50,848 - INFO - 
  Round 0:
2026-04-10 23:28:50,848 - INFO -   --------------------------------------------------
2026-04-10 23:28:51,116 - INFO -     Global model (round 1): FOUND
2026-04-10 23:28:51,877 - INFO -     Local models: 10/10
2026-04-10 23:28:51,929 - INFO -     Metrics (round_0.json): FOUND
2026-04-10 23:28:51,929 - INFO -     All artifacts present
2026-04-10 23:28:51,930 - INFO - 
  Round 1:
2026-04-10 23:28:51,930 - INFO -   --------------------------------------------------
2026-04-10 23:28:51,983 - INFO -     Global model (round 2): FOUND
2026-04-10 23:28:52,545 - INFO -     Local models: 10/10
2026-04-10 23:28:52,598 - INFO -     Metrics (round_1.json): FOUND
2026-04-10 23:28:52,598 - INFO -     All artifacts present
2026-04-10 23:28:52,598 - INFO - 
  Round 2:
2026-04-10 23:28:52,599 - INFO -   --------------------------------------------------
2026-04-10 23:28:52,653 - INFO -     Global model (round 3): FOUND
2026-04-10 23:28:53,212 - INFO -     Local models: 10/10
2026-04-10 23:28:53,264 - INFO -     Metrics (round_2.json): FOUND
2026-04-10 23:28:53,265 - INFO -     All artifacts present
2026-04-10 23:28:53,265 - INFO - 
  Round 3:
2026-04-10 23:28:53,265 - INFO -   --------------------------------------------------
2026-04-10 23:28:53,319 - INFO -     Global model (round 4): FOUND
2026-04-10 23:28:53,870 - INFO -     Local models: 10/10
2026-04-10 23:28:53,930 - INFO -     Metrics (round_3.json): FOUND
2026-04-10 23:28:53,930 - INFO -     All artifacts present
2026-04-10 23:28:53,930 - INFO - 
  Round 4:
2026-04-10 23:28:53,930 - INFO -   --------------------------------------------------
2026-04-10 23:28:53,989 - INFO -     Global model (round 5): FOUND
2026-04-10 23:28:54,553 - INFO -     Local models: 10/10
2026-04-10 23:28:54,608 - INFO -     Metrics (round_4.json): FOUND
2026-04-10 23:28:54,608 - INFO -     All artifacts present
2026-04-10 23:28:54,608 - INFO - 
  TC-3 Deductions: -0
2026-04-10 23:28:54,608 - INFO - ----------------- Checking Model Accuracy ----------------
2026-04-10 23:28:54,608 - INFO - 
  === TC-4: Validate Model Accuracy ===
2026-04-10 23:28:54,961 - INFO - 
  TC-4a: Final Accuracy
2026-04-10 23:28:54,961 - INFO -   --------------------------------------------------
2026-04-10 23:28:54,962 - INFO -     Final Accuracy: 0.9739
2026-04-10 23:28:54,962 - INFO -     Final Loss:     0.0830
2026-04-10 23:28:54,962 - INFO -     Score: 50/50
2026-04-10 23:28:54,962 - INFO - 
  TC-4b: Accuracy Progression
2026-04-10 23:28:54,962 - INFO -   --------------------------------------------------
2026-04-10 23:28:54,962 - INFO -     Round-by-round accuracy:
2026-04-10 23:28:54,962 - INFO -       Round 0: acc=0.9026, loss=0.3277
2026-04-10 23:28:54,962 - INFO -       Round 1: acc=0.9568, loss=0.1271
2026-04-10 23:28:54,962 - INFO -       Round 2: acc=0.9719, loss=0.0961
2026-04-10 23:28:54,963 - INFO -       Round 3: acc=0.9739, loss=0.0885
2026-04-10 23:28:54,963 - INFO -       Round 4: acc=0.9739, loss=0.0830
2026-04-10 23:28:54,963 - INFO - 
  TC-4 Score: 50/50, Deductions: -0
2026-04-10 23:28:54,963 - INFO - ----------------- Checking Training Speed ----------------
2026-04-10 23:28:54,963 - INFO - 
  === TC-5: Validate Training Speed ===
2026-04-10 23:28:54,963 - INFO -   --------------------------------------------------
2026-04-10 23:28:54,963 - INFO -     Training time: 46.7s
2026-04-10 23:28:54,963 - INFO -     Score: 50/50
2026-04-10 23:28:54,963 - INFO -     Tier: < 60s
2026-04-10 23:28:54,963 - INFO - 
  ==================================================
2026-04-10 23:28:54,963 - INFO -   SCORE BREAKDOWN:
2026-04-10 23:28:54,964 - INFO -     Accuracy:   50/50
2026-04-10 23:28:54,964 - INFO -     Speed:      50/50
2026-04-10 23:28:54,964 - INFO -     Deductions: -0
2026-04-10 23:28:54,964 - INFO -     ---
2026-04-10 23:28:54,964 - INFO -     TOTAL: 100/100
2026-04-10 23:28:54,964 - INFO - Total Grade Points: 100
2026-04-10 23:28:54,964 - INFO - 
----------------- Post-run S3 Cleanup ----------------
2026-04-10 23:28:55,292 - INFO -     9876543210-global-bucket — deleted 14 objects
2026-04-10 23:29:00,352 - INFO -     9876543210-global-bucket — confirmed empty after 1 pass(es)
2026-04-10 23:29:01,111 - INFO -     9876543210-local-bucket — deleted 50 objects
2026-04-10 23:29:06,401 - INFO -     9876543210-local-bucket — confirmed empty after 1 pass(es)
2026-04-10 23:29:06,402 - INFO - Removed extracted folder: extracted
2026-04-10 23:29:06,405 - INFO - Total time taken to grade for Test Student ASUID: 9876543210: 190.74780941009521 seconds
2026-04-10 23:29:06,405 - INFO - ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
2026-04-10 23:29:06,405 - INFO - Grading complete for Project-2-Part-2. Check the Project-2-Part-2-grades.csv file.

```
