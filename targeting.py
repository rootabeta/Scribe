from math import ceil
from nsapi import Nation, math
from datetime import datetime

# Each target, and how they are to be removed.
class Hit():
    def __init__(self, target, ban=True, cost=0):
        self.target = target
        self.ban = ban
        self.cost = cost

# List of WHO will get rid of those targets
class Hitlist():
    def __init__(
            self, 
             nation=None, 
             cutoff=0, 
             banEnabled=True, 
             delegate=False, 
             chooseEjection = True
    ):
        self.ready = False

        self.hits = []

        self.nation = nation
        self.delegate = delegate
        self.cutoff = cutoff

        # Once we have a password, we can just eject, not ban
        # Much cheaper.
        self.banEnabled = banEnabled

        # Sometimes, we believe a nation will not log back in and 
        # move back. In this case, it is cheaper to eject
        # However, if the nation is especially active, this may be
        # unwise, as if they move back, we will
        # need to eject the target twice, wasting influence
        self.chooseEjection = chooseEjection

        if self.nation:
            self.startingInfluence = self.nation.influence

            # Starts at cutoff
            self.remainingInfluence = self.startingInfluence - self.cutoff
            self.ready = True

    # Is it advisable and permitted to eject instead of ban?
    def canEjectOnly(self, target):
        timeout = 15 * 24 * 60 * 60
        tooOld = 23 * 24 * 60 * 60

        # If we are not allowed to sometimes eject, then refuse to
        if not self.chooseEjection:
            return False
        
        # If target has not logged in for 15-23 days (beware of CTE emails!)
        # Then we can choose to eject
        if (target.daysSinceLogin > int(datetime.now().timestamp()) - timeout
        and target.daysSinceLogin + tooOld < int(datetime.now().timestamp())):
            return True
        else:
            return False

    # Return a sorted list of all targets, from highest to lowest costs
    def getTargets(self):
        return sorted(self.hits, key=lambda x: x.cost)[::-1]

    # How much would it cost for me to get rid of this guy as ordered?
    def estimateCost(self, target):
        targetInf = target.influence
        remaining = self.remainingInfluence
        # Is this a ban, or an ejection?
        ban = False

        # Bans - in some cases, if chooseEject is permitted,
        # ban targets may be ejected instead of banned
        # Ban, as non-del
        if self.banEnabled and not self.delegate:
            if self.canEjectOnly(target):
                cost = math.ROeject(targetInf)
            else:
                cost = math.RObanject(targetInf)
                ban = True

        # Ban, as delegate
        elif self.banEnabled and self.delegate:
            if self.canEjectOnly(target):
                cost = math.DELeject(targetInf)
            else:
                cost = math.RObanject(targetInf)
                ban = True

        # Eject, as non-del and del
        elif not self.banEnabled and not self.delegate:
            cost = math.ROeject(targetInf)
        elif not self.banEnabled and self.delegate:
            cost = math.DELeject(targetInf)

        cost = int(ceil(cost))

        # How much is the cost?
        # How much do we have after doing it?
        # Do we ban or just eject?
        # We will NOT disqualify if over the limit, that is for other code
        return ( cost, remaining - cost, ban )

    def estimateDeficit(self, target):
        # How much more do I need?
        remaining = self.remainingInfluence
        cost = self.estimateCost(target)
        return cost[0] - remaining

    # Add a target to the list
    def addTarget(self, target):
        estCost = self.estimateCost(target)
        hit = Hit(target, estCost[2], estCost[0])
        self.hits.append(hit)
        self.remainingInfluence -= estCost[0]

# List of targets we want *gone*
class FiringSolution():
    def __init__(self):
        # We wanna get rid of these suckers
        self.targets = []

        # These are the suckers who will do it
        self.hitlists = {}

    def addTarget(self, target):
        self.targets.append(target)

    def setHitlists(self, hitlists):
        self.hitlists = hitlists

    def buildFiringSolution(self):
        # Largest inf first
        toBeProcessed = len(self.targets)
        processed = 0
        skipped = 0
        failure = False

        deficits = {}

        print("RO -> Spare influence at start")
        for hitman in self.hitlists.keys():
            print(f"{hitman} -> {self.hitlists[hitman].remainingInfluence}")
            deficits[hitman] = 0

        for target in sorted(self.targets, key=lambda x: x.influence)[::-1]:
            predictedStates = []
            failedStates = []

            for hitman in self.hitlists.keys():
                subject = self.hitlists[hitman]
                cost = subject.estimateCost(target)

                # This one can ban and have some left over
                if cost[1] > 0:
                    # RO (costs X) (will have X influence after) (will do X)
                    predictedStates.append((hitman, cost[0], cost[1], cost[2]))
                else:
                    estimatedDebt = subject.estimateDeficit(target)

                    # Skip anyone who actually CAN do it
                    if estimatedDebt > 0:
                        failedStates.append((hitman, deficits[hitman] + estimatedDebt))

            if not predictedStates:
                skipped += 1
                failure = True

                if failedStates:
                    minHelp = min(failedStates, key=lambda x: x[1])
                    deficits[minHelp[0]] = minHelp[1]

                continue
            else:
                processed += 1

                # Built potential banners for this target
                # Select whoever will have the MOST left over
                # Makes sense - cheap action, or spare influence, etc.
                # Autolevels nicely too
                bestOffer = max(sorted(predictedStates, key=lambda x: x[2]))
                self.hitlists[bestOffer[0]].addTarget(target)
                print(f"{bestOffer[0]} will take {target.name}, leaving them with {bestOffer[2]} influence after spending {bestOffer[1]} (Ban: {bestOffer[3]})")
        if failure:
            print()
            print("FS-ERROR: Failed to build firing solution fully")
            print(f"Skipped due to insufficient influence: {skipped}/{toBeProcessed}")
            print(f"Successfully removed: {processed}/{toBeProcessed}")
            print("Estimated deficits: ")
            for hitman in self.hitlists.keys():
                print(f"{hitman} -> {deficits[hitman]}")

            return False
        else:
            return True
