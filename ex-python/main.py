# /// script
# requires-python = ">=3.12"
# dependencies = ["boto3"]
# ///

from typing import TypedDict
import boto3
import json
import re
import io
import time


class Result(TypedDict):
    rate_2xx: float
    rate_4xx: float
    rate_5xx: float


def main(input: str) -> Result:
    """Read JSON logs from S3 and compute HTTP status rates, with progress checkpoints."""
    if not input.startswith("s3://"):
        raise ValueError("Input must start with s3://")

    input = input.replace("s3://", "")
    bucket, _, prefix = input.partition("/")
    if prefix and not prefix.endswith("/"):
        prefix += "/"

    s3 = boto3.client("s3")

    total = count_2xx = count_4xx = count_5xx = processed_gb = 0
    start_time = time.time()

    paginator = s3.get_paginator("list_objects_v2")
    files_seen = 0

    print("🔍 Starting analysis...")

    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            size_gb = obj["Size"] / (1024 ** 3)
            processed_gb += size_gb
            files_seen += 1

            response = s3.get_object(Bucket=bucket, Key=key)
            body = response["Body"].read().decode("utf-8")

            for line in io.StringIO(body):
                try:
                    data = json.loads(line.strip())
                    message = data.get("message", "")
                    match = re.search(r"HTTP Status Code: (\d{3})", message)
                    if match:
                        code = int(match.group(1))
                        total += 1
                        if 200 <= code < 300:
                            count_2xx += 1
                        elif 400 <= code < 500:
                            count_4xx += 1
                        elif 500 <= code < 600:
                            count_5xx += 1
                except json.JSONDecodeError:
                    continue

            # Checkpoint every 5 GB processed
            if processed_gb // 5 > (processed_gb - size_gb) // 5:
                elapsed = (time.time() - start_time) / 60
                print(f"⏱️  Checkpoint: ~{int(processed_gb // 5) * 5} GB processed "
                      f"after {elapsed:.2f} min ({files_seen} files).")

    if total == 0:
        return {"rate_2xx": 0.0, "rate_4xx": 0.0, "rate_5xx": 0.0}

    return {
        "rate_2xx": count_2xx / total,
        "rate_4xx": count_4xx / total,
        "rate_5xx": count_5xx / total,
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=str, help="Path to S3 bucket with all data")
    args = parser.parse_args()

    start = time.time()
    result = main(args.input)
    end = time.time()

    print("\n✅ Final results:")
    print(result)
    print(f"🏁 Total elapsed time: {(end - start) / 60:.2f} minutes")
    print("🚀 Done!")
    