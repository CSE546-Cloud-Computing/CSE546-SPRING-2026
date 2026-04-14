"""
File: grade_project2_p2.py
Author: CSE546 Cloud Computing
Description: Grading script for Project-2 Part-2 (Federated Learning
at the Edge with IoT Greengrass + MQTT).

Scoring (100 total):
    Accuracy  (0-50)  tiered by final accuracy
    Speed     (0-50)  tiered by total training time

    Fatal deductions (-100, skip the rest):
      EC2 worker instances do not exist
      Aggregator Lambda not Active / missing
      S3 buckets missing
      Greengrass Core API not accessible
      Fewer than 10 Greengrass core devices, or any not HEALTHY
      Any <ASU-ID>-fl-worker-{0..9}-gg IoT Thing missing

    Deductions:
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
E2E_TIMEOUT = 300  # seconds
GG_INIT_WAIT = 60  # seconds — wait for Greengrass to subscribe after boot

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
    (60,  50),
    (80,  30),
    (100, 15),
]


class grader_project2_p2():

    def __init__(self, logger, asuid, access_keyId, access_key,
                 ec2_access_flag, s3_access_flag, lambda_access_flag,
                 iam_access_flag, iot_access_flag, greengrass_access_flag,
                 num_rounds=NUM_ROUNDS):

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
        self.iot_client = self.iam_session.client("iot")
        self.iot_data_client = self.iam_session.client("iot-data")
        self.greengrass_client = self.iam_session.client("greengrassv2")
        self.logger = logger
        self.asuid = asuid
        self.ec2_access_flag = ec2_access_flag
        self.s3_access_flag = s3_access_flag
        self.lambda_access_flag = lambda_access_flag
        self.iam_access_flag = iam_access_flag
        self.iot_access_flag = iot_access_flag
        self.greengrass_access_flag = greengrass_access_flag
        self.num_rounds = num_rounds

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

    def robust_clean(self, bucket, max_attempts=6, wait=5):
        """Wipe + verify, retrying if Lambda writes more after cleanup.

        Lambda may still be in-flight after the final training round,
        and can write metrics/*.json or models/*.npz AFTER we wipe
        the bucket. Keep wiping and re-checking until the bucket
        stays empty, or give up after max_attempts.
        """
        for attempt in range(max_attempts):
            self.clean_bucket(bucket)
            time.sleep(wait)
            try:
                if self.s3_bucket_is_empty(bucket):
                    self.print_and_log(
                        f"    {bucket} — confirmed empty after "
                        f"{attempt + 1} pass(es)")
                    return True
            except ClientError as e:
                self.print_and_log_warn(
                    f"    {bucket} — emptiness check failed: {e}")
                return False
        self.print_and_log_warn(
            f"    {bucket} — still not empty after "
            f"{max_attempts} passes; giving up")
        return False

    def clean_bucket(self, bucket):
        """Delete every object in the given bucket."""
        try:
            paginator = self.s3_client.get_paginator("list_objects_v2")
            keys = []
            for page in paginator.paginate(Bucket=bucket):
                for obj in page.get("Contents", []):
                    keys.append({"Key": obj["Key"]})
            if keys:
                for i in range(0, len(keys), 1000):
                    self.s3_client.delete_objects(
                        Bucket=bucket,
                        Delete={"Objects": keys[i:i+1000]})
                self.print_and_log(
                    f"    {bucket} — deleted {len(keys)} objects")
            else:
                self.print_and_log(f"    {bucket} — already clean")
        except ClientError as e:
            self.print_and_log_warn(
                f"    {bucket} — cleanup failed: {e}")

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
        """
        deductions = []
        fatal = False

        self.print_and_log(
            "\n  === TC-1: Validate Initial State ===")

        # --- TC-1a: S3 buckets exist + empty ---
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

        # --- TC-1b: EC2 instances exist ---
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

        # --- TC-1c: Lambda function is Active ---
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

        # --- TC-1d: Greengrass Core devices HEALTHY (NEW) ---
        self.print_and_log("\n  TC-1d: Greengrass Core Devices")
        self.print_and_log(f"  {'-' * 50}")

        core_devices = []
        try:
            resp = self.greengrass_client.list_core_devices(
                maxResults=100)
            core_devices = resp.get("coreDevices", [])
            self.print_and_log(
                f"    Greengrass API accessible — "
                f"found {len(core_devices)} core devices:")
            for cd in core_devices:
                name = cd.get("coreDeviceThingName", "?")
                status = cd.get("status", "?")
                self.print_and_log(f"      - {name}: {status}")
        except ClientError as e:
            self.print_and_log_error(
                f"    FATAL: Greengrass API not accessible: {e}")
            deductions.append(
                (100, "Greengrass Core API not accessible"))
            fatal = True

        if not fatal and core_devices:
            expected = {f"{self.asuid}-fl-worker-{i}-gg"
                        for i in range(NUM_CLIENTS)}
            found_names = {cd.get("coreDeviceThingName", "")
                           for cd in core_devices}
            missing = expected - found_names
            if missing:
                self.print_and_log_error(
                    f"    FATAL: Missing core devices: "
                    f"{sorted(missing)}")
                deductions.append(
                    (100, "Fewer than 10 Greengrass core devices"))
                fatal = True
            else:
                unhealthy = [
                    cd.get("coreDeviceThingName", "?")
                    for cd in core_devices
                    if cd.get("coreDeviceThingName", "") in expected
                    and cd.get("status", "") != "HEALTHY"
                ]
                if unhealthy:
                    self.print_and_log_error(
                        f"    FATAL: Core device(s) not HEALTHY: "
                        f"{unhealthy}")
                    deductions.append(
                        (100, "Greengrass core device(s) not HEALTHY"))
                    fatal = True
                else:
                    self.print_and_log(
                        f"    All {NUM_CLIENTS} core devices HEALTHY")

        # --- TC-1e: IoT Things exist (NEW) ---
        self.print_and_log("\n  TC-1e: IoT Things")
        self.print_and_log(f"  {'-' * 50}")
        missing_things = []
        for i in range(NUM_CLIENTS):
            thing_name = f"{self.asuid}-fl-worker-{i}-gg"
            try:
                self.iot_client.describe_thing(thingName=thing_name)
                self.print_and_log(f"    {thing_name}: EXISTS")
            except ClientError:
                self.print_and_log_error(
                    f"    {thing_name}: MISSING")
                missing_things.append(thing_name)
        if missing_things:
            self.print_and_log_error(
                f"    FATAL: {len(missing_things)} IoT Thing(s) missing")
            deductions.append(
                (100, f"IoT Thing(s) missing: {missing_things}"))
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
                return None, f"Missing local file: {local_file}"
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
            self.print_and_log(
                f"    Uploaded {self.global_bucket}:{s3_key}")

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

        if instance_ids:
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

        # --- Step 5: Wait for Greengrass init (NEW) ---
        # Greengrass nucleus needs time to boot, reconnect to IoT Core,
        # and re-subscribe to the MQTT topic after the EC2 instance boots.
        # MQTT QoS 1 does not queue messages for offline subscribers, so
        # we must wait until all workers are listening before we publish.
        self.print_and_log(
            f"\n  Step 5 — Wait for Greengrass init ({GG_INIT_WAIT}s)")
        self.print_and_log(f"  {'-' * 50}")
        time.sleep(GG_INIT_WAIT)
        self.print_and_log("    Greengrass init wait complete")

        # --- Step 6: Publish MQTT trigger for round 0 (NEW) ---
        # The autograder only triggers round 0. The student's aggregator
        # Lambda must publish MQTT for the remaining rounds (self-driving).
        self.print_and_log(
            "\n  Step 6 — Publish MQTT trigger for round 0")
        self.print_and_log(f"  {'-' * 50}")
        topic = f"fl/{self.asuid}/next-round"
        payload = json.dumps({
            "round_number": 0,
            "num_rounds": self.num_rounds,
        })
        start_time = time.time()
        try:
            self.iot_data_client.publish(
                topic=topic, qos=1, payload=payload.encode("utf-8"))
            self.print_and_log(f"    Published to {topic}: {payload}")
        except Exception as e:
            self.print_and_log_error(f"    MQTT publish error: {e}")

        # --- Step 7: Monitor training ---
        self.print_and_log(
            f"\n  Step 7 — Monitor training "
            f"({self.num_rounds} rounds, timeout {E2E_TIMEOUT}s)")
        self.print_and_log(f"  {'-' * 50}")

        seen_rounds = set()
        done = False

        while time.time() - start_time < E2E_TIMEOUT:
            for r in range(self.num_rounds):
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

            if len(seen_rounds) >= self.num_rounds:
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
                f"({len(seen_rounds)}/{self.num_rounds} rounds "
                f"completed)")

        training_time = time.time() - start_time

        # --- Step 8: Stop instances ---
        self.print_and_log("\n  Step 8 — Stop instances")
        self.print_and_log(f"  {'-' * 50}")
        try:
            if instance_ids:
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

        self.print_and_log(
            "\n  === TC-3: Validate FL Artifacts ===")

        for r in range(self.num_rounds):
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
                    f"    Global model (round {r + 1}): FOUND")
            except ClientError:
                self.print_and_log_error(
                    f"    Global model (round {r + 1}): MISSING")
                missing.append(gm_key)

            # Local model updates (.npz per client) — in local-bucket
            local_found = 0
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
                f"    Local models: {local_found}/{NUM_CLIENTS}")

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
                self.print_and_log("    All artifacts present")

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
        for r in range(self.num_rounds):
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
        self.print_and_log(f"    Final Accuracy: {final_acc:.4f}")
        self.print_and_log(f"    Final Loss:     {final_loss:.4f}")

        acc_pts = self.score_accuracy(final_acc)
        self.print_and_log(f"    Score: {acc_pts}/50")

        # --- Accuracy progression ---
        self.print_and_log("\n  TC-4b: Accuracy Progression")
        self.print_and_log(f"  {'-' * 50}")

        if len(history) >= 2:
            accs = [h.get("accuracy", 0) for h in history]
            self.print_and_log("    Round-by-round accuracy:")
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
        """Score training speed (0-50)."""
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

        if training_time < 60:
            tier_desc = "< 60s"
        elif training_time < 80:
            tier_desc = ">= 60s and < 80s"
        elif training_time < 100:
            tier_desc = ">= 80s and < 100s"
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
        self.print_and_log(f"ASUID: {self.asuid}")
        self.print_and_log("-" * 60)

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
            self.print_and_log(
                "\n----------------- Post-run S3 Cleanup "
                "----------------")
            try:
                self.robust_clean(self.global_bucket)
                self.robust_clean(self.local_bucket)
            except Exception as e:
                self.print_and_log_warn(
                    f"  Post-run cleanup error: {e}")
            return test_results

        # =============================================
        # TC-2: FL Execution
        # =============================================
        self.print_and_log(
            "----------------- Executing FL Training "
            "----------------")
        training_time = None
        try:
            training_time, tc2_logs = self.run_e2e_training()
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
            acc_pts, tc4_ded, tc4_logs = self.validate_accuracy()
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
            speed_pts, tc5_logs = self.validate_speed(training_time)
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
        self.print_and_log("    ---")
        self.print_and_log(f"    TOTAL: {total}/100")

        test_results["grade_points"] = total
        self.print_and_log(f"Total Grade Points: {total}")

        # =============================================
        # Post-run cleanup: wipe both buckets so the
        # next run starts from a clean state and TC-1a
        # does not deduct for leftover objects.
        # =============================================
        self.print_and_log(
            "\n----------------- Post-run S3 Cleanup "
            "----------------")
        self.robust_clean(self.global_bucket)
        self.robust_clean(self.local_bucket)

        return test_results


if __name__ == "__main__":
    import logging
    import argparse

    parser = argparse.ArgumentParser(
        description='FL (Part 2) Grading Script')
    parser.add_argument('--access_keyId', type=str,
                        help='ACCESS KEY ID')
    parser.add_argument('--access_key', type=str,
                        help='SECRET ACCESS KEY')
    parser.add_argument('--asuid', type=str,
                        help='ASUID of the student')
    parser.add_argument('--num_rounds', type=int, default=NUM_ROUNDS,
                        help='Number of FL rounds')

    log_file = 'autograder.log'
    logging.basicConfig(
        filename=log_file, level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger()

    args = parser.parse_args()
    aws_obj = grader_project2_p2(
        logger, args.asuid,
        args.access_keyId, args.access_key,
        True, True, True, True, True, True,
        num_rounds=args.num_rounds)
    aws_obj.main()
