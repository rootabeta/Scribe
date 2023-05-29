from nsapi import Nation, Region, math

class Shot():
    RO = "" # Who swings the hammer? Mirrors parent hitlist.
    target = "" # Who are we sacrificing to the Overseer today?
    targetInfluence = 0 # How much inf do they have?
    influenceCost = 0 # How much will it cost us?
    startingInf = 0 # How much do we have before?
    endingInf = 0 # How much will we have left over?
    targetWA = False # Is target in the WA?
    ban = False # Banject, or eject?

    def printReport(self):
        reportString = f"{RO} will {'banject' if ban else 'eject'} {target} ({'WA member' if targetWA else 'Non-WA'}), costing {influenceCost} influence ({startingInf}->{endingInf})"
        return reportString

    def getCSV(self):
        # RO, target, banject/eject, targetWA, targetInf, startingInf, infCost, endingInf
        reportString = f"{RO},{target},{'banject' if ban else 'eject'},{'Member' if targetWA else 'Non-member'},{targetInfluence},{startingInf},{endingInf}"

        return reportString

class Hitlist():
    RO = ""
    startingInfluence = 0 
    consumedInfluence = 0
    passworder = False

    # List of Shot() types
    targets = []

    def report(self, makeCSV=True, verbose=True):
        print(f"[*] Purge list for {RO}")
        print(f"|- Starting influence: {startingInfluence}")
        print(f"|- Influence consumed: {consumedInfluence}")
        print(f"|-  This RO sets pass: {'YES' if passworder else 'No'}")
        if verbose:
            print(f"|- Target list: ")

            for target in targets:
                print(target.printReport())
        if makeCSV:
            self.makeCSV()

    def makeCSV(self):
        pass

class FiringSolution():
    # The total influence cost of executing this firing solution
    cost = 0 
    remainingNonWA = []
    remainingWA = []

    # Each RO gets a hitlist of targets in the order they are to be sacrificed to the Overseer
    # The hitlist will also specify whether they are to banned or ejected
    hitlists = [] 

    # Simulated state of the region - including officer/del influence and remaining nations
    resultingData = None

    def makeReport():
        pass

class Password():
    firingSolution = None

    def nofuture(self):
        pass

    def semifuture(self):
        pass

    def future(self):
        pass

    def __init__(self, cache, mode, passworder=None):
        if passworder:
            self.passworder = passworder
        else:
            self.passworder = max(cache.BCROs, key=lambda x: x.influence) # Passworder is whoever has the most influence
            
class Transition():
    # 1) Get list of all non-WA sorted by inf
    # 2) Get list of all WA sorted by inf
    # 3) Work way up list of WA
    # 4) Each WA, see how many non-WA we can boot for that amount
    # 5) Does booting that many non-WA lower our cost more than booting this one WA?
    # 6) If so, add the non-WA ones. Otherwise, add the WA one. 
    pass

class PassAndTrans():
    # We do three potential modes
    # Future, Semi-Future, and No-Future
    #
    # In FUTURE mode, we compare how many non-WA we can ban for the cost of each WA we want to ban
    # In SEMI-FUTURE mode, we simply only ban non-WA
    # In NO-FUTURE mode, we ignore WA membership status
    #
    # Then, we compute a firing solution for all three and simulate doing each - then take each
    # simulated reality, and simulate a transition on each of them. 
    # Then, we can sort only by the firing patterns that are valid, i.e. we have the influence for
    # If we have 1, that's our pattern. If we have 0, we error out and explain how much more we need
    # However, if we have 2+, we can select based on a number of criteria, including
    #
    # 1) Minimal amount of overall influence lost
    # 2) Minimal number of ejections/banjections combined
    # 3) Minimal amount of transition influence cost (this is likely the most useful)
    # 
    # And probably other systems besides. 
    # Then, we create two folders - phase 1, and phase 2
    # Each folder will contain RO.csv, and includes the targets, sorted top-down by order of ban, as
    # well as diagnostic information to allow the human to make informed decisions
    # Then, when all phase 1 targets are banned, the designated passworder may place a secret password
    # Once this is complete, the phase 2 targets can be distributed. These will be removed like the
    # phase 1 targets, but ejected, not banned. When all officers have ejected all their phase 2
    # targets, the delegate may then password the region.

    pass
