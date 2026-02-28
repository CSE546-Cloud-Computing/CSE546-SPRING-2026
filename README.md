# Autograder for Project-1 Part 2

Make sure that you use the provided autograder and follow the instructions below to test your project submission. Failure to do so may cause you to lose all the project points and there will be absolutely no second chance.

- Download the zip file you submitted from Canvas. 
- Download the autograder from GitHub: `https://github.com/CSE546-Cloud-Computing/CSE546-SPRING-2026.git`
  - In order to clone the GitHub repository follow the below steps:
  - `git clone https://github.com/CSE546-Cloud-Computing/CSE546-SPRING-2026.git`
  - `cd CSE546-SPRING-2026/`
  - `git checkout project-1-part-2`
- Create a directory `submissions` in the CSE546-SPRING-2026 directory and move your zip file to the submissions directory.

## Prepare to run the autograder
- Install Python: `sudo apt install python3`
- Populate the `class_roster.csv`
  - If you are a student; replace the given template only with your details.
  - If you are a grader; use the class roster for the entire class

## Run the autograder
- Run the autograder: `python3 autograder.py --num_requests 100 --img_folder="<dataset folder path>" --pred_file="<output classification csv file path>"`
  ```
  python3 autograder.py --help
  usage: autograder.py [-h] [--img_folder IMG_FOLDER] [--pred_file PRED_FILE] [--num_requests NUM_REQUESTS]
  Upload images
  options:
  -h, --help            show this help message and exit
  --num_requests NUM_REQUESTS  Number of Requests
  --img_folder IMG_FOLDER Path to the input images
  --pred_file PRED_FILE Classfication results file
  ```
- The autograder will look for submissions for each entry present in the class_roster.csv
- For each submission the autograder will
  - Validate if the zip file adheres to the submission guidelines as mentioned in the project document. Autograder expect case sensitive folder and file names.
    - If Yes; proceed to next step
    - If No; allocate 0 grade points and proceed to the next submission
  - The autograder extracts the credentials.txt from the submission and parses the entries.
  - Use the Grader IAM credentials to test the project as per the grading rubrics and allocate grade points.
  - The autograder will dump stdout and stderr in a log file named `autograder.log`
      
## Sample Output

