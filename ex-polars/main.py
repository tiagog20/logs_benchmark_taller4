# /// script
# requires-python = ">=3.12"
# dependencies = ["polars", "boto3"]
# ///

from typing import TypedDict
import Polars as pl
import boto3
import io
import json
import time


class Result(TypedDict):
    rate_2xx: float
    rate_4xx: float
    rate_5xx: float


def main(input: str) -> Result:
    """Read JSON logs from S3 using Polars and compute HTTP status rates."""
    if not input.startswith("s3://"):
        raise ValueError("Input must start with s3://")

    input = input.replace("s3://", "")
    bucket, _, prefix = input.partition("/")
    if prefix and not prefix.endswith("/"):
        prefix += "/"

    s3 = boto3.client("s3")
    paginator = s3.get_paginator("list_objects_v2")

    total = count_2xx = count_4xx = count_5xx = processed_gb = 0
    start_time = time.time()

    print("⚡ Starting Polars benchmark...")

    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            size_gb = obj["Size"] / (1024 ** 3)
            processed_gb += size_gb

            # Stream the file from S3
            response = s3.get_object(Bucket=bucket, Key=key)
            body = response["Body"].read().decode("utf-8")

            # Load directly into Polars DataFrame
            df = pl.read_ndjson(io.StringIO(body))

            # Extract HTTP code efficiently with regex
            df = df.with_columns(
                pl.col("message")
                .str.extract(r"HTTP Status Code: (\d{3})")
                .cast(pl.Int32)
                .alias("status")
            )

            total += df.height
            count_2xx += df.filter((pl.col("status") >= 200) & (pl.col("status") < 300)).height
            count_4xx += df.filter((pl.col("status") >= 400) & (pl.col("status") < 500)).height
            count_5xx += df.filter((pl.col("status") >= 500) & (pl.col("status") < 600)).height

            # Progress every 5 GB
            if processed_gb // 5 > (processed_gb - size_gb) // 5:
                elapsed = (time.time() - start_time) / 60
                print(f"⏱️  Checkpoint: ~{int(processed_gb // 5) * 5} GB processed after {elapsed:.2f} min.")

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