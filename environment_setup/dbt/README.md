# dbt Environment Setup

This document describes the dbt installation and environment setup performed on `Worker01` for the InvaSight project.

## Environment

- Server: Worker01
- User: ubuntu
- Python virtual environment: `/home/ubuntu/.venvs/dbt`
- dbt executable: `/home/ubuntu/.venvs/dbt/bin/dbt`

## Installation Process

### 1. Install Python package and virtual environment support

```bash
sudo apt install -y python3-pip
sudo apt install -y python3-venv
```

### 2. Create a dedicated virtual environment for dbt

```bash
mkdir -p ~/.venvs
python3 -m venv ~/.venvs/dbt
```

### 3. Activate the dbt virtual environment

```bash
source ~/.venvs/dbt/bin/activate
```

### 4. Verify the Python environment

```bash
which python
which pip
python --version
pip --version
```

### 5. Install dbt Core

```bash
python -m pip install dbt-core
```

### 6. Install the Snowflake adapter

```bash
python -m pip install dbt-snowflake
```

### 7. Verify the dbt installation

```bash
which dbt
dbt --version
```

## Verified Installation

The environment was verified on Worker01 with:

- dbt Core: `1.12.4`
- dbt Snowflake adapter: `1.12.0`
- dbt executable: `/home/ubuntu/.venvs/dbt/bin/dbt`

## Security

No passwords, API keys, private keys, Snowflake credentials, or other secrets are stored in this repository.

The local dbt profile file located at:

```text
/home/ubuntu/.dbt/profiles.yml
```

is intentionally excluded from this repository because it may contain environment-specific connection configuration and sensitive credentials.
