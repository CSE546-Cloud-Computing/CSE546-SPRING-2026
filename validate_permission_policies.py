"""
File: validate_permission_policies.py
Author: CSE546 Cloud Computing
Description: Validate IAM permission policies for Project-2 Part-1 grading
"""

import boto3
from botocore.exceptions import ClientError


class iam_policies():
    def __init__(self, logger, access_keyId, access_key):

        self.iam_access_keyId = access_keyId
        self.iam_secret_access_key = access_key
        self.iam_session = boto3.Session(
            aws_access_key_id=self.iam_access_keyId,
            aws_secret_access_key=self.iam_secret_access_key)
        self.iam_client = self.iam_session.client("iam", 'us-west-2')
        self.logger = logger

        self.print_and_log(self.logger, "-" * 60)
        self.print_and_log(self.logger,
                           f"IAM ACCESS KEY ID: {self.iam_access_keyId}")
        self.print_and_log(self.logger,
                           f"IAM SECRET ACCESS KEY: {self.iam_secret_access_key}")
        self.print_and_log(self.logger, "-" * 60)

    def print_and_log(self, logger, message):
        print(message)
        logger.info(message)

    def print_and_log_error(self, logger, message):
        print(message)
        logger.error(message)

    def validate_ec2(self, attached_policies):
        if "AmazonEC2FullAccess" in attached_policies:
            self.print_and_log(self.logger,
                               "[IAM-log] AmazonEC2FullAccess policy attached with grading IAM")
            return True
        else:
            self.print_and_log_error(self.logger,
                                     "[IAM-log] AmazonEC2FullAccess policy NOT attached with grading IAM")
            return False

    def validate_s3(self, attached_policies):
        if "AmazonS3FullAccess" in attached_policies:
            self.print_and_log(self.logger,
                               "[IAM-log] AmazonS3FullAccess policy attached with grading IAM")
            return True
        else:
            self.print_and_log_error(self.logger,
                                     "[IAM-log] AmazonS3FullAccess policy NOT attached with grading IAM")
            return False

    def validate_lambda(self, attached_policies):
        # Check for either naming convention
        if ("AWSLambda_ReadOnlyAccess" in attached_policies or
                "AWSLambdaReadOnlyAccess" in attached_policies):
            self.print_and_log(self.logger,
                               "[IAM-log] Lambda ReadOnlyAccess policy attached with grading IAM")
            return True
        else:
            self.print_and_log_error(self.logger,
                                     "[IAM-log] Lambda ReadOnlyAccess policy NOT attached with grading IAM")
            return False

    def validate_iam(self, attached_policies):
        if "IAMReadOnlyAccess" in attached_policies:
            self.print_and_log(self.logger,
                               "[IAM-log] IAMReadOnlyAccess policy attached with grading IAM")
            return True
        else:
            self.print_and_log_error(self.logger,
                                     "[IAM-log] IAMReadOnlyAccess policy NOT attached with grading IAM")
            return False

    def validate_policies(self):
        try:
            attached_policies = self.iam_client.list_attached_user_policies(
                UserName='cse546-AutoGrader',
                MaxItems=100)
            policy_names = [policy['PolicyName']
                            for policy in attached_policies['AttachedPolicies']]
            self.print_and_log(self.logger,
                               f"Following policies are attached with "
                               f"IAM user:cse546-AutoGrader: {policy_names}")

            iam_ro_access_flag = self.validate_iam(policy_names)
            ec2_access_flag = self.validate_ec2(policy_names)
            s3_access_flag = self.validate_s3(policy_names)
            lambda_access_flag = self.validate_lambda(policy_names)

            return (iam_ro_access_flag, ec2_access_flag,
                    s3_access_flag, lambda_access_flag)

        except ClientError as e:
            iam_ro_access_flag = False
            ec2_access_flag = None
            s3_access_flag = None
            lambda_access_flag = None
            self.print_and_log_error(self.logger,
                                     f"Failed to fetch the attached policies. {e}")
            return (iam_ro_access_flag, ec2_access_flag,
                    s3_access_flag, lambda_access_flag)


if __name__ == "__main__":
    import logging
    import argparse

    parser = argparse.ArgumentParser(description='Validate IAM policies')
    parser.add_argument('--access_keyId', type=str,
                        help='ACCESS KEY ID of the grading IAM user')
    parser.add_argument('--access_key', type=str,
                        help='SECRET ACCESS KEY of the grading IAM user')

    log_file = 'autograder.log'
    logging.basicConfig(filename=log_file, level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger()

    args = parser.parse_args()
    iam_obj = iam_policies(logger, args.access_keyId, args.access_key)
    iam_obj.validate_policies()
