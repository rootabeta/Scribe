### USER TAMPERABLES

refresh = True

### END USER TAMPERABLES
from math import ceil
from nsapi import standardize, math
from nationcache import Cache
from random import shuffle, choice

cache = Cache("volstrostia","greater_sahara")
if refresh:
    cache.refresh()

allNations, WANations, nonWANations = cache.fetchNationLists()

# This is a nation we will assume is GONE
blacklist = []
allNations = [nation for nation in allNations if standardize(nation.name) not in blacklist]
WANations = [nation for nation in WANations if standardize(nation.name) not in blacklist]
nonWANations = [nation for nation in nonWANations if standardize(nation.name) not in blacklist]


numWA = len(WANations)
numNonWA = len(nonWANations)

regionInfo = cache.fetchRegionInfo()
delegate = cache.fetch_nation_cached(regionInfo.delegate)

print(f"Current cost to transition is {math.transition(numWA, numNonWA)}")
print(f"The delegate has {delegate.influence}")

# Targets filter out endorsers
targets = [standardize(nation.name) for nation in allNations if standardize(nation.name) not in delegate.endorsers and standardize(nation.name) != standardize(delegate.name)]

booted = []
totalCost = 0

while math.transition(numWA, numNonWA) > ( delegate.influence - 100) :
    bestValue = 0
    bestTarget = None
    bestName = ""
    bestCost = 0
    bestResult = 0

    currentCost = math.transition(numWA, numNonWA)

    for target in targets:
        # Skip the ones we've already hit
        if target in booted:
            continue

        targetNation = cache.fetch_nation_cached(target)

        cost = targetNation.influence

        if cost <= 0:
            cost = 1

        # How much does ejecting this guy bring down our cost?
        if targetNation.WA:
            result = currentCost - math.transition(numWA - 1, numNonWA)
        else:
            result = currentCost - math.transition(numWA, numNonWA - 1)
    
        value = float(result) / float(cost)

        if value > bestValue or bestTarget == None:
            bestValue = value
            bestTarget = targetNation
            bestName = target
            bestCost = cost
            bestResult = result

    # Boot the selected one
    booted.append(bestName)
    totalCost += bestCost
    print(f"Boot {bestName} - influence is {bestCost} | brings down from {currentCost} by {bestResult} - {'WA MEMBER' if bestTarget.WA else 'WA NONMEMBER'}")

    if bestTarget.WA:
        numWA -= 1
    else:
        numNonWA -= 1

print(f"Booted {len(booted)}")
print(f"Resulting cost to transition is {math.transition(numWA, numNonWA)}")
print(f"The delegate has {delegate.influence}")
print(f"Required removing {totalCost} influence")

# Rich target list - this is everyone who needs to be banned, sorted by influence (descending)
targets = [ cache.fetch_nation_cached(nation) for nation in booted ]

# From least to most inf
targets = sorted(targets, key=lambda x: x.influence)
# From most to least
# targets = targets[::-1]

ROnames = [
    "inner_kilvaka",
#    "beauty_school_dropout",
#    "greater_chicati",
#    "tyreum",
#    "zong_jam_dan",
#    "silence_shadow"
]

ROs = [ cache.fetch_nation_cached(nation) for nation in ROnames ]
#delegate = cache.fetch_nation_cached("lave_deldederady")

remaining = []

whodoeswhat = {}
for RO in ROs:
    whodoeswhat[standardize(RO.name)] = []

# For each of these targets, who will ban them?
for target in targets:
    gaps = []
    
    ROlist = [RO for RO in ROs]
    shuffle(ROlist)

    for RO in ROlist:
        # How much does this RO have left over after banning this one?
        # Surely it must cost SOMETHING
        if target.influence < 1:
            target.influence = 1

        gap = RO.influence - math.ROeject(target.influence)

        # Do not count ROs who cannot do it
        if gap >= 1.0:
            gaps.append((RO, gap))

            # Pick a random person who can do it
#            ROofChoice = RO
#            print(f"{ROofChoice.name} will eject {target.name} ({int(ROofChoice.influence)} vs {ceil(target.influence)} - {ceil(math.ROeject(target.influence))})")
#            # Track that target to that RO
#            whodoeswhat[standardize(ROofChoice.name)].append(target.name)
#            ROofChoice.influence -= math.ROeject(target.influence)
#            break

    # Somebody can!
    if gaps:
        # Whoever has the smallest gap wins!
        # Prevent ties from ending up in a deterministic order
        shuffle(gaps) 
        ROofChoice = sorted(gaps, key=lambda x: x[1])[0][0] # First entry, get RO name from that

        print(f"{ROofChoice.name} will eject {target.name} ({int(ROofChoice.influence)} vs {ceil(target.influence)} - {ceil(math.ROeject(target.influence))})")
        # Track that target to that RO
        whodoeswhat[standardize(ROofChoice.name)].append(target.name)
        ROofChoice.influence -= math.ROeject(target.influence)

    # Nobody can :(
    else:
        remaining.append(target)

print()

for name in whodoeswhat.keys():
    print(f"TARGETS FOR {name.upper()}")
    startingInf = cache.fetch_nation_cached(name).influence
    totalCost = 0
    with open(f"firingsolutions/{name}.csv","w") as f:
        # Sort by largest-smallest influence
        for target in whodoeswhat[name][::-1]:
            print(target)
#            T = cache.fetch_nation_cached(target)
            f.write(target)
            f.write("\n")
    print()

if remaining:
    print("ERROR: INFLUENCE INSUFFICIENT")
    print(f"Remaining targets: {len(remaining)}")
    print([nation.name for nation in remaining])
