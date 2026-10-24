#
#  GoogleFindMyTools - A set of tools to interact with the Google Find My API
#  Copyright © 2024 Leon Böttger. All rights reserved.
#

import json
import os

SECRETS_FILE = 'secrets.json'

def get_cached_value_or_set(name: str, generator: callable):

    existing_value = get_cached_value(name)

    if existing_value is not None:
        return existing_value

    value = generator()
    set_cached_value(name, value)
    return value


def get_cached_value(name: str):
    secrets_file = _get_secrets_file()

    if os.path.exists(secrets_file):
        with open(secrets_file, 'r') as file:
            try:
                data = json.load(file)
                value = data.get(name)
                if value:
                    return value
            except json.JSONDecodeError:
                return None
    return None


def get_cached_values_with_prefix(prefix: str) -> dict:
    """Returns {name: value} for every cached entry whose name starts with
    prefix, e.g. all encrypted_owner_key_v* entries cached per vault key
    version by KeyBackup/shared_key_flow.py."""
    secrets_file = _get_secrets_file()

    if os.path.exists(secrets_file):
        with open(secrets_file, 'r') as file:
            try:
                data = json.load(file)
            except json.JSONDecodeError:
                return {}
            return {name: value for name, value in data.items() if name.startswith(prefix)}
    return {}


def set_cached_value(name: str, value: str):
    secrets_file = _get_secrets_file()

    if os.path.exists(secrets_file):
        with open(secrets_file, 'r') as file:
            try:
                data = json.load(file)
            except json.JSONDecodeError:
                raise Exception("Could not read secrets file. Aborting.")
    else:
        data = {}
    data[name] = value
    with open(secrets_file, 'w') as file:
        json.dump(data, file)


def _get_secrets_file():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(script_dir, SECRETS_FILE)