import json

from airflow.providers.amazon.aws.hooks.s3 import S3Hook


AWS_CONN_ID = "aws_default"
S3_BUCKET = "invasight"


def upload_json_to_s3(data, key):
    S3Hook(aws_conn_id=AWS_CONN_ID).load_string(
        string_data=json.dumps(data),
        key=key,
        bucket_name=S3_BUCKET,
        replace=True,
    )
    print(f"Uploaded to s3://{S3_BUCKET}/{key}")


def upload_file_to_s3(file_path, key):
    S3Hook(aws_conn_id=AWS_CONN_ID).load_file(
        filename=file_path,
        key=key,
        bucket_name=S3_BUCKET,
        replace=True,
    )
    print(f"Uploaded to s3://{S3_BUCKET}/{key}")
