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

from git import Repo
from langchain.schema import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from copilot.copilot_shared import configure_logging, process_env


def main():
    process_env()
    configure_logging()
    script_dir = os.path.dirname(os.path.realpath(__file__))
    repo_dir = os.path.realpath(os.path.join(script_dir, ".."))

    process_env(script_dir)

    old_tag = "v0.1.0"
    new_tag = "v0.1.1"

    changelog = generate_changelog_since_tag(repo_dir, old_tag)
    logging.info("--- Changelog extracted from git commits")
    logging.info(changelog)
    logging.info("--- Changelog summary")
    summary = summarize(changelog, old_tag, new_tag)

    file_path = os.path.join(repo_dir, "CHANGELOG.md")
    with open(file_path, "r") as file:
        original_content = file.read()
    with open(file_path, "w") as file:
        file.write(summary + "\n\n\n" + original_content)

    logging.info("Changelog generated successfully")


def generate_changelog_since_tag(repo_path, tag):
    repo = Repo(repo_path)
    assert not repo.bare
    commits = list(repo.iter_commits(f"{tag}..HEAD"))
    changelog = f"Changelog since {tag}\n\n"
    for commit in commits:
        changelog += f"- {commit.summary}\n"
    return changelog


def get_changes_between_tags(repo_path, old_tag, new_tag):
    repo = Repo(repo_path)
    assert not repo.bare
    commits = list(repo.iter_commits(f"{old_tag}...{new_tag}"))
    changelog = f"Changelog from {old_tag} to {new_tag}\n\n"
    for commit in commits:
        changelog += f"- {commit.summary}\n"
    return changelog


def summarize(changelog, old_tag, new_tag):
    chat = ChatOpenAI(temperature=0)
    chat.model_name = "gpt-3.5-turbo"
    messages = [
        SystemMessage(
            content="Your directive is to summarize git commits into a changelog that will go into a markdown file. "
            "There should be a paragraph that summarizes the changes. "
            "The response should conform (and additional sections can be added if deemed necessary) to: "
            f"# Changelog from {old_tag} to {new_tag} part.\n\n"
            "<summary>\n\n"
            "## Enhancements\n"
            "<list_of_enhancements>\n\n"
            "## Cleanups"
            "<list_of_cleanups>"
        ),
        HumanMessage(content=f"Convert the following commits into a summary: {changelog}"),
    ]
    response = chat.invoke(messages)
    logging.info(response.content)
    return response.content


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.error(f"main caught exception: {e}", exc_info=e)
        sys.exit(1)
