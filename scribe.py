# Generic utils
import argparse
import config
from os import path
import gzip
from defusedxml import ElementTree as ET
import sqlite3

from nsapi import math
from nationcache import Cache
from datetime import datetime

# No easy frontend for you, we hardcode this sucka
# Easy frontend - just pass it our starting conditions, and it will return a procedure to get there.
# from reachstate import EndState

def easyTime(timestamp):
    if timestamp:
        return datetime.fromtimestamp(timestamp)
    else:
        return "Unknown"

def banner():
    with open("banner.txt", "r") as f:
        print(f.read().format(VERSION=config.VERSION, CODENAME=config.CODENAME),end="",flush=True)

def main(args):
    # INIT
    mainNation = ""
    region = args.target.lower().replace(" ", "_")
    purge = False
    if args.purge:
        print("Warning: You are about to purge the database! This cannot be undone!")
        confirmation = input("Are you sure you want to do this? (y/N) ")
        if confirmation and confirmation[0].lower() == "y":
            print("So be it.")
            purge = True

    if args.locked and args.lock_only:
        print("Error: cannot specify we want to lock AND we are already locked!")

    if args.mainNation:
        mainNation = args.mainNation
    else:
        print(
            "Scribe needs to know your main nation in order to comply with NationStates scripting requirements"
        )
        mainNation = input("Main nation: ")

    cache = Cache(mainNation, region)
    if purge:
        # Initiate a full purge of the target region's cache data
        cache.purge(routine=False)

    if not args.cached:
        cache.refresh()
        newest, oldest = cache.dateRange(region)
        print(f"The newest entry for {region} was refreshed on: {easyTime(newest)}")
        print(f"The oldest entry for {region} was refreshed on: {easyTime(oldest)}")
    else:
        print("WARNING: You have selected to only use previously cached data")
        print("This provides a performance boost at the cost of reduced temporal accuracy")
        print("Relying on old or incomplete data can cause dangerously inaccurate results!")
        newest, oldest = cache.dateRange(region)
        print(f"The newest entry for {region} was refreshed on: {easyTime(newest)}")
        print(f"The oldest entry for {region} was refreshed on: {easyTime(oldest)}")

    # Deadline is... much harder
    if args.fast_forward:
        print(f"WARNING: You have chosen to forecast {args.fast_forward} UPDATES (not days) ahead.")
        print(f"The generated firing solution, if any, may not be suitable for immediate use.")
#        cache.fastForward(args.forecast)
        # Manually rebuild nationcache with forecasting
        cache.fastForward(args.fast_forward) 

    allNations, WANations, nonWANations = cache.fetchNationLists()
    regionInfo = cache.fetchRegionInfo() # Useful things like who is RO or delegate
    
    print(f"Current estimated cost to password:  {math.password(len(allNations))}")
    print(f"Current estimated cost to transition: {math.transition(len(WANations), len(nonWANations))}")

    # Set our desired state. It will give us a recipe containing firing plans
    state = EndState(cache, allNations, WANations, nonWANations, regionInfo, not args.locked, not args.lock_only)
    state.generateRecipes()
    result = state.pickBest()

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

#parser.add_argument(
#    "--exempt",
#    action="store",
#    help="BCROs who will not be purging",
#    metavar="nation",
#    default=None,
#    nargs="*",
#)

parser.add_argument(
    "--passworder",
    action="store",
    help="designate a specific nation to apply password; default is automatically selected.",
    metavar="nation",
    default=None
)

#parser.add_argument(
#    "--no-trans",
#    action="store_true",
#    help="delegate will not be required to remain above f/s transition threshhold",
#)

parser.add_argument(
    "--locked",
    action="store_true",
    help="assume region is already in passworded state, and calculate transition cost directly"
)

parser.add_argument(
    "--lock-only",
    action="store_true",
    help="only calculate cost to get to password"
)

parser.add_argument(
    "--fast-forward",
    action="store",
    help="estimate a certain of updates in the future, instead of now",
    type=int,
    default=0
)

parser.add_argument(
    "--purge",
    action="store_true",
    help="purge database entries for the target region before anything else is done"
)

parser.add_argument("--cached",action="store_true",help="use cached database and do not refresh")

args = parser.parse_args()

main(args)
