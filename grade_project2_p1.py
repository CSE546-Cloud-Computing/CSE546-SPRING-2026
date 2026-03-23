"""
File: grade_project2_p1.py
Author: CSE546 Cloud Computing
Description: Grading script for Project-2 Part-1 (Federated Learning)

Scoring (100 total):
    Accuracy  (0-50)  tiered by final accuracy
    Speed     (0-50)  tiered by total training time

    Deductions:
      -100  EC2 worker instances do not exist (fatal)
      -100  Aggregator Lambda not Active (fatal)
       -10  Any S3 bucket not empty at start
       -10  Any worker instance not in stopped state at start
       -10  Per round missing any FL artifact
       -10  Per round accuracy regression (acc[i] < acc[i-1])

    Final = Accuracy + Speed - Deductions, min 0
"""

import os
import json
import time
import boto3
from botocore.exceptions import ClientError

# ============================================================================
# Constants
# ============================================================================
REGION = "us-west-2"
FUNCTION_NAME = "fl-aggregator"

# S3 key prefixes
MODELS_PREFIX = "models/"
UPDATES_PREFIX = "updates/"
METRICS_PREFIX = "metrics/"

# Local data files bundled with the grader (in data/ directory)
# All uploaded to global-bucket (Lambda reads test data, workers read model)
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
LOCAL_DATA_FILES = {
    "labels.csv": "labels.csv",
    "test.tar.gz": "archives/test.tar.gz",
    "initial_model.npz": "models/global_model_round_0.npz",
}

# Training parameters
NUM_ROUNDS = 5
NUM_CLIENTS = 10
E2E_TIMEOUT = 100  # seconds — training typically completes in ~30s

# Accuracy tiers: (threshold, points)
ACCURACY_TIERS = [
    (0.90, 50),
    (0.80, 40),
    (0.70, 30),
    (0.60, 20),
    (0.50, 10),
]

# Speed tiers: (max_seconds, points)
SPEED_TIERS = [
    (50, 50),
    (75, 30),
    (100, 15),
]


