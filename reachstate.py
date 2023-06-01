from math import ceil
from copy import deepcopy
from nsapi import math
from random import random, randint

class Hitlist():
    def __init__(self, nation, cutoff=0, ban=True, delegate=False):
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
        if verbose:
            print(f"|- Target list: ")
            # Starting at the top, now we're here
            for target in self.targets:
                print(target)

        if makeCSV:
            self.makeCSV()

    def estimateDeficit(self, influence):
        # How much do we need to banject?
        cost = self.estimateCost(influence)
        
        # How much do I have to play with?
        remaining = self.remainingInfluence - self.cutoff

        # I need 5 and I have 4 - I need 1 more. 
        return cost - remaining

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

        self.failure = False

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
        deficits = {}
        for ROname in self.hitlists.keys():
            # How much MORE influence do we need?
            deficits[ROname] = 0

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
            # Well shiiiit, nobody is offering. Let's just try for funsies.
            if not offers:
               # print(f"Error: We have run out of influence! Processed {processed}/{total}")
               # print(f"Died trying to banject {target.name}")
               # print(f"Influence consumed: {infConsumed}")

                self.failure = True
                self.failed = processed
                eviloffers = []

                for ROname in self.hitlists.keys():
                    RO = self.hitlists[ROname]

                    # Can't hit. How much do we need to make it happen?
                    if RO.canHit(target.influence) == -1:
                        eviloffer = RO.estimateDeficit(target.influence) + deficits[ROname]
#                        print(ROname, eviloffer)
                        eviloffers.append((ROname, eviloffer))

                    # Who has the smallest deficit?

                if eviloffers:
                    hitman = min(eviloffers, key=lambda x: x[1])

                    deficits[hitman[0]] = hitman[1] #+= hitman[1]

#                    self.hitlists[hitman[0]].addTarget(target)
#
#                return False
                else:
                    print("Well that can't be right")

            else:
                # Who is closest?
                hitman = min(offers, key=lambda x: x[1])
                self.hitlists[hitman[0]].addTarget(target)
                #print(f"{hitman[0]} will take {target.name}, leaving them with {self.hitlists[hitman[0]].remainingInfluence} influence to spare ({self.hitlists[hitman[0]].consumedInfluence} used of {self.hitlists[hitman[0]].startingInfluence} and a floor of {self.hitlists[hitman[0]].cutoff})")

                processed+=1

        if deficits:
            print("DEFICIT REPORT:")
            for key in deficits.keys():
                print(f"{key} is short by {deficits[key]} influence")

        if not self.failure:
            return True
        else:
            return False

    def makeReport(self):
        pass

class Transitions:
    modes = ["nofuture","semifuture","future"]

    def generateAll(StartState):
        startState = StartState #deepcopy(StartState)
        allTransitions = []
        for mode in Transitions.modes:
            transition = Transitions.Transition(startState, mode=mode)
            if transition:
                allTransitions.append(transition)

        return allTransitions

    class Transition():
        def __init__(self, startState, mode="nofuture"):
            self.startState = deepcopy(startState)
            self.mode = mode

            # Firing solution chosen by the given mode
            self.firingSolution = None
            # Will get steadily modified as the desired mode is done
            self.endState = self.startState 

            # NOOP
            if mode == "none":
                self.firingSolution = None
                self.endState = self.startState 

            elif mode == "nofuture":
                self.nofuture()

            elif mode == "semifuture":
                self.semifuture()

            elif mode == "nofuture":
                self.semifuture()

        def nofuture(self):
            
            return

        def semifuture(self):

            return

        def future(self):

            return

        def getMode(self):
            return self.mode

        def getSolution(self):
            # The firing solution that will make this so
            return self.firingSolution

        def getState(self):
            # The resultant state of executing self.firingSolution
            return self.endState

class Passwords:
    modes = ["nofuture","semifuture","future","nofuture_noex","semifuture_noex","future_noex"]

    # Generate all firing solutions
    def generateAll(oldStartState):
        startState = oldStartState
        allPasswords = []
        for mode in Passwords.modes:
            # generates an end state
            password = Passwords.Password(startState, mode=mode)
            if password:
                allPasswords.append(password)

        return allPasswords

    class Password():
        def __init__(self, startState, mode="nofuture_noex", passworderOverride=None):
            self.mode = mode
            self.startState = deepcopy(startState)
            #self.startState = startState

            # Special feature - who will do the passwording?
            self.passworder = passworderOverride

            # List of who is banned in what order by whom
            self.firingSolution = None
            # Used to determine next phase starting conditions
            self.endState = None
