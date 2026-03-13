import os.path
import shutil
import subprocess
from dataclasses import asdict, dataclass, field
from datetime import datetime

import yaml
from groq import Groq

ROOT = os.path.dirname(os.path.dirname(__file__))
conf_file = os.path.join(ROOT, "config.yaml")


@dataclass
class Config:
    author: str
    repos: list[str]
    titles: list[str]
    groq_key: str
    model: str = "openai/gpt-oss-120b"
    instruction: str | None = None
    notes: list[str] = field(default_factory=list)
    no_copy: bool = False


def normalize_path(path: str) -> str:
    return os.path.abspath(os.path.expanduser(path))


def get_conf_content() -> str:
    with open(conf_file, encoding="utf-8") as f:
        return f.read()


def copy_config(file: str):
    shutil.copy2(file, conf_file)


def load_config() -> Config:
    if not os.path.isfile(conf_file):
        raise TypeError("Config file not found")

    try:
        with open(conf_file, encoding="utf-8") as f:
            conf_data = yaml.safe_load(f)

        config = Config(**conf_data)
        if len(config.repos) != len(config.titles):
            msg = "Number of repos in the config must be equal to the number of titles"
            raise TypeError(msg)

        for idx in range(len(config.repos)):
            config.repos[idx] = normalize_path(config.repos[idx])
        return config
    except TypeError:
        msg = (
            "Invalid or missnig keys in the YAML config file, "
            "please ensure (only) 'author', 'repos', 'titles' "
            "and 'groq_key' fields"
        )
        raise TypeError(msg)


def dump_config(config: Config):
    with open(conf_file, "w", encoding="utf-8") as f:
        yaml.safe_dump(asdict(config), f)


def get_commits(config: Config) -> str:
    cwd, logs = os.getcwd(), []
    for idx in range(len(config.repos)):
        repo, title = config.repos[idx], config.titles[idx]
        os.chdir(repo)

        try:
            run = subprocess.run(
                [
                    "git",
                    "log",
                    "--since=midnight",
                    f"--author={config.author}",
                ],
                capture_output=True,
                text=True,
            )
            if run.returncode != 0:
                print(run.stderr)
                break

            if not run.stdout:
                continue

            logs.append(f"title: {title}\n---\n\n")
            logs.append(run.stdout)
            logs.append("\n-----\n\n\n")
        finally:
            os.chdir(cwd)

    return "".join(logs)


def describe_commits(commits: str, config: Config, notes: list[str]) -> str:
    client = Groq(api_key=config.groq_key)
    instruction = (
        "You are a bot assisting a software engineer write daily "
        "updates, you will be given their commmits for today and "
        "you need to summarize it. Create logical sections for all "
        "the given repos and write the updates following it.\n\n"
        "use this format:\n"
        "Updates, <today_date>\n\n<repo_title>\n  1. did fizz\n  2. did buzz"
        "\n\n <repo_title>\n  3. did foom\n\n"
        "NOTE: the updates must be in past tense as opposed to the "
        "(most probably) imperative commit messages\n"
        'NOTE: say "Updates <today_date>\n\nno updates today" if there '
        "were no commits today, follow the format (newlines) strictly\n"
        "NOTE: Do NOT respond with anything other than the summary of the"
        "NOTE: sort the updates in the descending order of significance\n"
        f"NOTE: the date today is {datetime.now().strftime('%d %b %Y')}\n"
    )
    for note in notes:
        instruction += f"NOTE: {note}\n"

    messages = [
        {"role": "system", "content": config.instruction or instruction},
        {"role": "user", "content": commits},
    ]
    response = client.chat.completions.create(
        messages=messages, model=config.model
    )
    return response.choices[0].message.content