class grader_project2_p1():

    def __init__(self, logger, asuid, access_keyId, access_key,
                 ec2_access_flag, s3_access_flag, lambda_access_flag,
                 iam_access_flag):

        self.iam_access_keyId = access_keyId
        self.iam_secret_access_key = access_key
        self.iam_session = boto3.Session(
            aws_access_key_id=self.iam_access_keyId,
            aws_secret_access_key=self.iam_secret_access_key,
            region_name=REGION,
        )
        self.s3_client = self.iam_session.client("s3")
        self.ec2_client = self.iam_session.client("ec2")
        self.lambda_client = self.iam_session.client("lambda")
        self.logger = logger
        self.asuid = asuid
        self.ec2_access_flag = ec2_access_flag
        self.s3_access_flag = s3_access_flag
        self.lambda_access_flag = lambda_access_flag
        self.iam_access_flag = iam_access_flag

        self.local_bucket = f"{asuid}-local-bucket"
        self.global_bucket = f"{asuid}-global-bucket"

    # ========================================================================
    # Helpers
    # ========================================================================
    def print_and_log(self, message):
        print(message)
        self.logger.info(message)

    def print_and_log_error(self, message):
        print(message)
        self.logger.error(message)

    def print_and_log_warn(self, message):
        print(message)
        self.logger.warning(message)

    def s3_bucket_is_empty(self, bucket):
        resp = self.s3_client.list_objects_v2(Bucket=bucket, MaxKeys=1)
        return resp.get("KeyCount", 0) == 0

    def clean_s3_prefixes(self, bucket, prefixes):
        for prefix in prefixes:
            paginator = self.s3_client.get_paginator("list_objects_v2")
            keys = []
            for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
                for obj in page.get("Contents", []):
                    keys.append({"Key": obj["Key"]})
            label = f"{bucket}:{prefix if prefix else '(root)'}"
            if keys:
                for i in range(0, len(keys), 1000):
                    self.s3_client.delete_objects(
                        Bucket=bucket,
                        Delete={"Objects": keys[i:i+1000]})
                self.print_and_log(
                    f"    {label} — deleted {len(keys)} objects")
            else:
                self.print_and_log(
                    f"    {label} — already clean")

    @staticmethod
    def score_accuracy(final_acc):
        for threshold, pts in ACCURACY_TIERS:
            if final_acc > threshold:
                return pts
        return 0

    @staticmethod
    def score_speed(training_time):
        for max_secs, pts in SPEED_TIERS:
            if training_time < max_secs:
                return pts
        return 0

    # ========================================================================
    # TC-1: Validate Initial State
    # ========================================================================
    def validate_initial_state(self):
        """Validate initial state of resources.

        Returns (deduction_points, comments, is_fatal).
        deduction_points: total points deducted (positive number).
        """
        deductions = []
        fatal = False
        comments = ""

        self.print_and_log(
            "\n  === TC-1: Validate Initial State ===")

        # --- Check S3 buckets exist ---
        self.print_and_log("\n  TC-1a: S3 Buckets")
        self.print_and_log(f"  {'-' * 50}")
        buckets_exist = True
        for bname, label in [(self.local_bucket, "local-bucket"),
                             (self.global_bucket, "global-bucket")]:
            try:
                self.s3_client.head_bucket(Bucket=bname)
                empty = self.s3_bucket_is_empty(bname)
                status = "EXISTS, empty" if empty else "EXISTS, NOT EMPTY"
                self.print_and_log(f"    {label} ({bname}): {status}")
                if not empty:
                    deductions.append((10, f"{label} is not empty"))
            except ClientError:
                self.print_and_log_error(
                    f"    {label} ({bname}): MISSING")
                buckets_exist = False

        if not buckets_exist:
            self.print_and_log_error(
                "    FATAL: S3 buckets missing — cannot proceed")
            deductions.append((100, "S3 buckets do not exist"))
            fatal = True

        # --- Check EC2 instances exist ---
        self.print_and_log("\n  TC-1b: EC2 Instances")
        self.print_and_log(f"  {'-' * 50}")

        resp = self.ec2_client.describe_instances(
            Filters=[
                {"Name": "tag:Name",
                 "Values": [f"{self.asuid}-fl-worker-*"]},
                {"Name": "instance-state-name",
                 "Values": ["running", "stopped", "pending", "stopping"]},
            ]
        )
        instances = []
        for res in resp["Reservations"]:
            for inst in res["Instances"]:
                name = ""
                for t in inst.get("Tags", []):
                    if t["Key"] == "Name":
                        name = t["Value"]
                instances.append({
                    "id": inst["InstanceId"],
                    "name": name,
                    "state": inst["State"]["Name"],
                    "type": inst["InstanceType"],
                })
        instances.sort(key=lambda x: x["name"])

        self.print_and_log(
            f"    Found {len(instances)} "
            f"{self.asuid}-fl-worker instances")
        for inst in instances:
            self.print_and_log(
                f"    {inst['name']} ({inst['id']}) — "
                f"{inst['state']} ({inst['type']})")

        if len(instances) < NUM_CLIENTS:
            self.print_and_log_error(
                f"    FATAL: Expected {NUM_CLIENTS} instances, "
                f"found {len(instances)}")
            deductions.append((100, "Worker instances do not exist"))
            fatal = True
        else:
            not_stopped = [i for i in instances
                           if i["state"] != "stopped"]
            if not_stopped:
                self.print_and_log_warn(
                    f"    DEDUCTION: {len(not_stopped)} instances "
                    f"not in stopped state")
                deductions.append(
                    (10, "Worker instances not all stopped"))

        # --- Check Lambda function is Active ---
        self.print_and_log("\n  TC-1c: Lambda Function")
        self.print_and_log(f"  {'-' * 50}")

        try:
            resp = self.lambda_client.get_function(
                FunctionName=FUNCTION_NAME)
            cfg = resp["Configuration"]
            state = cfg.get("State", "Unknown")
            self.print_and_log(
                f"    Lambda '{FUNCTION_NAME}': "
                f"ARN={cfg['FunctionArn']}")
            self.print_and_log(f"    State: {state}")
            self.print_and_log(
                f"    Memory: {cfg.get('MemorySize', 0)} MB")
            env_vars = cfg.get("Environment", {}).get("Variables", {})
            self.print_and_log(
                f"    Env: NUM_CLIENTS="
                f"{env_vars.get('NUM_CLIENTS')}, "
                f"TOTAL_ROUNDS={env_vars.get('TOTAL_ROUNDS')}")

            if state != "Active":
                self.print_and_log_error(
                    f"    FATAL: Lambda state is '{state}', "
                    f"expected 'Active'")
                deductions.append(
                    (100, "Aggregator Lambda not Active"))
                fatal = True
        except ClientError:
            self.print_and_log_error(
                f"    FATAL: Lambda '{FUNCTION_NAME}' NOT FOUND")
            deductions.append(
                (100, "Aggregator Lambda does not exist"))
            fatal = True

        # Summary
        total_ded = sum(d[0] for d in deductions)
        self.print_and_log(f"\n  TC-1 Deductions: -{total_ded}")
        if fatal:
            self.print_and_log_error(
                "  TC-1: FATAL — grading stops here")

        comments = "; ".join(
            f"-{d[0]}: {d[1]}" for d in deductions
        ) if deductions else "No deductions"

        return total_ded, comments, fatal

    # ========================================================================
    # TC-2: FL Execution (run training)
    # ========================================================================
    def run_e2e_training(self):
        """Run federated learning training.

        Returns (training_time, comments).
        training_time: seconds elapsed, or None if failed/timed out.
        """
        comments = ""

        self.print_and_log("\n  === TC-2: FL Execution ===")

        # --- Step 1: Verify local data files ---
        self.print_and_log("\n  Step 1 — Verify local data files")
        self.print_and_log(f"  {'-' * 50}")
        for local_file in LOCAL_DATA_FILES:
            path = os.path.join(DATA_DIR, local_file)
            if not os.path.isfile(path):
                self.print_and_log_error(
                    f"    FAIL: {local_file} not found at {path}")
                return None, None, f"Missing local file: {local_file}"
            size_kb = os.path.getsize(path) / 1024
            self.print_and_log(f"    {local_file}: {size_kb:.1f} KB")

        # --- Step 2: Clean S3 buckets ---
        self.print_and_log("\n  Step 2 — Clean S3 buckets")
        self.print_and_log(f"  {'-' * 50}")
        self.clean_s3_prefixes(self.global_bucket, [
            METRICS_PREFIX, MODELS_PREFIX,
        ])
        self.clean_s3_prefixes(self.local_bucket, [
            UPDATES_PREFIX,
        ])

        # --- Step 3: Upload data files (all to global-bucket) ---
        self.print_and_log("\n  Step 3 — Upload data files")
        self.print_and_log(f"  {'-' * 50}")

        for local_file, s3_key in LOCAL_DATA_FILES.items():
            path = os.path.join(DATA_DIR, local_file)
            with open(path, "rb") as f:
                data = f.read()
            self.s3_client.put_object(
                Bucket=self.global_bucket, Key=s3_key, Body=data)
            self.print_and_log(f"    Uploaded {self.global_bucket}:{s3_key}")

        # --- Step 4: Start instances ---
        self.print_and_log("\n  Step 4 — Start client instances")
        self.print_and_log(f"  {'-' * 50}")

        resp = self.ec2_client.describe_instances(
            Filters=[
                {"Name": "tag:Name",
                 "Values": [f"{self.asuid}-fl-worker-*"]},
                {"Name": "instance-state-name",
                 "Values": ["stopped"]},
            ]
        )
        instances = []
        for res in resp["Reservations"]:
            for inst in res["Instances"]:
                name = ""
                for t in inst.get("Tags", []):
                    if t["Key"] == "Name":
                        name = t["Value"]
                instances.append({
                    "id": inst["InstanceId"], "name": name})

        instances.sort(key=lambda x: x["name"])
        instances = instances[:NUM_CLIENTS]
        instance_ids = [inst["id"] for inst in instances]

        for inst in instances:
            self.print_and_log(
                f"    {inst['name']} ({inst['id']})")

        self.ec2_client.start_instances(InstanceIds=instance_ids)
        self.print_and_log(
            f"    Starting {len(instance_ids)} instances ...")

        waiter = self.ec2_client.get_waiter("instance_running")
        try:
            waiter.wait(InstanceIds=instance_ids)
            self.print_and_log("    All instances running.")
        except Exception as e:
            self.print_and_log_warn(
                f"    WARN: Error waiting for instances: {e}")

        # --- Step 5: Monitor training ---
        self.print_and_log(
            f"\n  Step 5 — Monitor training "
            f"({NUM_ROUNDS} rounds, timeout {E2E_TIMEOUT}s)")
        self.print_and_log(f"  {'-' * 50}")

        start_time = time.time()
        seen_rounds = set()
        done = False

        while time.time() - start_time < E2E_TIMEOUT:
            for r in range(NUM_ROUNDS):
                if r in seen_rounds:
                    continue
                try:
                    resp = self.s3_client.get_object(
                        Bucket=self.global_bucket,
                        Key=f"{METRICS_PREFIX}round_{r}.json",
                    )
                    metrics = json.loads(
                        resp["Body"].read().decode())
                    seen_rounds.add(r)
                    elapsed = time.time() - start_time
                    self.print_and_log(
                        f"    Round {r}: "
                        f"accuracy="
                        f"{metrics.get('accuracy', 0):.4f}, "
                        f"loss={metrics.get('loss', 0):.4f} "
                        f"({elapsed:.1f}s)")
                except ClientError:
                    break

            if len(seen_rounds) >= NUM_ROUNDS:
                elapsed = time.time() - start_time
                self.print_and_log(
                    f"    Training complete in {elapsed:.1f}s")
                done = True
                break

            time.sleep(5)

        if not done:
            elapsed = time.time() - start_time
            self.print_and_log(
                f"    TIMEOUT after {elapsed:.1f}s "
                f"({len(seen_rounds)}/{NUM_ROUNDS} rounds "
                f"completed)")

        training_time = time.time() - start_time

        # --- Step 6: Stop instances ---
        self.print_and_log("\n  Step 6 — Stop instances")
        self.print_and_log(f"  {'-' * 50}")
        try:
            self.ec2_client.stop_instances(InstanceIds=instance_ids)
            self.print_and_log(
                f"    Stopping {len(instance_ids)} instances ...")
            stop_waiter = self.ec2_client.get_waiter(
                "instance_stopped")
            stop_waiter.wait(InstanceIds=instance_ids)
            self.print_and_log("    All instances stopped.")
        except Exception as e:
            self.print_and_log_warn(
                f"    WARN: Error stopping instances: {e}")

        comments = f"Training time: {training_time:.1f}s"
        return training_time, comments

    # ========================================================================
    # TC-3: Validate FL Artifacts
    # ========================================================================
    def validate_artifacts(self):
        """Check per-round FL artifacts in S3.

        Returns (deduction_points, comments).
        -10 per round missing any artifact.
        """
        deductions = []
        comments = ""

        self.print_and_log(
            "\n  === TC-3: Validate FL Artifacts ===")

        for r in range(NUM_ROUNDS):
            self.print_and_log(f"\n  Round {r}:")
            self.print_and_log(f"  {'-' * 50}")
            missing = []

            # Global model (round N produces round_{N+1})
            gm_key = (f"{MODELS_PREFIX}"
                       f"global_model_round_{r + 1}.npz")
            try:
                self.s3_client.head_object(
                    Bucket=self.global_bucket, Key=gm_key)
                self.print_and_log(
                    f"    Global model (round {r+1}): FOUND")
            except ClientError:
                self.print_and_log_error(
                    f"    Global model (round {r+1}): MISSING")
                missing.append(gm_key)

            # Local model updates (.npz per client) — in local-bucket
            local_found = 0
            local_expected = NUM_CLIENTS
            for c in range(NUM_CLIENTS):
                key = (f"{UPDATES_PREFIX}"
                       f"local_model_round_{r}"
                       f"_worker_{c}.npz")
                try:
                    self.s3_client.head_object(
                        Bucket=self.local_bucket, Key=key)
                    local_found += 1
                except ClientError:
                    missing.append(key)
            self.print_and_log(
                f"    Local models: "
                f"{local_found}/{local_expected}")

            # Round metrics
            met_key = f"{METRICS_PREFIX}round_{r}.json"
            try:
                self.s3_client.head_object(
                    Bucket=self.global_bucket, Key=met_key)
                self.print_and_log(
                    f"    Metrics (round_{r}.json): FOUND")
            except ClientError:
                self.print_and_log_error(
                    f"    Metrics (round_{r}.json): MISSING")
                missing.append(met_key)

            if missing:
                self.print_and_log_warn(
                    f"    DEDUCTION: -10 (missing "
                    f"{len(missing)} artifact(s))")
                deductions.append(
                    (10, f"Round {r}: missing "
                         f"{len(missing)} artifact(s)"))
            else:
                self.print_and_log(
                    "    All artifacts present")

        total_ded = sum(d[0] for d in deductions)
        self.print_and_log(f"\n  TC-3 Deductions: -{total_ded}")

        comments = "; ".join(
            f"-{d[0]}: {d[1]}" for d in deductions
        ) if deductions else "No deductions"

        return total_ded, comments

    # ========================================================================
    # TC-4: Validate Model Accuracy
    # ========================================================================
    def validate_accuracy(self):
        """Score final accuracy (0-50) and check progression.

        Reads individual round metrics from S3.
        Returns (accuracy_pts, deduction_points, comments).
        """
        deductions = []

        self.print_and_log(
            "\n  === TC-4: Validate Model Accuracy ===")

        # Read per-round metrics from S3
        history = []
        schema_errors = []
        for r in range(NUM_ROUNDS):
            try:
                resp = self.s3_client.get_object(
                    Bucket=self.global_bucket,
                    Key=f"{METRICS_PREFIX}round_{r}.json")
                raw = resp["Body"].read().decode()
                try:
                    metrics = json.loads(raw)
                except json.JSONDecodeError:
                    self.print_and_log_error(
                        f"    round_{r}.json: invalid JSON")
                    schema_errors.append(r)
                    continue
                # Validate schema: must have round, accuracy, loss
                missing_keys = []
                for key in ("round", "accuracy", "loss"):
                    if key not in metrics:
                        missing_keys.append(key)
                if missing_keys:
                    self.print_and_log_error(
                        f"    round_{r}.json: missing keys "
                        f"{missing_keys} — expected "
                        f"{{\"round\": int, \"accuracy\": "
                        f"float, \"loss\": float}}")
                    schema_errors.append(r)
                    continue
                history.append(metrics)
            except ClientError:
                self.print_and_log_warn(
                    f"    round_{r}.json not found")

        if schema_errors:
            self.print_and_log_warn(
                f"    Schema errors in rounds: "
                f"{schema_errors}. Expected format: "
                f"{{\"round\": int, \"accuracy\": float, "
                f"\"loss\": float}}")

        if not history:
            self.print_and_log(
                "    No valid round metrics available — "
                "cannot validate accuracy")
            self.print_and_log("    Accuracy: 0/50")
            return 0, 0, "No valid round metrics"

        final_acc = history[-1].get("accuracy", 0)
        final_loss = history[-1].get("loss", 0)

        # --- Final accuracy (tiered) ---
        self.print_and_log("\n  TC-4a: Final Accuracy")
        self.print_and_log(f"  {'-' * 50}")
        self.print_and_log(
            f"    Final Accuracy: {final_acc:.4f}")
        self.print_and_log(
            f"    Final Loss:     {final_loss:.4f}")

        acc_pts = self.score_accuracy(final_acc)
        self.print_and_log(f"    Score: {acc_pts}/50")

        # --- Accuracy progression ---
        self.print_and_log("\n  TC-4b: Accuracy Progression")
        self.print_and_log(f"  {'-' * 50}")

        if len(history) >= 2:
            accs = [h.get("accuracy", 0) for h in history]
            self.print_and_log(
                "    Round-by-round accuracy:")
            for h in history:
                self.print_and_log(
                    f"      Round {h.get('round', '?')}: "
                    f"acc={h.get('accuracy', 0):.4f}, "
                    f"loss={h.get('loss', 0):.4f}")

            for i in range(1, len(accs)):
                if accs[i] < accs[i - 1]:
                    self.print_and_log_warn(
                        f"    DEDUCTION: -10 "
                        f"(Round {i} acc {accs[i]:.4f} < "
                        f"Round {i-1} acc "
                        f"{accs[i-1]:.4f})")
                    deductions.append(
                        (10, f"Round {i} accuracy regression: "
                             f"{accs[i]:.4f} < "
                             f"{accs[i-1]:.4f}"))
        else:
            self.print_and_log(
                f"    Insufficient history "
                f"({len(history)} entries)")

        total_ded = sum(d[0] for d in deductions)
        self.print_and_log(
            f"\n  TC-4 Score: {acc_pts}/50, "
            f"Deductions: -{total_ded}")

        comments = f"Accuracy={final_acc:.4f} ({acc_pts}/50)"
        if deductions:
            comments += "; " + "; ".join(
                f"-{d[0]}: {d[1]}" for d in deductions)

        return acc_pts, total_ded, comments

    # ========================================================================
    # TC-5: Validate Training Speed
    # ========================================================================
    def validate_speed(self, training_time):
        """Score training speed (0-20).

        Returns (speed_pts, comments).
        """
        self.print_and_log(
            "\n  === TC-5: Validate Training Speed ===")
        self.print_and_log(f"  {'-' * 50}")

        if training_time is None:
            self.print_and_log(
                "    Training did not complete — "
                "speed score: 0/50")
            return 0, "Training did not complete"

        speed_pts = self.score_speed(training_time)
        self.print_and_log(
            f"    Training time: {training_time:.1f}s")
        self.print_and_log(f"    Score: {speed_pts}/50")

        if training_time < 50:
            tier_desc = "< 50s"
        elif training_time < 75:
            tier_desc = ">= 50s and < 75s"
        elif training_time < 100:
            tier_desc = ">= 75s and < 100s"
        else:
            tier_desc = ">= 100s"
        self.print_and_log(f"    Tier: {tier_desc}")

        return speed_pts, \
            f"Time={training_time:.1f}s ({speed_pts}/50)"

    # ========================================================================
    # Main
    # ========================================================================
    def main(self):
        """Run all test cases and return results dict."""
        test_results = {}

        self.print_and_log(
            "-------------- CSE546 Cloud Computing "
            "Grading Console -----------")
        self.print_and_log(
            f"IAM ACCESS KEY ID: {self.iam_access_keyId}")
        self.print_and_log(
            f"ASUID: {self.asuid}")
        self.print_and_log(
            "-" * 60)

        # =============================================
        # TC-1: Validate Initial State
        # =============================================
        self.print_and_log(
            "----------------- Checking The Initial State "
            "----------------")
        all_deductions = []
        fatal = False

        try:
            tc1_ded, tc1_logs, fatal = \
                self.validate_initial_state()
            all_deductions.append(tc1_ded)
            test_results["tc_1"] = (-tc1_ded, tc1_logs)
        except Exception as e:
            fatal = True
            self.print_and_log_error(f"  TC-1 ERROR: {e}")
            all_deductions.append(100)
            test_results["tc_1"] = (-100, f"TC-1 error: {e}")

        self.print_and_log(
            f"  TC-1 Total Deductions: "
            f"-{sum(all_deductions)}")

        if fatal:
            total = 0
            test_results["tc_2"] = (0, "Skipped (fatal)")
            test_results["tc_3"] = (0, "Skipped (fatal)")
            test_results["tc_4"] = (0, "Skipped (fatal)")
            test_results["tc_5"] = (0, "Skipped (fatal)")
            test_results["grade_points"] = total
            self.print_and_log(
                f"\n  TOTAL: {total}/100 "
                f"(fatal deduction, skipping E2E)")
            return test_results

        # =============================================
        # TC-2: FL Execution
        # =============================================
        self.print_and_log(
            "----------------- Executing FL Training "
            "----------------")
        training_time = None
        try:
            training_time, tc2_logs = \
                self.run_e2e_training()
            test_results["tc_2"] = (0, tc2_logs)
        except Exception as e:
            self.print_and_log_error(f"  TC-2 ERROR: {e}")
            test_results["tc_2"] = (0, f"TC-2 error: {e}")

        # =============================================
        # TC-3: Validate FL Artifacts
        # =============================================
        self.print_and_log(
            "----------------- Checking Training Artifacts "
            "----------------")
        try:
            tc3_ded, tc3_logs = self.validate_artifacts()
            all_deductions.append(tc3_ded)
            test_results["tc_3"] = (-tc3_ded, tc3_logs)
        except Exception as e:
            self.print_and_log_error(f"  TC-3 ERROR: {e}")
            test_results["tc_3"] = (0, f"TC-3 error: {e}")

        # =============================================
        # TC-4: Validate Model Accuracy
        # =============================================
        self.print_and_log(
            "----------------- Checking Model Accuracy "
            "----------------")
        acc_pts = 0
        try:
            acc_pts, tc4_ded, tc4_logs = \
                self.validate_accuracy()
            all_deductions.append(tc4_ded)
            test_results["tc_4"] = (acc_pts, tc4_logs)
        except Exception as e:
            self.print_and_log_error(f"  TC-4 ERROR: {e}")
            test_results["tc_4"] = (0, f"TC-4 error: {e}")

        # =============================================
        # TC-5: Validate Training Speed
        # =============================================
        self.print_and_log(
            "----------------- Checking Training Speed "
            "----------------")
        speed_pts = 0
        try:
            speed_pts, tc5_logs = \
                self.validate_speed(training_time)
            test_results["tc_5"] = (speed_pts, tc5_logs)
        except Exception as e:
            self.print_and_log_error(f"  TC-5 ERROR: {e}")
            test_results["tc_5"] = (0, f"TC-5 error: {e}")

        # =============================================
        # Final Score
        # =============================================
        total_ded = sum(all_deductions)
        total = max(0, acc_pts + speed_pts - total_ded)

        self.print_and_log(f"\n  {'=' * 50}")
        self.print_and_log("  SCORE BREAKDOWN:")
        self.print_and_log(f"    Accuracy:   {acc_pts}/50")
        self.print_and_log(f"    Speed:      {speed_pts}/50")
        self.print_and_log(f"    Deductions: -{total_ded}")
        self.print_and_log(f"    ---")
        self.print_and_log(f"    TOTAL: {total}/100")

        test_results["grade_points"] = total
        self.print_and_log(
            f"Total Grade Points: {total}")

        return test_results


if __name__ == "__main__":
    import logging
    import argparse

    parser = argparse.ArgumentParser(
        description='FL Grading Script')
    parser.add_argument('--access_keyId', type=str,
                        help='ACCESS KEY ID')
    parser.add_argument('--access_key', type=str,
                        help='SECRET ACCESS KEY')
    parser.add_argument('--asuid', type=str,
                        help='ASUID of the student')

    log_file = 'autograder.log'
    logging.basicConfig(
        filename=log_file, level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger()

    args = parser.parse_args()
    aws_obj = grader_project2_p1(
        logger, args.asuid,
        args.access_keyId, args.access_key,
        True, True, True, True)
    aws_obj.main()
