#!/usr/bin/python3

"""
File: utils.py
Author: CSE546 Cloud Computing
Description: Utils for Project-2 Part-2 Autograder
"""
import os
import shutil
import zipfile
import pandas as pd
from grade_project2_p2 import *


def print_and_log(logger, message):
    print(message)
    logger.info(message)


def print_and_log_error(logger, message):
    print(message)
    logger.error(message)


def is_none_or_empty(string):
    return string is None or string.strip() == ""


def write_to_csv(data, csv_path):
    df = pd.DataFrame(data)
    if os.path.exists(csv_path):
        df.to_csv(csv_path, mode='a', header=False, index=False)
    else:
        df.to_csv(csv_path, mode='w', header=True, index=False)


def extract_zip(logger, zip_path, extract_to):
    """Extract the student's zip file."""
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)
    print_and_log(logger, f"Extracted {zip_path} to {extract_to}")


def del_directory(logger, directory_name):
    try:
        if os.path.exists(directory_name) and os.path.isdir(directory_name):
            shutil.rmtree(directory_name)
            print_and_log(logger, f"Removed extracted folder: {directory_name}")
    except Exception as e:
        print_and_log_error(logger, f"Could not remove extracted folder {directory_name}: {e}")


def read_and_extract_file(logger, file_path):
    try:
        with open(file_path, 'r') as file:
            if "credentials.txt" in file_path:
                contents = file.read().strip()
                values = contents.split(",")
                print_and_log(logger, f"File: {file_path} has values {tuple(values)}")
                return tuple(values)
            else:
                return "Other files found!"
    except FileNotFoundError:
        print_and_log_error(logger, f"File not found: {file_path}")
        return None
    except Exception as e:
        print_and_log_error(logger, f"An error occurred: {e}")
        return None


def append_grade_remarks(results, name, asuid,
                         tc_0_status, tc_0_logs,
                         tc_1_status, tc_1_logs,
                         tc_infra_pts, tc_infra_logs,
                         tc_e2e_pts, tc_e2e_logs,
                         grade_points, grade_comments):

    results.append({
        'Name': name,
        'ASUID': asuid,
        'Test-0 (Sanity)': tc_0_status,
        'Test-0-logs': tc_0_logs,
        'Test-1 (IAM)': tc_1_status,
        'Test-1-logs': tc_1_logs,
        'TC-1 (Infrastructure)': tc_infra_pts,
        'TC-1-logs': tc_infra_logs,
        'TC-2 (E2E Training)': tc_e2e_pts,
        'TC-2-logs': tc_e2e_logs,
        'Total Grades': grade_points,
        'Comments': grade_comments,
    })
    return results
