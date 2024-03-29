from math import ceil
from nsapi import Nation, Region, math

#class Shot():
#    RO = "" # Who swings the hammer? Mirrors parent hitlist.
#    target = "" # Who are we sacrificing to the Overseer today?
#    targetInfluence = 0 # How much inf do they have?
#    influenceCost = 0 # How much will it cost us?
#    startingInf = 0 # How much do we have before?
#    endingInf = 0 # How much will we have left over?
#    targetWA = False # Is target in the WA?
#    ban = False # Banject, or eject?
#
#    def printReport(self):
#        reportString = f"{RO} will {'banject' if ban else 'eject'} {target} ({'WA member' if targetWA else 'Non-WA'}), costing {influenceCost} influence ({startingInf}->{endingInf})"
#        return reportString
#
#    def getCSV(self):
#        # RO, target, banject/eject, targetWA, targetInf, startingInf, infCost, endingInf
#        reportString = f"{RO},{target},{'banject' if ban else 'eject'},{'Member' if targetWA else 'Non-member'},{targetInfluence},{startingInf},{endingInf}"
#
#        return reportString

class Hitlist():
    def __init__(self, nation, cutoff=0, ban=False, delegate=False):
        self.nation = nation
        self.name = nation.name

        self.delegate = delegate
        self.startingInfluence = int(nation.influence)
        # How much must this person stay above?
        self.cutoff = cutoff

        self.remainingInfluence = self.startingInfluence
        self.consumedInfluence = 0

        self.ban = ban

        # Target list. Plain nation name.
        # In sorted order by influence - largest inf first
        # This is done during parcelling of a firing solution to hitlists
        self.targets = []

    def report(self, makeCSV=True, verbose=True):
        print(f"[*] Purge list for {self.name}")
        print(f"|- Ban or Eject Targets: {'BAN' if self.ban else 'EJECT'}")
        print(f"|-   Starting influence: {self.startingInfluence}")
        print(f"|-   Influence consumed: {self.consumedInfluence}")
        print(f"|-      Final influence: {self.startingInfluence - self.consumedInfluence}")
        print(f"|-      Influence floor: {self.cutoff}")
        print(f"|-    This RO sets pass: {'YES' if self.passworder else 'No'}")
        if verbose:
            print(f"|- Target list: ")
            # Starting at the top, now we're here
            for target in self.targets:
                print(target)

        if makeCSV:
            self.makeCSV()

    def estimateCost(self, influence):
        # Ban, as non-del and del
        if self.ban and not self.delegate:
            cost = math.RObanject(influence)
        elif self.ban and self.delegate:
            cost = math.DELbanject(influence)

        # Eject, as non-del and del
        elif not self.ban and not self.delegate:
            cost = math.ROeject(influence)
        elif not self.ban and self.delegate:
            cost = math.DELeject(influence)

        cost = int(ceil(cost))

#        print(f"/ {self.name} has {self.remainingInfluence} after expending {self.consumedInfluence} from {self.startingInfluence}")
#        print(f"| Additionally, they must stay above {self.cutoff}")
#        print(f"| They have {self.remainingInfluence - self.cutoff} left to spend")
#        print(f"| Banning this target would consume {cost}")
#        if cost < self.remainingInfluence - self.cutoff:
#            print("\ They CAN ban this one")
#        else:
#            print("\ They CANNOT ban this one")
#
#        print()

        return cost

    def canHit(self, influence):
        cost = self.estimateCost(influence)
        # At least one inf to spare, just in case
        if cost < (self.remainingInfluence - self.cutoff):
            # Return the prediction of how much influence we'd have left
            return int((self.remainingInfluence - self.cutoff)) - ceil(cost)
        else:
            # We cannot hit this one
            return -1

    def addTarget(self, target):
        estCost = self.estimateCost(target.influence)
        self.consumedInfluence += estCost
        self.remainingInfluence -= estCost
        self.targets.append(target)

    def makeCSV(self):
        pass

