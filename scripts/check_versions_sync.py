# ------------------------------------------------------------------------------
#  Copyright (c) 2024 eContriver LLC
#  This file is part of Capital Copilot from eContriver.
#  -
#  Capital Copilot from eContriver is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  any later version.
#  -
#  Capital Copilot from eContriver is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  -
#  You should have received a copy of the GNU General Public License
#  along with Capital Copilot from eContriver.  If not, see <https://www.gnu.org/licenses/>.
# ------------------------------------------------------------------------------

import logging
import os
import sys

import toml
import yaml

from copilot.copilot_shared import configure_logging, process_env


def main():
    process_env()
    configure_logging()
    script_dir = os.path.dirname(os.path.realpath(__file__))
    repo_dir = os.path.realpath(os.path.join(script_dir, ".."))
    pyproject_versions = load_pyproject_versions(repo_dir)
    logging.debug(f"pyproject.toml versions: {pyproject_versions}")
    precommit_versions = load_precommit_versions(repo_dir)
    logging.debug(f".pre-commit-config.yaml versions: {precommit_versions}")
    mismatches = check_versions_sync(pyproject_versions, precommit_versions)
    if mismatches:
        logging.info("Version mismatches found between pyproject.toml and .pre-commit-config.yaml:")
        for tool, pyproject_version, precommit_version in mismatches:
            logging.info(f"{tool}: pyproject.toml={pyproject_version}, .pre-commit-config.yaml={precommit_version}")
        sys.exit(1)
    else:
        logging.info("All versions are in sync.")


def load_pyproject_versions(repo_dir):
    with open(os.path.join(repo_dir, "pyproject.toml"), "r") as pyproject_file:
        pyproject = toml.load(pyproject_file)
        poetry = pyproject.get("tool", {}).get("poetry", {})
        dependencies = poetry.get("dependencies", {})
        dev_dependencies = poetry.get("group", {}).get("dev", {}).get("dependencies", {})
    return {**dependencies, **dev_dependencies}


def load_precommit_versions(repo_dir):
    with open(os.path.join(repo_dir, ".pre-commit-config.yaml"), "r") as precommit_file:
        precommit_config = yaml.safe_load(precommit_file)
        hook_info = {}
        for repo in precommit_config.get("repos", []):
            repo_rev = repo.get("rev", "")
            if repo_rev == "":  # Skip if no rev is specified, generally local repos
                continue
            for hook in repo.get("hooks", []):
                hook_id = hook.get("id", "")
                hook_info[hook_id] = repo_rev
    return hook_info


def normalize_version(version):
    """Remove a preceding 'v' from version string if present."""
    return version.lstrip("v")


def check_versions_sync(pyproject_versions, precommit_versions):
    mismatched_versions = []
    for tool, pyproject_version in pyproject_versions.items():
        if tool not in precommit_versions:
            continue
        normalized_pyproject_version = normalize_version(pyproject_version)
        normalized_precommit_version = normalize_version(precommit_versions[tool])
        if normalized_pyproject_version != normalized_precommit_version:
            mismatched_versions.append((tool, pyproject_version, precommit_versions[tool]))
    return mismatched_versions


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.error(f"main caught exception: {e}", exc_info=e)
        sys.exit(1)
