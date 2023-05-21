# Generic utils
import argparse
import config

# NS API
from NS import API, Math


def banner():
    with open("banner.txt", "r") as f:
        print(f.read().format(VERSION=config.VERSION, CODENAME=config.CODENAME))


def main(args):
    mainNation = ""
    doTrans = True  # :3
    skipDown = False
    forceDown = False

    if args.skip_download and args.force_download:
        exit("Error: cannot supply skip and force at the same time!")

    exempt = args.exempt
    conserve = args.conserve

    if args.no_trans:
        doTrans = False

    if args.skip_download:
        skipDown = True
    elif args.force_download:
        forceDown = True

    if args.mainNation:
        mainNation = args.mainNation
    else:
        print(
            "Scribe needs to know your main nation in order to comply with NationStates scripting requirements"
        )
        mainNation = input("Main nation: ")

    api = API(mainNation)


### INIT + OPTS

banner()

parser = argparse.ArgumentParser(description="Purging with prestige")

parser.add_argument(
    "target", action="store", help="region scheduled for purge", metavar="region"
)
parser.add_argument(
    "--main",
    "-n",
    "-m",
    action="store",
    help="your main nation; used to identify you to the NationStates API",
    metavar="main",
    dest="mainNation",
)
parser.add_argument(
    "--exempt",
    action="append",
    help="BCROs who will not be purging",
    metavar="RO",
    default=[],
    nargs="*",
)
parser.add_argument(
    "--conserve",
    action="append",
    help="BCROs who will not be purging beyond amount required for secret password",
    metavar="RO",
    default=[],
    nargs="*",
)
parser.add_argument(
    "--no-trans",
    action="store_true",
    help="delegate will not be required to remain above f/s transition threshhold",
)
parser.add_argument(
    "--skip-download",
    action="store_true",
    help="skip downloading nations.xml if present",
)
parser.add_argument(
    "--force-download", action="store_true", help="force downloading nations.xml"
)

args = parser.parse_args()

main(args)