class FiringSolution():
    # The target list - unparcelled to given ROs. 
    def __init__(self, hitlists = {}):
        self.targets = []

        # The total influence cost of executing this firing solution
        self.cost = 0 
    
        # Each RO gets a hitlist of targets in the order they are to be sacrificed to the Overseer
        # The hitlist will also specify whether they are to banned or ejected
        # These hitlists are populated via taking the next target from targets after population, 
        # deciding whom to assign it to, and appending that target to that ROs hitlist. 
        # When all targets have been distributed, the hitlists are ready to be sent out to each
        # RO - this is done when the makeReport() function is invoked in the FiringSolution
        # method. It will generate CSVs and terminal reports on who will banject/eject whom when.
        # Hitlists are stored as dicts with the RO's nation name being the key

        # Simulated state of the region - including officer/del influence and remaining nations
        self.remainingNonWA = []
        self.remainingWA = []
        self.remainingNations = []

        # Accept a hitlist from on high, all we need to do is populate it
        self.hitlists = hitlists
        # resultingData = None

        self.total = 0
        self.failed = 0

    # Add someone we want GONE
    def addTarget(self, target): #), influence, isWA):
        self.cost += target.influence
        self.targets.append(target)

    # Get the cost of this evil ploy
    def getCost(self):
        return self.cost

    def setHitlists(self, hitlists):
        self.hitlists = hitlists

    def getFailed(self):
        return self.targets[::-1][self.failed:]

    def buildFiringSolution(self, reverse=True):
        # We wanna ban every last one of these
        # They got appended small->large
        # We wanna go large->small when parcelling out
        # So, invert list order and start with the big bads

        #skipped = []
        processed = 0
        infConsumed = 0

        total = len(self.targets)
        self.total = total

        for target in self.targets[::-1]:
            # Fetch each nation's hitlist

            offers = []

            for ROname in self.hitlists.keys():
                RO = self.hitlists[ROname]
                offer = RO.canHit(target.influence)
                if offer > 0:
                    offers.append((ROname, offer))
                    infConsumed += offer

            # Seek who is closest to getting soaked up exactly
            if not offers:
                print(f"Error: We have run out of influence! Processed {processed}/{total}")
                print(f"Died trying to banject {target.name}")
                print(f"Influence consumed: {infConsumed}")

                self.failed = processed

                return False

            else:
                hitman = min(offers, key=lambda x: x[1])
                self.hitlists[hitman[0]].addTarget(target)

                processed+=1

        return True
    def makeReport(self):
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

    bestFiringSolution = None
    resultantNations = []
    resultantWA = []
    resultantNonWA = []

    passwordFiringSolution = None
    passworder = None

    # region data should be static
    def __init__(self, cache, passworder=None, verbose=True):
        self.cache = cache
        self.allNations, self.WANations, self.nonWANations = self.cache.fetchNationLists()
        self.passworder = passworder
        self.passworderInf = 0
        self.firingSolutions = []
        self.purgeRequired = False

        # Selecting passworder from regional officers
        if not self.passworder:
            RONations = [self.cache.fetch_nation(RO) for RO in self.cache.fetchRegionInfo().BCROnames]

            # If one or multiple ROs can password right now, then pick whichever has the least influence right now and have them do it
            # This frees up larger influence stockpilers to tackle larger influence nations if the need arises
            canPassword = [RONation for RONation in RONations if RONation.influence > math.password(len(self.allNations))]
            if canPassword:
                print(f"One or multiple ROs can initiate a password with the current dataset! Purge is not required.")
                self.passworder = min(canPassword, key=lambda x: x.influence) 

            else:
                print("No RO has sufficient influence to set a password")
                # Of all the nations that have 
                self.passworder = max(RONations, key=lambda x: x.influence) 
                print(f"Selecting {self.passworder.name} as passworder")
                print(f"{self.passworder.name} has {self.passworder.influence} influence")
                print(f"Currently, passwording requires {math.password(len(self.allNations))}, a gap of {math.password(len(self.allNations))-self.passworder.influence} influence")
        else:
            print(f"Manually overriding passworder to {self.passworder}")
            self.passworder = self.cache.fetch_nation(self.passworder)
        self.passworderInf = self.passworder.influence

        print(f"Selected {self.passworder.name}, who has {self.passworderInf} influence, to apply password (cost: {math.password(len(self.allNations))} influence)")
        print()

    # Select desired firing solution.
    # Default will execute all and select
    # whichever is most efficient for our goal
    def getFiringSolutions(self, mode=0):
        if mode == 0 or mode == 1:
            self.nofuture()

        if mode == 0 or mode == 2:
            self.semifuture()

        if mode == 0 or mode == 3:
            self.future()

        return self.firingSolutions

    # Used for when our only goal is passwording. Very short-sighted
    # Sort simply based on influence
    def nofuture(self):
        # Just a list of all nations, sorted by influence, nothing fancy.
        firingSolution = FiringSolution()
        targets = sorted(self.allNations, key=lambda x: x.influence)

        if math.password(len(targets)) < self.passworderInf:
            print("Passworder {self.passworder} has sufficient influence to apply a password immediately.")
            print("No firing solution necessary.")
            return None

        # Keep removing lowest-inf targets and adding them to the hitlist, 
        # and repeat until we either run out of targets
        while math.password(len(targets)) >= self.passworderInf:
            # Pop from potential targets and add to tracked targets
            if len(targets) > 0:
                firingSolution.addTarget(targets.pop(0)) 
            else:
                print("Error: could not find valid firing solution with nofuture strategy. Passworder influence insufficient.")
                return None

        print(f"Found potential firing solution with nofuture strategy. Total cost: {firingSolution.getCost()}")
        # TODO: Validate that we can actually ban that many!
        print(f"Would require banning {len(firingSolution.targets)} nations out of {len(self.allNations)}")
        print(f"This would bring the influence cost down to {math.password(len(targets))}")
        print(f"This cost is below the password threshold of {self.passworderInf} for {self.passworder.name} to set a secret password")
        print(f"Transitioning with the resultant state would require {math.transition(len([nation for nation in targets if nation.WA == True]), len([nation for nation in targets if nation.WA == False]))} influence")
        print()

        self.firingSolutions.append(firingSolution)
        return firingSolution

    # Used when we want to blindly prioritize non-WA
    # Do we want to also ban WA? I guess...
    def semifuture(self):
        firingSolution = FiringSolution()
        targets = sorted(self.nonWANations, key=lambda x: x.influence)
        targets += sorted(self.WANations, key=lambda x: x.influence)

        if math.password(len(targets)) < self.passworderInf:
            print("Passworder {self.passworder} has sufficient influence to apply a password immediately.")
            print("No firing solution necessary.")
            return None

        # Keep removing lowest-inf targets and adding them to the hitlist, 
        # and repeat until we either run out of targets
        while math.password(len(targets)) >= self.passworderInf:
            # Pop from potential targets and add to tracked targets
            if len(targets) > 0:
                firingSolution.addTarget(targets.pop(0)) 
            else:
                print("Error: could not find valid firing solution with semifuture strategy. Passworder influence insufficient.")
                return None

        print(f"Found potential firing solution with semifuture strategy. Total cost: {firingSolution.getCost()}")
        # TODO: Validate that we can actually ban that many!
        print(f"Would require banning {len(firingSolution.targets)} nations out of {len(self.allNations)}")
        print(f"This would bring the influence cost down to {math.password(len(targets))}")
        print(f"This cost is below the password threshold of {self.passworderInf} for {self.passworder.name} to set a secret password")
        print(f"Transitioning with the resultant state would require {math.transition(len([nation for nation in targets if nation.WA == True]), len([nation for nation in targets if nation.WA == False]))} influence")
        print()

        self.firingSolutions.append(firingSolution)
        return firingSolution

    def future(self):
        firingSolution = FiringSolution()
        targetsnonWA = sorted(self.nonWANations, key=lambda x: x.influence)
        targetsWA = sorted(self.WANations, key=lambda x: x.influence)

        while math.password(len(targetsnonWA + targetsWA)) >= self.passworderInf:
            # Need to ban someone, but noone left to ban!
            if not targetsnonWA and not targetsWA:
                print("Error: could not find valid firing solution with future strategy. Passworder influence insufficient.")
                return None
                
            for candidate in targetsnonWA:
                # Calculate how much getting rid of this one guy would reduce my influence
                # Find out how many WA that influence could remove
                # Determine whether or not getting rid of this WA or those non-WA would help me more
                banfluence = candidate.influence
                wafluence = 0
                watargs = 0 # First X targets
                for wacandidate in targetsWA:
                    watargs += 1
                    wafluence += wacandidate.influence
                    if wafluence >= banfluence:
                        break

            # For wafluence influence, we can either boot watargs WA, or one non-WA.
            # Does the benefit from banning the WA outweigh the cost reduction of the password?
            WAbannedresult = math.password(len(targetsWA) + len(targetsnonWA) - watargs)
            nWAbannedresult = math.password(len(targetsWA) + len(targetsnonWA) - 1)

            # If the diff between banning the WA nations and non-WA ones 
            # is larger than the difference between the influence difference between 
            # banning WA and non-WA, ban the WA
            # Also if we can't find any WA targets, just ban the non-WA
            if (watargs > 0) and (WAbannedresult - nWAbannedresult) < (wafluence - banfluence):
                # Select the first X watargets we identified
                for i in range(watargs):
                    # Add each to the target list
                    firingSolution.addTarget(targetsWA.pop(0))
            else:
                # Add the non-WA we were inspecting to the list
                firingSolution.addTarget(targetsnonWA.pop(0)) 
        print(f"Found potential firing solution with future strategy. Total cost: {firingSolution.getCost()}")
        # TODO: Validate that we can actually ban that many!
        print(f"Would require banning {len(firingSolution.targets)} nations out of {len(self.allNations)}")
        print(f"This would bring the influence cost down to {math.password(len(targetsWA + targetsnonWA))}")
        print(f"This cost is below the password threshold of {self.passworderInf} for {self.passworder.name} to set a secret password")
        print(f"Transitioning with the resultant state would require {math.transition(len(targetsWA), len(targetsnonWA))} influence")
        print()

        self.firingSolutions.append(firingSolution)
        return firingSolution

