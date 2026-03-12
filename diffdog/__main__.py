import sys

import pyperclip as clip

from diffdog.cli import parse
from diffdog.utils import (
    copy_config,
    describe_commits,
    get_commits,
    get_conf_content,
    load_config,
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
        commits = get_commits(config)
        description = describe_commits(
            commits, config, options.note or config.notes
        )
        if options.no_copy or config.no_copy:
            print(description + "\n")
        else:
            clip.copy(description)
    except TypeError as e:
        parser.error(e)


if __name__ == "__main__":
    main()
