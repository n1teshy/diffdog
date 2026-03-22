import sys

import pyperclip as clip

from diffdog.cli import parse
from diffdog.utils import (
    add_repo,
    copy_config,
    describe_commits,
    get_commits,
    get_conf_content,
    load_config,
    remove_repo,
)


def main():
    parser, options = parse()
    try:
        if options.config:
            copy_config(options.config)
            sys.exit()

        if options.show_conf:
            print(get_conf_content())
            sys.exit()

        config = load_config()

        if options.repo:
            add_repo(options.repo, options.title, config)
            sys.exit()

        if options.rm_repo:
            remove_repo(options.rm_repo, config)
            sys.exit()

        commits = get_commits(config)
        description = describe_commits(
            commits, config, options.note or config.notes
        )
        if options.no_copy or config.no_copy:
            print(description + "\n")
        else:
            clip.copy(description)
    except Exception as e:
        parser.error(e)


if __name__ == "__main__":
    main()