class JustPassword():
    bestFiringSolution = None
    resultantNations = []
    resultantWA = []
    resultantNonWA = []

    passwordFiringSolution = None
    passworder = None

    # region data should be static
    def __init__(self, cache, passworder=None, verbose=True):
        self.cache = cache
        self.allNations, self.WANations, self.nonWANations = self.cache.fetchNationLists()
        self.passworder = passworder
        self.passworderInf = 0
        self.firingSolutions = None
        self.purgeRequired = False

        self.delegate = self.cache.fetch_nation(self.cache.fetchRegionInfo().delegate)

        self.RONations = [self.cache.fetch_nation(RO) for RO in self.cache.fetchRegionInfo().BCROnames]
        for RO in self.RONations:
            self.excemptTargs = self.cache.fetch_nation(RO).endorsers

        # Selecting passworder from regional officers
        if not self.passworder:
            # If one or multiple ROs can password right now, then pick whichever has the least influence right now and have them do it
            # This frees up larger influence stockpilers to tackle larger influence nations if the need arises
            self.RONations = [RONation for RONation in self.RONations if RONation]
            canPassword = [RONation for RONation in self.RONations if RONation.influence > math.password(len(self.allNations))]
            if canPassword:
                print(f"One or multiple ROs can initiate a password with the current dataset! Purge is not required.")
                self.passworder = min(canPassword, key=lambda x: x.influence) 

            else:
                print("No RO has sufficient influence to set a password")
                # Get whoever is closest to setting a password currently
                self.passworder = max(self.RONations, key=lambda x: x.influence) 
                print(f"Selecting {self.passworder.name} as passworder")
                print(f"{self.passworder.name} has {self.passworder.influence} influence")
                print(f"Currently, passwording requires {math.password(len(self.allNations))}, a gap of {math.password(len(self.allNations))-self.passworder.influence} influence")
        else:
            print(f"Manually overriding passworder to {self.passworder}")
            self.passworder = self.cache.fetch_nation(self.passworder)
        self.passworderInf = self.passworder.influence

        print(f"Selected {self.passworder.name}, who has {self.passworderInf} influence, to apply password (cost: {math.password(len(self.allNations))} influence)")
        print()

        self.firingSolution = self.nofuture()

    # Select desired firing solution.
    # Default will execute all and select
    # whichever is most efficient for our goal
    def getFiringSolutions(self, mode=0):
        self.nofuture()

    def nofuture(self):
        # Just a list of all nations, sorted by influence, nothing fancy.
        firingSolution = FiringSolution()
        targets = sorted(self.allNations, key=lambda x: x.influence)

        if math.password(len(targets)) < self.passworderInf:
            print("Passworder {self.passworder} has sufficient influence to apply a password immediately.")
            print("No firing solution necessary.")
            return None

        # Keep removing lowest-inf targets and adding them to the hitlist, 
        # and repeat until we either run out of targets
        while math.password(len(targets)) >= self.passworderInf:
            # Pop from potential targets and add to tracked targets
            if len(targets) > 0:
                firingSolution.addTarget(targets.pop(0)) 
            else:
                print("Error: could not find valid firing solution with nofuture strategy. Passworder influence insufficient.")
                return None

        print(f"Built potential firing solution with nofuture strategy. Total cost: {firingSolution.getCost()}")
        print(f"Would require banning {len(firingSolution.targets)} nations out of {len(self.allNations)}")
        print(f"This would bring the influence cost down to {math.password(len(targets))}")
        print(f"This cost is below the password threshold of {self.passworderInf} for {self.passworder.name} to set a secret password")
        print()
        

        transCost = 0
