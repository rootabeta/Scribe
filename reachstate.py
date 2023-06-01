from nsapi import math

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

class Transitions:
    modes = ["nofuture","semifuture","future"]

    def generateAll(startState):
        allTransitions = []
        for mode in Transitions.modes:
            transition = Transitions.Transition(startState, mode=mode)
            if transition:
                allTransitions.append(transition)

        return allTransitions

    class Transition():
        def __init__(self, startState, mode="nofuture"):
            self.startState = startState
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
    def generateAll(startState):
        allPasswords = []
        for mode in Passwords.modes:
            # generates an end state
            password = Passwords.Password(startState, mode=mode)
            if password:
                allPasswords.append(password)

        return allPasswords

    class Password():
        def __init__(self, startState, mode="nofuture_noex", passworder=None):
            self.mode = mode
            self.startState = startState

            # Special feature - who will do the passwording?
            self.passworder = passworder

            # List of who is banned in what order by whom
            self.firingSolution = None
            # Used to determine next phase starting conditions
            self.endState = self.startState

            if mode == "none":
                self.firingSolution = None
                self.endState = self.startState

            # Each sets
            # self.firingSolution
            # self.endState
            elif mode == "nofuture":
                self.nofuture()

            elif mode == "semifuture":
                self.semifuture()

            elif mode == "future":
                self.future()

            elif mode == "nofuture_noex":
                self.nofuture_noex()

            elif mode == "semifuture_noex":
                self.semifuture_noex()

            elif mode == "future_noex":
                self.future_noex()

        # O.G. algorithms, EXCEPT that anyone endorsing
        # the delegate or at least one officer is exempt
        def nofuture(self):

            return

        def semifuture(self):

            return

        def future(self):

            return

        # O.G. algorithms
        # We can do silly things like eject our own endorsers,
        # Because we can predict how this will affect us later
        # when we evaluate the resulting costs
        def nofuture_noex(self):

            return

        def semifuture_noex(self):

            return

        def future_noex(self):

            return

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

        self.ROs = []

        self.delegate = None
        for nation in self.nations:
            if nation.name == self.delegateName:
                self.delegate = nation
                break

        for nation in self.nations:
            if nation.name in self.RONames:
                self.ROs.append(nation)

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
                    transitions = Transitions.generateAll(password.getState())
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

