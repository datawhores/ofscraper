import sys

import ofscraper.utils.args.globals as global_args
import ofscraper.utils.args.parse as parse_args
import ofscraper.utils.manager as manager


def retriveArgsVManager():
    try:
        if not manager.get_manager_dict().get("args"):
            manager.get_manager_dict()["args"] = parse_args.parse_args()
        return manager.get_manager_dict().get("args")
    except SystemExit as E:
        print(f"Passed Args {sys.argv[1:]}")
        raise E


def retriveArgs():
    try:
        if not global_args.args:
            global_args.args = parse_args.parse_args()
        return global_args.args
    except SystemExit as E:
        print(f"Passed Args {sys.argv[1:]}")
        raise E
