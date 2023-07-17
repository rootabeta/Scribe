import requests
from defusedxml import ElementTree as ET
from time import sleep

headers = {
    "User-Agent":"Just a simple API watcher; Devved and used by Volstrostia"
}

def transCost(W,N):
    CN = 0
    if N > 200:
        CN = 4000
    else:
        CN = N * 20

    return (80 * W) + CN

r = requests.get("https://www.nationstates.net/cgi-bin/api.cgi?region=greater_sahara&q=numnations+numwanations",headers=headers)
xml = ET.fromstring(r.text)
numNations = int(xml.findtext("NUMNATIONS"))
numWA = int(xml.findtext("NUMUNNATIONS"))
nonWA = numNations - numWA

print(f"NATIONS: {numNations} | WA: {numWA} | NWA: {nonWA}")
print(f"TRANSITION COST: {transCost(numWA, nonWA)}")
print("Reminder: Lave has 3250")
