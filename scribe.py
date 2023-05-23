# Generic utils
import argparse
import config
from os import path
import gzip
from defusedxml import ElementTree as ET

# NS API
from NS import API, RegionInfo, NationInfo


def banner():
    with open("banner.txt", "r") as f:
        print(f.read().format(VERSION=config.VERSION, CODENAME=config.CODENAME))


def main(args):
    # INIT
    mainNation = ""
    target = args.target.lower().replace(" ", "_")
    doTrans = True  # :3
    skipDown = False
    forceDown = False
    ban = args.banject

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

    # PERFORM CALCULATIONS
    regionInfo = api.regionInfo(target)
    gap = regionInfo.targetInf - regionInfo.delegate.influence
    print(
        f"Delegate {regionInfo.delegate.nation} would require approximately {regionInfo.targetInf} influence - they have {regionInfo.delegate.influence}"
    )
    print(f"The deficit is: {gap}")

    if ban:
        pass

    print()
    print("The following BCROs are appointed:")
    for RO in regionInfo.BCROs:
        if RO.nation not in exempt and (
            RO.nation not in conserve or RO.influence > regionInfo.targetInf
        ):
            print(f"Nation {RO.nation} has {RO.influence} influence")
    print()
    print("Building target list")

    print("Acquiring nations.xml.gz")
    if (forceDown or not path.isfile("nations.xml.gz")) and not skipDown:
        print("Downloading nations.xml.gz")
        api.download_file(
            "https://www.nationstates.net/pages/nations.xml.gz"
        )  # Download nations.xml.gz

    elif not skipDown:
        print("Existing nations.xml.gz file detected.")
        confirmation = input("Overwrite? (Y/n) ")
        if not (confirmation and confirmation.lower()[0] == "n"):
            api.download_file(
                "https://www.nationstates.net/pages/nations.xml.gz"
            )  # Download nations.xml.gz

    print("Loading nations.xml")
    with gzip.open("nations.xml.gz", mode="r") as f:
        rawnations = f.read()

    nationsxml = ET.fromstring(rawnations)

    print("Parsing nations.xml")

    print("Nations in target: ")
    for nation in nationsxml.findall("NATION"):
        if nation.find("REGION").text.lower().replace(
            " ", "_"
        ) == target.lower().replace(" ", "_"):
            print(
                nation.findtext("NAME"),
                nation.findtext("UNSTATUS"),
                nation.findtext("INFLUENCE"),
                nation.findtext("ENDORSEMENTS"),
            )
            # print(nation.find("NAME").text, nation.find("LASTLOGIN").text, nation.find("LASTACTIVITY").text)


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
    action="store",
    help="BCROs who will not be purging",
    metavar="RO",
    default=[],
    nargs="*",
)
parser.add_argument(
    "--conserve",
    action="store",
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

parser.add_argument(
    "--banject",
    action="store_true",
    help="assume banjection, not just ejection (i.e., assume password in place). default: no",
    default=False,
)

args = parser.parse_args()

main(args)