#            self.endState = deepcopy(self.startState)


            # Never ban an RO or delegate
            # For obvious reasons

            if mode == "none":
                self.firingSolution = None
                self.endState = deepcopy(self.startState)

            elif mode == "nofuture":
                self.nofuture()

            elif mode == "semifuture":
                self.semifuture()

            elif mode == "future":
                self.future()

            elif mode == "nofuture_noex":
                self.nofuture()

            elif mode == "semifuture_noex":
                self.semifuture()

            elif mode == "future_noex":
                self.future()


        # Blind purge of fury
        # Influence is all we care about, nothing more
        def nofuture(self, exempt=[]):
            # We will never touch the startState, only the endState
            # Even during data fetches
            # Get all nations
            print("Computing nofuture password strategy")
            self.endState = deepcopy(self.startState)
            self.firingSolution = FiringSolution()

            canPassword = [RO for RO in self.endState.RONations if RO.influence > self.endState.getCosts()[0]]
            if canPassword:
                passworder = min(canPassword, key=lambda x: x.influence)
                print(f"Passworder selected: {passworder.name} ({passworder.influence} influence)")
                print(f"Passworder HAS sufficient influence! No purge necessary! Cost is {self.endState.getCosts()[0]}")
                return
            else:
                # Whoever is closest to being able to set will set
                passworder = max([RO for RO in self.endState.RONations], key=lambda x: x.influence)
                print(f"Passworder selected: {passworder.name} ({passworder.influence} influence)")
                print(f"Passworder does NOT have sufficient influence. Cost to password is {self.endState.getCosts()[0]}")

            delegate = self.endState.delegateNation
            # Sort targets by influence - cheapest first
            targets = self.endState.nations
            targets = sorted(targets, key=lambda x: x.influence)

            mindex = 0

            # If we need another target, and we have another to pick from, launch the attack
            while self.endState.getCosts()[0] > passworder.influence and len(targets) > mindex:
                # Remove cheapest remaining target and assign to targetlist
                considered = targets[mindex]
                # If they are an RO, delegate, or anyone else we want to keep around, skip
                if considered.name in self.endState.donotban or considered.name in exempt: 
#                    print(f"Skipping {considered.name}")
                    mindex += 1
                    continue
                # Otherwise, they are the lowest on the totem pole! Make em go away.
                else:
                    target = targets.pop(mindex)
                    #print(f"Hitting {target.name}")
                    self.firingSolution.addTarget(target)
                    self.endState.remove(target.name)

            if self.endState.getCosts()[0] > passworder.influence:
                # Should never happen unless NOBODY has like, ANY influence
                print("Error: Exhausted target list with nofuture strategy (somehow)")
                print(f"Cost is {self.endState.getCosts()[0]}, we have {passworder.influence}")
                print(f"Estimated gap: {passworder.influence-self.endState.getCosts()[0]}")

                self.firingSolution = None
                self.endState = None

            else:

                print("Found potential firing list with nofuture strategy.")
                print(f"Password cost is {self.endState.getCosts()[0]}, we have {passworder.influence}")
                print(f"Transition cost is {self.endState.getCosts()[1]}, we have {delegate.influence}")
                print(f"Requires banjecting {len(self.firingSolution.targets)} targets out of {len(self.startState.nations)}, leaving {len(self.endState.nations)}")
               # print("Starting influences:")
               # for RO in self.endState.RONations:
               #     print(f"{RO.name} -> {RO.influence} influence")

                hitlists = {}
                for RO in self.endState.RONations:
                    if RO.name == passworder.name:
               #         print(f"{RO.name} must stay above {math.password(len(self.endState.nations))}")
                        hitlists[RO.name] = Hitlist(RO, cutoff=ceil(math.password(len(self.endState.nations))))
                    else:
                        hitlists[RO.name] = Hitlist(RO)

                if delegate:
                    hitlists[delegate.name] = Hitlist(delegate, cutoff=ceil(self.endState.getCosts()[1]))

                self.firingSolution.setHitlists(hitlists)
                if self.firingSolution.buildFiringSolution():
                    print("Success!")
                else:
                    print("Failure")

                #print("Ending influences:")
                #for RO in self.endState.RONations:
                #    print(f"{RO.name} -> {RO.influence} influence")

                print(f"Password cost is {self.endState.getCosts()[0]}, we have {passworder.influence}")
                print(f"Transition cost is {self.endState.getCosts()[1]}, we have {delegate.influence}")
                print("")

#                hitlists = {}
#                for RO in self.RONations:
#                    if RO.name == self.passworder.name:
#                        # Add a cutoff, plus padding to be sure
#                        hitlists[RO.name] = Hitlist(RO,cutoff=ceil(math.password(len(targets))))
#                    else:
#                        # Assume all other ROs influence is entirely expendable
#                        hitlists[RO.name] = Hitlist(RO)
#
#                if self.delegate and self.delegate not in self.RONations:
#                    hitlists[self.delegate.name] = Hitlist(self.delegate, cutoff=transCost, delegate=True)
#
#                firingSolution.setHitlists(hitlists)
#
#                if firingSolution.buildFiringSolution():


        # Slightly less blind
        # We will chew through all the non-WA, then move on to the WA
        def semifuture(self, exempt=[]):
            self.firingSolution = FiringSolution()
            self.endState = self.startState


        # We will prioritize non-WA, UNLESS banjecting the number of WA
        # that that influence buys us reduces TRANSITION influence cost
        # Just going by influence may be most efficient to password, 
        # But password+transition will require a little forward thinking
        def future(self, exempt=[]):
            self.firingSolution = FiringSolution()
            self.endState = self.startState


        # Diagnostic and statistic
        def getMode(self):
            return self.mode

        def getSolution(self):
            # The firing solution that will make this so
            return self.firingSolution

        def getState(self):
            # The resultant state of executing self.firingSolution
            return self.endState

