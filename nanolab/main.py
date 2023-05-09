#!./venv_py/bin/python

import logging
from nanolab.src.argparse_commands import ArgParseHandler

logger = logging.getLogger(__name__)


def main():
    arg_parse = ArgParseHandler()
    args = arg_parse.get_args()
    if args.command == "run":
        arg_parse.run()

    elif args.command == "list":
        arg_parse.list_testcases()

    else:
        print("Invalid command. Use 'nanolab run' or 'nanolab list'")


if __name__ == "__main__":
    main()
