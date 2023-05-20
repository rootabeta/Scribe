# Generic utils
import argparse
import config

# NS API
import NS

def banner():
    with open("banner.txt","r") as f:
        print(f.read().format(VERSION=config.VERSION,CODENAME=config.CODENAME))

banner()

parser = argparse.ArgumentParser(description="Purging with prestige")

parser.add_argument("target", action="store", help="region scheduled for purge", metavar="region")
parser.add_argument("--excempt", action="append", help="BCROs who will not be purging", metavar="RO")
parser.add_argument("--conserve", action="append", help="BCROs who will not be purging beyond amount required for secret password", metavar="RO")
parser.add_argument("--conservative", action="store_true", help="assume no trans. delegate will not be required to remain above f/s transition threshhold")

args = parser.parse_args()