# Just keeps the passwords and transitions nice and neatly organized together
class Recipe():
    def __init__(self, State, password=None, transition=None):
        self.startState = State
        self.endState = State
    
        self.password = password
        self.transition = transition

        if self.transition:
            self.endState = self.transition.getState()

        elif self.password:
            self.endState = self.password.getState()

        else:
            self.endState = None

    def show(self):
        if self.password: 
            P = self.password.getMode()
        else:
            P = "XP"

        if self.transition:
            T = self.transition.getMode()
        else:
            T = "XT"

        print(f"{P} -> {T}")

    def getState():
        return self.endState

    def getPass():
        return self.password

    def getTrans():
        return self.transition

# The state of a region at any point in time. 
# Used to evaluate different firing solutions.
class State():
    def __init__(self, regionInfo, allNations, WANations, nonWANations):
        self.nations = allNations
        self.WANations = WANations
        self.nonWANations = nonWANations
        self.delegateName = regionInfo.delegate
        self.RONames = regionInfo.BCROnames
        
        self.passwordCost = math.password(len(self.nations))
        self.transitionCost = math.transition(len(self.WANations), len(self.nonWANations))

        self.donotban = self.RONames
        self.donotban.append(self.delegateName)

        self.RONations = []
        self.delegateNation = None
        for nation in self.nations:
            if nation.name == self.delegateName:
                self.delegateNation = nation
                self.delegateNation.influence = int(self.delegateNation.influence)
                break

        for nation in self.nations:
            if nation.name in self.RONames and nation.name != self.delegateName:
                self.RONations.append(nation)

    # Might as well
    def getCosts(self):
        self.updateCosts()
        return self.passwordCost, self.transitionCost

    # Update the costs
    def updateCosts(self):
        self.passwordCost = math.password(len(self.nations))
        self.transitionCost = math.transition(len(self.WANations), len(self.nonWANations))
#        print(f"New costs are now {self.passwordCost}, {self.transitionCost}")

    # Simulate a nations removal from the region
    def remove(self, name):
        index = 0
        for nation in self.nations:
            if nation.name == name:
                del(self.nations[index])
                break
            index+=1

        index = 0
        for nation in self.WANations:
            if nation.name == name:
                del(self.WANations[index])
                break
            index+=1

        index = 0
        for nation in self.nonWANations:
            if nation.name == name:
                del(self.nonWANations[index])
                break
            index+=1

        self.updateCosts()

# The desired end-state of execution
# We give it what we have to want with, and ask of it
# To give us a password, and/or allow us to transition
# In return, it will take this data, and compute for us
# A way to do it ASAP.
class EndState():
    def __init__(self, cache, allNations, WANations, nonWANations, regionInfo, doPassword, doTransition):
        self.cache = cache
        self.allNations = allNations
        self.WANations = WANations
        self.nonWANations = nonWANations
        self.regionInfo = regionInfo
        self.doPassword = doPassword
        self.doTransition = doTransition
        self.startState = State(self.regionInfo, self.allNations, self.WANations, self.nonWANations)
        self.recipes = []

        self.passwords = []
        self.transitions = []

    # Generate a recipe for each strategy we know
    def generateRecipes(self):
        recipes = []

        # We want a password
        if self.doPassword:
            passwords = Passwords.generateAll(self.startState)

            # For each of these passwords,
            # If there is a firing solution...
            for password in passwords:
                # Make a transition plan based on the password plan we just ran
                if self.doTransition:
                    passwordEndState = password.getState()
                    transitions = Transitions.generateAll(passwordEndState) 
                    for transition in transitions:
                        recipes.append(Recipe(self.startState, password, transition))

                # No need to transition, mission accomplished
                elif not self.doTransition:
                    recipes.append(Recipe(self.startState, password, None))

        # We want transition only, no password
        elif self.doTransition:
            transitions = Transitions.generateAll(self.startState)
            for transition in transitions:
                recipes.append(Recipe(self.startState, None, transition))

        # These are all the different routes we could take!

#        for recipe in recipes:
#            recipe.show()

        return recipes

    # Of all the recipes we have chosen, which one accomplishes the goal best, or at least at all?
    # Chosen by fastest route to victory
    def evaluate(self):
        pass

