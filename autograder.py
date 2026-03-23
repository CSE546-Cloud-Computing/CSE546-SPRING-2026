#!/usr/bin/python3

"""
File: autograder.py
Author: CSE546 Cloud Computing
Description: Grading script for Project-2 Part-1 (Federated Learning)
"""
import os
import sys
import glob
import time
import logging
import argparse
import pandas as pd

from utils import *
from validate_permission_policies import *

parser = argparse.ArgumentParser(description='Project-2 Part-1 Autograder')

args         = parser.parse_args()

log_file = 'autograder.log'
logging.basicConfig(filename=log_file, level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

# CSV Files and Paths
grade_project           = "Project-2-Part-1"
project_path            = os.path.abspath(".")
roster_csv              = 'class_roster.csv'
grader_results_csv      = f'{grade_project}-grades.csv'
zip_folder_path         = f'{project_path}/submissions'

print_and_log(logger, f'+++++++++++++++++++++++++++++++ CSE546 Autograder  +++++++++++++++++++++++++++++++')
print_and_log(logger, "- 1) Extract the credentials from the credentials.txt")
print_and_log(logger, "- 2) Execute the test cases as per the Grading Rubrics")
print_and_log(logger, "++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")

print_and_log(logger, f'++++++++++++++++++++++++++++ Autograder Configurations ++++++++++++++++++++++++++++')
print_and_log(logger, f"Project Path: {project_path}")
print_and_log(logger, f"Grade Project: {grade_project}")
print_and_log(logger, f"Class Roster: {roster_csv}")
print_and_log(logger, f"Zip folder path: {zip_folder_path}")
print_and_log(logger, f"Autograder Results: {grader_results_csv}")
print_and_log(logger, "++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")

roster_df   = pd.read_csv(roster_csv)
results     = []

if os.path.exists(grader_results_csv):
    #todo
    pass
else:
    print_and_log(logger, f"The file {grader_results_csv} does NOT exist.")

for index, row in roster_df.iterrows():

    if 'First Name' in row and 'Last Name' in row:
        first_name = row['First Name']
        last_name  = row['Last Name']
        name = f"{last_name} {first_name}"
    else:
        name = str(row.get('Name', '')).strip()
        first_name = name
        last_name  = ''

    asuid = str(row['ASUID']).strip()

    print_and_log(logger, f'++++++++++++++++++ Grading for {name} ASUID: {asuid} +++++++++++++++++++++')

    start_time = time.time()
    grade_points        = 0
    grade_comments      = ""
    results             = []
    pattern             = os.path.join(zip_folder_path, f'*{asuid}*.zip')
    zip_files           = glob.glob(pattern)

    if zip_files and os.path.isfile(zip_files[0]):

        zip_file            = zip_files[0]
        sanity_pass         = True
        sanity_status       = ""
        sanity_err          = ""

        # STEP-1: Validate the zip file
        extracted_folder = f'extracted'
        del_directory(logger, extracted_folder)
        extract_zip(logger, zip_file, extracted_folder)

        credentials_txt_path = "extracted/credentials/credentials.txt"
        cred_values = read_and_extract_file(logger, credentials_txt_path)

        # Check all required submission files
        worker_py_path = "extracted/worker/worker.py"
        aggregator_py_path = "extracted/aggregator/aggregator.py"
        missing_files = []
        if not cred_values:
            missing_files.append("credentials/credentials.txt")
        if not os.path.isfile(worker_py_path):
            missing_files.append("worker/worker.py")
        if not os.path.isfile(aggregator_py_path):
            missing_files.append("aggregator/aggregator.py")

        if missing_files:
            sanity_pass     = False
            test_pass       = False
            test_status     = "Fail"
            test_comments   = f"Sanity Test Failed: missing {', '.join(missing_files)}. Please check if the zip follows the correct structure."
            test_err        = ""
            test_results    = []
            print_and_log_error(logger, test_comments)
        else:
            sanity_pass     = True
            test_pass       = True
            test_status     = "Pass"
            test_comments   = "Sanity Test Passed: credentials.txt, worker/worker.py, aggregator/aggregator.py found."
            test_err        = ""
            test_results    = []
            print_and_log(logger, test_comments)

        sanity_pass     = test_pass
        sanity_status   = test_status
        sanity_err      += test_err
        grade_comments  += test_comments
        results         = test_results

        if sanity_pass:

            sanity_comment = "Unzip submission and check folders/files: PASS"
            try:
                # STEP-2: Validate the credentials.txt (2 values: key_id, secret_key)
                if (len(cred_values) >= 2 and is_none_or_empty(cred_values[0]) == False
                        and is_none_or_empty(cred_values[1]) == False):
                    print_and_log(logger, "Credentials parsing complete.")
                else:
                    print_and_log_error(logger, "Issue with credentials submitted. Points: [0/100]")
                    grade_comments += f"Issue with submitted credentials. Credentials Found : {cred_values}"
                    grade_points = 0
                    results = append_grade_remarks(results, name, asuid,
                            sanity_status, sanity_comment,
                            "Fail", grade_comments,
                            0, grade_comments,
                            0, grade_comments,
                            0, grade_comments,
                            0, grade_comments,
                            grade_points, grade_comments)
                    write_to_csv(results, grader_results_csv)
                    continue

                try:
                    # STEP-3: Validate the permission policies
                    iam_obj = iam_policies(logger, cred_values[0], cred_values[1])
                    iam_ro_access_flag, ec2_access_flag, s3_access_flag, lambda_access_flag = iam_obj.validate_policies()

                    if (iam_ro_access_flag == False):
                        print_and_log(logger, "IAMReadOnlyAccess not attached.")

                    # STEP-4: Execute test cases
                    aws_grader = grader_project2_p1(
                        logger, asuid,
                        cred_values[0], cred_values[1],
                        ec2_access_flag, s3_access_flag,
                        lambda_access_flag, iam_ro_access_flag)

                    test_results = aws_grader.main()
                    grade_points = test_results["grade_points"]

                    # Build comments from all TCs
                    for tc_key in ["tc_1", "tc_2", "tc_3", "tc_4", "tc_5"]:
                        if tc_key in test_results:
                            grade_comments += test_results[tc_key][1] + "\n"

                    results = append_grade_remarks(results, name, asuid,
                                            sanity_status, sanity_comment,
                                            "Pass", "IAM policies validated",
                                            test_results["tc_1"][0], test_results["tc_1"][1],
                                            test_results["tc_3"][0], test_results["tc_3"][1],
                                            test_results["tc_4"][0], test_results["tc_4"][1],
                                            test_results["tc_5"][0], test_results["tc_5"][1],
                                            grade_points, grade_comments)

                except (ClientError, Exception) as e:
                    print_and_log_error(logger, f"Failed to fetch the attached policies. {e}")
                    print_and_log_error(logger, f"Total Grade Points: {grade_points}")
                    grade_comments += f"Failed to fetch attached policies. {e}"
                    grade_points = 0
                    results = append_grade_remarks(results, name, asuid,
                                                sanity_status, sanity_comment,
                                                "Fail", grade_comments,
                                                0, grade_comments,
                                                0, grade_comments,
                                                0, grade_comments,
                                                0, grade_comments,
                                                grade_points, grade_comments)

            except (Exception) as e:
                print_and_log_error(logger, "Error encountered while grading. Please inspect the autograder logs..")

            # Clean up: remove the extracted folder
            del_directory(logger, extracted_folder)

        else:
            sanity_comment = f"Unzip submission and check folders/files: FAIL {test_comments}"
            grade_comments += sanity_comment
            grade_points = 0
            results = append_grade_remarks(results, name, asuid,
                                                sanity_status, sanity_comment,
                                                "Fail", grade_comments,
                                                0, grade_comments,
                                                0, grade_comments,
                                                0, grade_comments,
                                                0, grade_comments,
                                                grade_points, grade_comments)
            logger.handlers[0].flush()
            del_directory(logger, extracted_folder)

    else:
        sanity_status           = False
        sanity_comment          = f"Submission File (.zip) not found for {asuid}."
        print_and_log_error(logger, sanity_comment)
        grade_comments      += f"{sanity_comment} There is a possibility that student has misspelled their asuid"
        grade_points = 0
        results = append_grade_remarks(results, name, asuid,
                                        sanity_status, sanity_comment,
                                        "Fail", grade_comments,
                                        0, grade_comments,
                                        0, grade_comments,
                                        0, grade_comments,
                                        0, grade_comments,
                                        grade_points, grade_comments)

    write_to_csv(results, grader_results_csv)

    # End timer
    end_time = time.time()

    # Calculate and print execution time
    execution_time = end_time - start_time
    print_and_log(logger, f"Total time taken to grade for {name} ASUID: {asuid}: {execution_time} seconds")
    print_and_log(logger, "++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
    logger.handlers[0].flush()

print_and_log(logger, f"Grading complete for {grade_project}. Check the {grader_results_csv} file.")
