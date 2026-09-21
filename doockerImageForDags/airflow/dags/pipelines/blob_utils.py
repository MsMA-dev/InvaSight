import json

from airflow.providers.microsoft.azure.hooks.wasb import WasbHook


WASB_CONN_ID = "wasb_default"
CONTAINER_NAME = "invasight-data"


def upload_json_to_blob(data, blob_name):
    WasbHook(wasb_conn_id=WASB_CONN_ID).load_string(
        string_data=json.dumps(data),
        container_name=CONTAINER_NAME,
        blob_name=blob_name,
        overwrite=True,
    )
    print(f"Uploaded to blob {CONTAINER_NAME}/{blob_name}")


def upload_file_to_blob(file_path, blob_name):
    WasbHook(wasb_conn_id=WASB_CONN_ID).load_file(
        file_path=file_path,
        container_name=CONTAINER_NAME,
        blob_name=blob_name,
        overwrite=True,
    )
    print(f"Uploaded to blob {CONTAINER_NAME}/{blob_name}")
