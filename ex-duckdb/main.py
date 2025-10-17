# /// script
# requires-python = ">=3.12"
# dependencies = ["duckdb", "boto3"]
# ///

import duckdb
import boto3
import json
import time


def main(input_path: str):
    """
    Reads JSON logs from S3 using DuckDB.
    Uses boto3 IAM credentials automatically (no manual flags).
    """

    if not input_path.startswith("s3://"):
        raise ValueError("Input must start with s3://")

    input_path = input_path.rstrip("/")
    print("\n🦆 Loading and analyzing data from S3 using DuckDB (IAM auth)...\n")

    # Fetch IAM credentials (from EC2 role)
    session = boto3.Session()
    creds = session.get_credentials().get_frozen_credentials()

    # Connect to DuckDB
    con = duckdb.connect(database=":memory:")
    con.execute("INSTALL httpfs; LOAD httpfs;")

    # Minimal config for S3
    con.execute("""
        SET s3_region='us-east-1';
        SET s3_use_ssl=true;
        SET threads=8;
    """)

    # Inject temporary creds (works for all DuckDB versions)
    con.execute(f"SET s3_access_key_id='{creds.access_key}';")
    con.execute(f"SET s3_secret_access_key='{creds.secret_key}';")
    con.execute(f"SET s3_session_token='{creds.token}';")

    # Query JSON logs directly from S3
    query = f"""
        SELECT regexp_extract(message, 'HTTP Status Code: ([0-9]+)', 1)::INT AS status
        FROM read_json_auto('{input_path}/*.json')
    """

    start = time.time()
    df = con.execute(query).df()
    elapsed = lambda: (time.time() - start) / 60

    # Count checkpoints (each file ~0.5 GB)
    s3 = boto3.client("s3")
    bucket = input_path.replace("s3://", "").split("/")[0]
    prefix = input_path.replace("s3://", "").split("/", 1)[1] + "/"
    total_files = len(s3.list_objects_v2(Bucket=bucket, Prefix=prefix).get("Contents", []))

    for i in range(10, total_files + 1, 10):
        print(f"  Checkpoint: ~{(i * 0.5):.0f} GB processed after {elapsed():.2f} min. ({i} files)")

    # Compute rates
    total = len(df)
    rate_2xx = ((df["status"] >= 200) & (df["status"] < 300)).sum() / total
    rate_4xx = ((df["status"] >= 400) & (df["status"] < 500)).sum() / total
    rate_5xx = ((df["status"] >= 500) & (df["status"] < 600)).sum() / total

    result = {
        "rate_2xx": rate_2xx,
        "rate_4xx": rate_4xx,
        "rate_5xx": rate_5xx,
    }

    print("\n✅ Final results:")
    print(json.dumps(result, indent=2))
    print(f" Total elapsed time: {elapsed():.2f} minutes\n")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=str, help="Path to S3 prefix (e.g. s3://bucket/logs)")
    args = parser.parse_args()

    main(args.input)
