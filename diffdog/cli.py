import argparse
import sys

parser = argparse.ArgumentParser(
    formatter_class=lambda prog: argparse.HelpFormatter(
        prog, max_help_position=100
    )
)
parser.add_argument("-c", "--config", help="Here, this is my config file")
parser.add_argument(
    "-n",
    "--note",
    nargs="*",
    action="extend",
    help="Notes to the LLM on summary creation",
    default=[],
)
parser.add_argument(
    "--repo", nargs="?", const=".", help="Add the current repo to the config"
)
parser.add_argument(
    "--title", help="Use this title for the new repo being registered"
)
parser.add_argument(
    "--rm-repo",
    nargs="?",
    const=".",
    help="Remove (unregister) this repository",
)
parser.add_argument(
    "--no-copy", action="store_true", help="Don't copy summary to clipboard"
)
parser.add_argument(
    "--show-conf", action="store_true", help="Show me my configuration"
)


def parse() -> tuple[argparse.ArgumentParser, argparse.Namespace]:
    return parser, parser.parse_args(sys.argv[1:])