#        transCost = ceil(math.transition(len([nation for nation in targets if nation.WA == True]), len([nation for nation in targets if nation.WA == False])))
#        transCost = ceil(math.transition(len([nation for nation in targets if nation.WA == True]), len([nation for nation in targets if nation.WA == False])))
#        print(f"Transitioning with the resultant state would require {transCost} influence")

        hitlists = {}
        for RO in self.RONations:
            if RO.name == self.passworder.name:
                # Add a cutoff, plus padding to be sure
                hitlists[RO.name] = Hitlist(RO,cutoff=ceil(math.password(len(targets))))
            else:
                # Assume all other ROs influence is entirely expendable
                hitlists[RO.name] = Hitlist(RO)

        if self.delegate and self.delegate not in self.RONations:
            hitlists[self.delegate.name] = Hitlist(self.delegate, cutoff=transCost, delegate=True)

        firingSolution.setHitlists(hitlists)

        if firingSolution.buildFiringSolution():
            print()
            print("Firing solution is valid!")
            return firingSolution

        else:
            print()
            print("Could not distribute firing solution targets")
            print(f"Resulting cost: {math.password(len(targets) + len(firingSolution.getFailed()))}")
#            transCost = ceil(math.transition(len([nation for nation in targets if nation.WA == True]), len([nation for nation in targets if nation.WA == False])))
#            print(f"Resulting trans: {transCost}")

#            failedTargs = firingSolution.getFailed()
#            [targ.name for targ in failedTargs])

            return None

class Transition():
    # 1) Get list of all non-WA sorted by inf
    # 2) Get list of all WA sorted by inf
    # 3) Work way up list of WA
    # 4) Each WA, see how many non-WA we can boot for that amount
    # 5) Does booting that many non-WA lower our cost more than booting this one WA?
    # 6) If so, add the non-WA ones. Otherwise, add the WA one. 
    pass


