import os.path
import shutil
import subprocess
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Union

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


def is_repo(path: str):
    return os.path.isdir(os.path.join(path, ".git"))


def copy_config(file: str):
    with open(file, "r", encoding="utf-8") as f:
        conf_data = yaml.safe_load(f)

    repos = conf_data.get("repos", None)
    titles = conf_data.get("titles", None)
    if repos is None or titles is None:
        raise ValueError("Config file is missing repos and/or titles")
    if type(repos) is not list or type(titles) is not list:
        raise TypeError("Repos and titles must be lists")
    if len(repos) != len(titles):
        raise ValueError("Number of repos must equal number of titles")

    for idx in range(len(repos)):
        if type(repos[idx]) is str:
            repos[idx] = {
                "path": normalize_path(repos[idx]),
                "branch": "main",
            }
        else:
            repos[idx] = {
                **repos[idx],
                "path": normalize_path(repos[idx]["path"]),
            }

    conf_data["repos"] = repos
    with open(file, "w", encoding="utf-8") as f:
        yaml.safe_dump(conf_data, f)

    shutil.copy2(file, conf_file)


def load_config() -> Config:
    if not os.path.isfile(conf_file):
        raise FileNotFoundError("Config file not found")

    with open(conf_file, encoding="utf-8") as f:
        conf_data = yaml.safe_load(f)

    config = Config(**conf_data)
    return config


def dump_config(config: Config):
    with open(conf_file, "w", encoding="utf-8") as f:
        yaml.safe_dump(asdict(config), f)


def add_repo(path: str, title: str, branch: Union[str, None], config: Config):
    path = normalize_path(path)
    branch = branch or "main"
    if any(repo["path"] == path for repo in config.repos):
        raise ValueError(f"{path} is already registered")

    if not is_repo(path):
        raise ValueError(f"{path} is not a git repository")
    if not title:
        raise ValueError("A title for the new repo is required")

    exists = (
        subprocess.call(
            ["git", "rev-parse", "--verify", branch],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            cwd=path,
        )
        == 0
    )
    if not exists:
        raise ValueError(f"Branch '{branch}' does not exist")

    config.repos.append({"path": path, "branch": branch})
    config.titles.append(title)
    dump_config(config)


def remove_repo(path: str, config: Config):
    path = normalize_path(path)
    idx = next(
        (i for i, repo in enumerate(config.repos) if repo["path"] == path),
        None,
    )
    if not idx:
        raise ValueError(f"{path} is not registered")

    config.repos = [
        repo for r_idx, repo in enumerate(config.repos) if r_idx != idx
    ]
    config.titles = [
        title for t_idx, title in enumerate(config.titles) if t_idx != idx
    ]
    dump_config(config)


def get_commits(config: Config) -> str:
    logs = []
    for idx in range(len(config.repos)):
        title = config.titles[idx]
        run = subprocess.run(
            [
                "git",
                "log",
                config.repos[idx]["branch"],
                "--since=midnight",
                f"--author={config.author}",
            ],
            capture_output=True,
            text=True,
            cwd=config.repos[idx]["path"],
        )
        if run.returncode != 0:
            print(run.stderr)
            break

        if not run.stdout:
            continue

        logs.append(f"title: {title}\n---\n\n")
        logs.append(run.stdout)
        logs.append("\n-----\n\n\n")

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