```
+++++++++++++++++++++++++++++++ CSE546 Autograder  +++++++++++++++++++++++++++++++
- 1) The script will first look up for the zip file following the naming conventions as per project document
- 2) The script will then do a sanity check on the zip file to make sure all the expected files are present
- 3) Extract the credentials from the credentials.txt
- 4) Execute the test cases as per the Grading Rubrics
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
++++++++++++++++++++++++++++ Autograder Configurations ++++++++++++++++++++++++++++
Project Path: /home/local/ASUAD/kjha9/git/GTA-CSE546-SPRING-2026/Project-1/part-2/grader
Grade Project: Project-1
Class Roster: class_roster.csv
Zip folder path: /home/local/ASUAD/kjha9/git/GTA-CSE546-SPRING-2026/Project-1/part-2/grader/submissions
Grading script: /home/local/ASUAD/kjha9/git/GTA-CSE546-SPRING-2026/Project-1/part-2/grader/grade_project1_p2.py
Test Image folder path: ../web-tier/upload_images/
Classification results file: ../../Classification Results on Face Dataset (1000 images).csv
Autograder Results: Project-1-grades.csv
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
The file Project-1-grades.csv does NOT exist.
++++++++++++++++++ Grading for Doe John ASUID: 1225754101 +++++++++++++++++++++
Extracted /home/local/ASUAD/kjha9/git/GTA-CSE546-SPRING-2026/Project-1/part-2/grader/submissions/Project1-1225754101.zip to extracted
File: extracted/credentials/credentials.txt has values ('XXXXXXXXXXXXXXXXXXXXXXXXX', 'XXXXXXXXXXXXXXXXXXXXXXXXX', 'XXXXXXXXXXXXXXXXXXXXXXXXX')
Unzip submission and check folders/files: PASS
Credentials parsing complete.
-----------------------------------------------------------------
IAM ACESS KEY ID: XXXXXXXXXXXXXXXXXXXXXXXXX
IAM SECRET ACCESS KEY: XXXXXXXXXXXXXXXXXXXXXXXXX
-----------------------------------------------------------------
Following policies are attached with IAM user:cse546-AutoGrader: ['AmazonEC2ReadOnlyAccess', 'IAMReadOnlyAccess', 'AmazonSQSFullAccess', 'AmazonDynamoDBFullAccess' 'AmazonS3FullAccess']
[IAM-log] AmazonEC2ReadOnlyAccess policy attached with grading IAM
[IAM-log] AmazonS3FullAccess policy attached with grading IAM
[IAM-log] AmazonSQSFullAccess policy attached with grading IAM
[DynamoDB-log] AmazonDynamoDBFullAccess policy attached with grading IAM
[Cloudwatch-log] CAUTION !! You do not have a Cloudwatch alarm set. Kindly refer to the Project-0 document and learn how to set a billing alarm
-------------- CSE546 Cloud Computing Grading Console -----------
IAM ACESS KEY ID: XXXXXXXXXXXXXXXXXXXXXXXXX
IAM SECRET ACCESS KEY: XXXXXXXXXXXXXXXXXXXXXXXXX
Web-Instance IP Address: XXXXXXXXXXXXXXXXXXXXXXXXX
-----------------------------------------------------------------
----------------- Executing Test-Case:1 ----------------
[EC2-log] AmazonEC2ReadOnlyAccess policy attached with grading IAM
[EC2-log] Found 1 web-tier instances in running state.
[EC2-log] Found 0 app-tier instances in running state
[EC2-log] EC2-state validation Pass. Found 1 web-tier instances in running state. Found 0 app-tier instances in running state.Points deducted: 0
[S3-log] AmazonS3FullAccess policy attached with grading IAM
[S3-log] - WARN: If there are objects in the S3 buckets; they will be deleted
[S3-log] ---------------------------------------------------------
[S3-log] Bucket:1225754101-in-bucket is now EMPTY !!
[S3-log] S3 Bucket:1225754101-in-bucket has 0 object(s).
[S3-log] Points deducted:0
[SQS-log] The expectation is that both the Request and Response SQS should exist with max message size set to 1KB and be EMPTY
[SQS-log] - WARN: This will purge any messages available in the SQS
[SQS-log] ---------------------------------------------------------
[SQS-log] AmazonSQSFullAccess policy attached with grading IAM
[SQS-log] SQS Request Queue:1225754101-req-queue has 0 pending messages with max message size set to 1 KB.
[SQS-log] SQS Response Queue:1225754101-resp-queue has 0 pending messages.
[SQS-log] Points deducted:0
[DynamoDB-log] AmazonDynamoDBFullAccess policy attached with grading IAM
[DynamoDB-log] The expectation is that the DynamoDB table should exist and be EMPTY
[DynamoDB-log] - WARN: If there are items in the table, they will be deleted
[DynamoDB-log] ---------------------------------------------------------
[DynamoDB-log] DynamoDB Table:1225754101-dynamoDB exists with 0 item(s).
[DynamoDB-log] Points deducted:0
----------------- Executing Test-Case:2 ----------------
[AS-log] - Autoscaling validation starts ..
[AS-log] - The expectation is as follows:
[AS-log]  -- # of app tier instances should gradually scale and eventually reduce back to 0
[AS-log]  -- # of SQS messages should gradually increase and eventually reduce back to 0
-------------------------------------------------------------------------------------------------------------------  
|   # of messages in   |   # of messages in   |   # of app-tier EC2  |  # of objects in S3  |     # of items in   |
|  SQS Request Queue   |  SQS Response Queue  | instances in running |     Input Bucket     |    DynamoDB Table   |
-------------------------------------------------------------------------------------------------------------------
|          0           |          0           |          0           |          0           |          0          |
-------------------------------------------------------------------------------------------------------------------
|          0           |          0           |          0           |          63          |          0          |
-------------------------------------------------------------------------------------------------------------------
|          0           |          0           |          0           |         100          |          0          |
-------------------------------------------------------------------------------------------------------------------
|          56          |          0           |          0           |         100          |          0          |
-------------------------------------------------------------------------------------------------------------------
|          94          |          0           |          0           |         100          |          0          |
-------------------------------------------------------------------------------------------------------------------
|          0           |          0           |          2           |         100          |          0          |
-------------------------------------------------------------------------------------------------------------------
|          56          |          0           |          5           |         100          |          0          |
-------------------------------------------------------------------------------------------------------------------
|         100          |          0           |          8           |         100          |          0          |
-------------------------------------------------------------------------------------------------------------------
|         100          |          0           |          10          |         100          |          0          |
-------------------------------------------------------------------------------------------------------------------
|         100          |          0           |          11          |         100          |          0          |
-------------------------------------------------------------------------------------------------------------------
|         100          |          0           |          15          |         100          |          0          |
-------------------------------------------------------------------------------------------------------------------
|          0           |          0           |          15          |         100          |          0          |
-------------------------------------------------------------------------------------------------------------------
|          97          |          0           |          15          |         100          |          0          |
-------------------------------------------------------------------------------------------------------------------
|          95          |          0           |          15          |         100          |          0          |
-------------------------------------------------------------------------------------------------------------------
|          93          |          0           |          15          |         100          |          1          |
-------------------------------------------------------------------------------------------------------------------
|         100          |          0           |          15          |         100          |          2          |
-------------------------------------------------------------------------------------------------------------------
|          77          |          0           |          15          |         100          |          7          |
-------------------------------------------------------------------------------------------------------------------
|          87          |          0           |          15          |         100          |          10         |
-------------------------------------------------------------------------------------------------------------------
|          89          |          2           |          15          |         100          |          14         |
-------------------------------------------------------------------------------------------------------------------
|          80          |          0           |          15          |         100          |          22         |
-------------------------------------------------------------------------------------------------------------------
|          70          |          0           |          15          |         100          |          26         |
-------------------------------------------------------------------------------------------------------------------
|          58          |          7           |          15          |         100          |          31         |
-------------------------------------------------------------------------------------------------------------------
|          49          |          0           |          15          |         100          |          39         |
-------------------------------------------------------------------------------------------------------------------
|          42          |          7           |          15          |         100          |          42         |
-------------------------------------------------------------------------------------------------------------------
|          42          |          2           |          15          |         100          |          50         |
-------------------------------------------------------------------------------------------------------------------
|          35          |          8           |          15          |         100          |          54         |
-------------------------------------------------------------------------------------------------------------------
|          29          |          3           |          15          |         100          |          58         |
-------------------------------------------------------------------------------------------------------------------
|          18          |          2           |          15          |         100          |          67         |
-------------------------------------------------------------------------------------------------------------------
|          18          |          6           |          15          |         100          |          71         |
-------------------------------------------------------------------------------------------------------------------
|          21          |          4           |          15          |         100          |          76         |
-------------------------------------------------------------------------------------------------------------------
|          8           |          10          |          15          |         100          |          84         |
-------------------------------------------------------------------------------------------------------------------
|          10          |          7           |          15          |         100          |          88         |
-------------------------------------------------------------------------------------------------------------------
|          6           |          5           |          15          |         100          |          97         |
-------------------------------------------------------------------------------------------------------------------
|          0           |          9           |          15          |         100          |         100         |
-------------------------------------------------------------------------------------------------------------------
|          6           |          11          |          15          |         100          |         100         |
-------------------------------------------------------------------------------------------------------------------
[Workload-gen] ----- Workload Generator Statistics -----
[Workload-gen] Total number of requests: 100
[Workload-gen] Total number of requests completed successfully: 100
[Workload-gen] Total number of failed requests: 0
[Workload-gen] Total number of correct predictions : 100
[Workload-gen] Total number of wrong predictions: 0
[Workload-gen] Total response time: 87.09396982192993 (seconds)
[Workload-gen] -----------------------------------
|          0           |          6           |          13          |         100          |         100         |
-------------------------------------------------------------------------------------------------------------------
|          0           |          6           |          7           |         100          |         100         |
-------------------------------------------------------------------------------------------------------------------
|          0           |          0           |          1           |         100          |         100         |
-------------------------------------------------------------------------------------------------------------------
|          0           |          2           |          0           |         100          |         100         |
-------------------------------------------------------------------------------------------------------------------
[Test-Case-3-log] Waiting for 5sec for the resources to scale in ...
[AS-log] Time to scale in to 0 instances: 0.11 seconds.Points:[10/10]
|          0           |          6           |          0           |         100          |         100         |
-------------------------------------------------------------------------------------------------------------------
|          0           |          0           |          0           |         100          |         100         |
-------------------------------------------------------------------------------------------------------------------
[Test-Case-3-log] Stop event set. Waiting for autoscaling thread to finish.
[Test-Case-3-log] 100/100 entries in S3 bucket:1225754101-in-bucket.Points:[5.0/5]
[Test-Case-3-log] 100/100 correct predictions.Points:[10.0/10]
[Test-Case-3-log] Test Average Latency: 0.8709396982192993 sec. `avg latency<1.2s`.Points:[20/20]
[Test-Case-3-log] ---------------------------------------------------------
[AS-log] EC2 instances scale out as expected. Points:[15/15]
[AS-log] EC2 instances scale back to 0 as expected. Points:[5/5]
[AS-log] SQS messages in 1225754101-req-queue increased from 0 and reduced back to 0. Points:[5/5]
[AS-log] SQS messages in 1225754101-resp-queue increased from 0 and reduced back to 0. Points:[5/5]
[AS-log] S3 bucket:1225754101-in-bucket objects increased from 0 to 100.
[S3-log] Bucket:1225754101-in-bucket is now EMPTY !!
[AS-log] DynamoDB table:1225754101-dynamoDB items increased from 0 to 100.
[AS-log] ---------------------------------------------------------
----------------- Executing Test-Case:3 (Warm Cache) ----------------
[Test-Case-WC-log] Preparing for warm cache run ...
[Test-Case-WC-log] Emptying S3 buckets and SQS queues (DynamoDB cache retained)
[S3-log] Bucket:1225754101-in-bucket is now EMPTY !!
[Test-Case-WC-log] Waiting for app-tier instances to scale in before warm cache run ...
[Workload-gen] ----- Workload Generator Statistics -----
[Workload-gen] Total number of requests: 100
[Workload-gen] Total number of requests completed successfully: 100
[Workload-gen] Total number of failed requests: 0
[Workload-gen] Total number of correct predictions : 100
[Workload-gen] Total number of wrong predictions: 0
[Workload-gen] Total response time: 31.68979811668396 (seconds)
[Workload-gen] -----------------------------------
[Test-Case-3-log] Test Average Latency: 0.3168979811668396 sec. `avg latency<0.6s`.Points:[20/20]
[Test-Case-WC-log] ---------------------------------------------------------
[Test-Case-WC-log] Clearing DynamoDB table after warm cache run ...
[DynamoDB-log] Table:1225754101-dynamoDB is now EMPTY !!
Total Grade Points: 100.0
Removed extracted folder: extracted
Total time taken to grade for Doe John ASUID: 1225754101: 153.8372926712036 seconds
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
Grading complete for Project-1. Check the Project-1-grades.csv file.
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
`
