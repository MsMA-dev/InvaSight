DBT_SSH_CONN = "dbt_ec2_ssh"
DBT_POOL = "dbt_ssh_pool"

# dev_env.sh activates the dbt-env venv, cds into the project, and exports
# Snowflake creds pulled from AWS Secrets Manager. It must be sourced (not
# executed) so those exports land in the same shell that runs `dbt build`.
DBT_ENV_SCRIPT = "/home/ubuntu/invasight_pipeline/dev_env.sh"


# clean + deps on every run: teammates work in the same project folder and
# dbt_packages/ keeps getting wiped, which fails the build with exit status 2.
def dbt_build_cmd(*select_args):
    select = " ".join(select_args)
    return (
        f". {DBT_ENV_SCRIPT} && dbt clean && dbt deps"
        f" && dbt build --full-refresh --select {select}"
    )
