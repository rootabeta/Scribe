from math import ceil
from copy import deepcopy
from nsapi import math, standardize, standardize
from random import random, randint
from targeting import Hitlist, FiringSolution

class Transitions:
    modes = ["blind","halfblind","foresight"]

    def generateAll(StartState):
        startState = StartState #deepcopy(StartState)
        allTransitions = []
        for mode in Transitions.modes:
            transition = Transitions.Transition(startState, mode=mode)
            if transition.firingSolution:
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

            elif mode == "blind":
                self.blind()

            elif mode == "halfblind":
                self.halfblind()

            elif mode == "foresight":
                self.foresight()

        def blind(self):
            print("===== Computing blind transition strategy =====")
            print("***********************************************")

            self.endState = deepcopy(self.startState)
            self.firingSolution = FiringSolution()


            if self.endState.delegateNation.influence > self.endState.getCosts()[1]:
                print()
                print(f"Delegate HAS sufficient influence! No purge necessary! Cost is {self.endState.getCosts()[1]}")
                print()

                self.firingSolution = None
                return self.firingSolution

            print(f"Delegate does NOT have sufficient influence. Cost to transition is {self.endState.getCosts()[1]}")
            delegate = self.endState.delegateNation
            exempt = self.endState.delegateNation.endorsers

            # Build targeting parameters
            targets = self.endState.nations
            targets = sorted(targets, key=lambda x: x.influence)

            mindex = 0

            # If we need another target, and we have another to pick from, launch the attack
            while self.endState.getCosts()[1] > delegate.influence and len(targets) > mindex:
                # Remove cheapest remaining target and assign to targetlist
                considered = targets[mindex]

                if considered.influence < 0:
                    considered.influence = 0

                if standardize(considered.name) in self.endState.donotban or standardize(considered.name) in exempt:
                    mindex += 1
                    continue

                else:
                    target = targets.pop(mindex)
                    self.firingSolution.addTarget(target)
                    self.endState.remove(target.name)

            if self.endState.getCosts()[1] > delegate.influence:
                print("Error: Exhausted target list with blind strategy (somehow)")
                print(f"Cost is {self.endState.getCosts()[1]}, we have {delegate.influence}")
                print(f"Estimated gap: {self.endState.getCosts()[1]-delegate.influence}")

                self.firingSolution = None
                return None
            
            else:
                print("Found potential target list via blind strategy.")
                print(f"Transition cost is {self.endState.getCosts()[1]}, we have {delegate.influence}")
                print(f"Requires ejecting {len(self.firingSolution.targets)} targets out of {len(self.startState.nations)}, leaving {len(self.endState.nations)}")

                hitlists = {}
                for RO in self.endState.RONations:
                    if RO.name == delegate.name:
                        hitlists[RO.name] = Hitlist(RO, cutoff=ceil(self.endState.getCosts()[1]), delegate=True, banEnabled=False)
                    else:
                        hitlists[RO.name] = Hitlist(RO, banEnabled=False)

                self.firingSolution.setHitlists(hitlists)
                
                if self.firingSolution.buildFiringSolution():
                    print("[+] SUCCESSFULLY BUILT FIRING SOLUTION")
                    print()
                    print("Firing solution result summary:")
                    print(f"Transition cost is {self.endState.getCosts()[1]}; The delegate will have {delegate.influence} remaining")
                    print("=== END OF REPORT ===")
                    print()
                    return self.firingSolution
                else:
                    print("[!] FAILED TO BUILD FIRING SOLUTION")
                    print("=== END OF REPORT ===")
                    print()
                    return None

        def halfblind(self):
            print("===== Computing half-blind transition strategy =====")
            print("****************************************************")

            self.endState = deepcopy(self.startState)
            self.firingSolution = FiringSolution()


            if self.endState.delegateNation.influence > self.endState.getCosts()[1]:
                print()
                print(f"Delegate HAS sufficient influence! No purge necessary! Cost is {self.endState.getCosts()[1]}")
                print()

                self.firingSolution = None
                return self.firingSolution

            print(f"Delegate does NOT have sufficient influence. Cost to transition is {self.endState.getCosts()[1]}")
            delegate = self.endState.delegateNation
            exempt = self.endState.delegateNation.endorsers

            # Build targeting parameters
            WAtargs = self.endState.WANations
            nWAtargs = self.endState.nonWANations

            # Prioritize WA nations
            targets = sorted(WAtargs, key=lambda x: x.influence)
            targets += sorted(nWAtargs, key=lambda x: x.influence)

            mindex = 0

            # If we need another target, and we have another to pick from, launch the attack
            while self.endState.getCosts()[1] > delegate.influence and len(targets) > mindex:
                # Remove cheapest remaining target and assign to targetlist
                considered = targets[mindex]

                if considered.influence < 0:
                    considered.influence = 0

                if standardize(considered.name) in self.endState.donotban or standardize(considered.name) in exempt:
                    mindex += 1
                    continue

                else:
                    target = targets.pop(mindex)
                    self.firingSolution.addTarget(target)
                    self.endState.remove(target.name)

            if self.endState.getCosts()[1] > delegate.influence:
                print("Error: Exhausted target list with blind strategy (somehow)")
                print(f"Cost is {self.endState.getCosts()[1]}, we have {delegate.influence}")
                print(f"Estimated gap: {self.endState.getCosts()[1]-delegate.influence}")

                self.firingSolution = None
                return None
            
            else:
                print("Found potential target list via blind strategy.")
                print(f"Transition cost is {self.endState.getCosts()[1]}, we have {delegate.influence}")
                print(f"Requires ejecting {len(self.firingSolution.targets)} targets out of {len(self.startState.nations)}, leaving {len(self.endState.nations)}")

                hitlists = {}
                for RO in self.endState.RONations:
                    if RO.name == delegate.name:
                        hitlists[RO.name] = Hitlist(RO, cutoff=ceil(self.endState.getCosts()[1]), delegate=True, banEnabled=False)
                    else:
                        hitlists[RO.name] = Hitlist(RO, banEnabled=False)

                self.firingSolution.setHitlists(hitlists)
                
                if self.firingSolution.buildFiringSolution():
                    print("[+] SUCCESSFULLY BUILT FIRING SOLUTION")
                    print()
                    print("Firing solution result summary:")
                    print(f"Transition cost is {self.endState.getCosts()[1]}; The delegate will have {delegate.influence} remaining")
                    print("=== END OF REPORT ===")
                    print()
                    return self.firingSolution
                else:
                    print("[!] FAILED TO BUILD FIRING SOLUTION")
                    print("=== END OF REPORT ===")
                    print()
                    return None

        def foresight(self):
            print("===== Computing foresight transition strategy =====")
            print("***************************************************")
            print("ABORTED")
            return None

            self.endState = deepcopy(self.startState)
            self.firingSolution = FiringSolution()


            if self.endState.delegateNation.influence > self.endState.getCosts()[1]:
                print()
                print(f"Delegate HAS sufficient influence! No purge necessary! Cost is {self.endState.getCosts()[1]}")
                print()

                self.firingSolution = None
                return self.firingSolution

            print(f"Delegate does NOT have sufficient influence. Cost to transition is {self.endState.getCosts()[1]}")
            delegate = self.endState.delegateNation
            exempt = self.endState.delegateNation.endorsers

            # Build targeting parameters
            WANations = self.endState.WANations
            NWANations = self.endState.NWANations

            wmindex = 0
            nmindex = 0

            # If we need another target, and we have another to pick from, launch the attack
            while self.endState.getCosts()[1] > delegate.influence:
                # We have at least one potential nonendo to work against
                if len(WANations) > wmindex:
                    considered = WANations[wmindex]

                    # Oops, it *is* an endo! SKIP!!!
                    if standardize(considered.name) in self.endState.donotban or standardize(considered.name) in exempt:
                        wmindex += 1
                        continue
                    
                    else:
                        pass
                        # How many non-WA can I get for this?


                # We are OUT of nonendos!!! Move onto non-WA
                else:
                    considered = NWANations[nmindex]

                    # Whitelist, skip
                    if standardize(considered.name) in self.endState.donotban or standardize(considered.name) in exempt:
                        nmindex += 1
                        continue

                    else:
                        pass


            if self.endState.getCosts()[1] > delegate.influence:
                print("Error: Exhausted target list with blind strategy (somehow)")
                print(f"Cost is {self.endState.getCosts()[1]}, we have {delegate.influence}")
                print(f"Estimated gap: {self.endState.getCosts()[1]-delegate.influence}")

                self.firingSolution = None
                return None
            
            else:
                print("Found potential target list via blind strategy.")
                print(f"Transition cost is {self.endState.getCosts()[1]}, we have {delegate.influence}")
                print(f"Requires ejecting {len(self.firingSolution.targets)} targets out of {len(self.startState.nations)}, leaving {len(self.endState.nations)}")

                hitlists = {}
                for RO in self.endState.RONations:
                    if RO.name == delegate.name:
                        hitlists[RO.name] = Hitlist(RO, cutoff=ceil(self.endState.getCosts()[1]), delegate=True, banEnabled=False)
                    else:
                        hitlists[RO.name] = Hitlist(RO, banEnabled=False)

                self.firingSolution.setHitlists(hitlists)
                
                if self.firingSolution.buildFiringSolution():
                    print("[+] SUCCESSFULLY BUILT FIRING SOLUTION")
                    print()
                    print("Firing solution result summary:")
                    print(f"Transition cost is {self.endState.getCosts()[1]}; The delegate will have {delegate.influence} remaining")
                    print("=== END OF REPORT ===")
                    print()
                    return self.firingSolution
                else:
                    print("[!] FAILED TO BUILD FIRING SOLUTION")
                    print("=== END OF REPORT ===")
                    print()
                    return None

        def getMode(self):
            return self.mode

        def getSolution(self):
            # The firing solution that will make this so
            return self.firingSolution

        def getState(self):
            # The resultant state of executing self.firingSolution
            return self.endState

class Chaos():
    def __init__(self, startState, EjectAllowed=False):
        self.startState = deepcopy(startState)
        self.ejectAllowed = EjectAllowed
        self.endState = None
        self.firingSolution = None

        self.causeChaos()

    def causeChaos(self):
        self.firingSolution = FiringSolution()
        self.endState = deepcopy(self.startState)

        targets = self.startState.nations
        delegate = self.endState.delegateNation
        targets = sorted(targets, key=lambda x: x.influence)
        for target in targets:
            # Do not ban our ROs
            if standardize(target.name) not in self.endState.donotban:
                self.firingSolution.addTarget(target)

        hitlists = {}
        for RO in self.endState.RONations:
            if delegate and standardize(RO.name) != delegate.name:
                hitlists[RO.name] = Hitlist(RO)

        if delegate:
            hitlists[delegate.name] = Hitlist(delegate, cutoff=0, delegate=True)
        self.firingSolution.setHitlists(hitlists)

        if self.firingSolution.buildFiringSolution(invert=False, chaos=True):
            print("Successfully caused chaos")
            return self.firingSolution
        else:
            print("How?")
            return None

class Passwords:
    modes = ["nofuture","semifuture","nofuture_noex","semifuture_noex"] #,"future","future_noex"]

    # Generate all firing solutions
    def generateAll(oldStartState):
        startState = oldStartState
        allPasswords = []
        for mode in Passwords.modes:
            # generates an end state
            password = Passwords.Password(startState, mode=mode)
            if password.firingSolution:
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

            # List of all the nations endorsing our people
            # We don't wanna fw these in any case where
            # our purge will last multiple updates
            self.endos = self.startState.endorsers

            # Never ban an RO or delegate
            # For obvious reasons

            if mode == "none":
                self.firingSolution = None
                self.endState = deepcopy(self.startState)

            elif mode == "nofuture":
                self.nofuture(self.endos)

            elif mode == "semifuture":
                self.semifuture(self.endos)

            elif mode == "future":
                self.future(self.endos)

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
            print("===== Computing nofuture password strategy =====")
            print("************************************************")

            self.endState = deepcopy(self.startState)
            self.firingSolution = FiringSolution()
            print(f"Ruthless Mode: {'OFF' if exempt else 'ON'}")
#            print(f"Always exempting {self.endState.donotban}")
#            print(f"Exempting {exempt}")

            canPassword = [RO for RO in self.endState.RONations if RO.influence > self.endState.getCosts()[0]]
            if canPassword:
                passworder = min(canPassword, key=lambda x: x.influence)
                print(f"Passworder selected: {passworder.name} ({passworder.influence} influence)")
                print(f"Passworder HAS sufficient influence! No purge necessary! Cost is {self.endState.getCosts()[0]}")
                print()
                # Empty...
                return self.firingSolution
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
                
                if considered.influence < 0:
                    considered.influence = 0
#                print(f"Considering {considered.name} -> {considered.influence}")
                # If they are an RO, delegate, or anyone else we want to keep around, skip
                if standardize(considered.name) in self.endState.donotban or standardize(considered.name) in exempt: 
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
                print(f"Estimated gap: {self.endState.getCosts()[0]-passworder.influence}")

                self.firingSolution = None
                return None

            else:

                print("Found potential target list via nofuture strategy.")
                print(f"Password cost is {self.endState.getCosts()[0]}, we have {passworder.influence}")
                print(f"Transition cost is {self.endState.getCosts()[1]}, we have {delegate.influence}")
                print(f"Requires banjecting {len(self.firingSolution.targets)} targets out of {len(self.startState.nations)}, leaving {len(self.endState.nations)}")

                hitlists = {}
                for RO in self.endState.RONations:
                    if RO.name == passworder.name:
               #         print(f"{RO.name} must stay above {math.password(len(self.endState.nations))}")
                        hitlists[RO.name] = Hitlist(RO, cutoff=ceil(math.password(len(self.endState.nations))))
                    else:
                        hitlists[RO.name] = Hitlist(RO)

                if delegate:
                    hitlists[delegate.name] = Hitlist(delegate, cutoff=0, delegate=True)
                    #hitlists[delegate.name] = Hitlist(delegate, cutoff=ceil(self.endState.getCosts()[1]), delegate=True)

                self.firingSolution.setHitlists(hitlists)
                if self.firingSolution.buildFiringSolution():
                    print("[+] SUCCESSFULLY BUILT FIRING SOLUTION")
                    print()
                    print("Firing solution result summary:")
                    print(f"Password cost is {self.endState.getCosts()[0]}; The passworder will have {passworder.influence} remaining")
                    print(f"Transition cost is {self.endState.getCosts()[1]}; The delegate will have {delegate.influence} remaining")
                    print("=== END OF REPORT ===")
                    print()
                    return self.firingSolution
                else:
                    print("[!] FAILED TO BUILD FIRING SOLUTION")
                    print("=== END OF REPORT ===")
                    print()
                    return None

        # Slightly less blind
        # We will chew through all the non-WA, then move on to the WA
        def semifuture(self, exempt=[]):
            #self.firingSolution = FiringSolution()
            #self.endState = self.startState

            print("===== Computing semifuture password strategy =====")
            print("**************************************************")

            self.endState = deepcopy(self.startState)
            self.firingSolution = FiringSolution()
            print(f"Ruthless Mode: {'OFF' if exempt else 'ON'}")

            canPassword = [RO for RO in self.endState.RONations if RO.influence > self.endState.getCosts()[0]]
            if canPassword:
                passworder = min(canPassword, key=lambda x: x.influence)
                print(f"Passworder selected: {passworder.name} ({passworder.influence} influence)")
                print(f"Passworder HAS sufficient influence! No purge necessary! Cost is {self.endState.getCosts()[0]}")
                print()
                # Empty...
                return self.firingSolution
            else:
                # Whoever is closest to being able to set will set
                passworder = max([RO for RO in self.endState.RONations], key=lambda x: x.influence)
                print(f"Passworder selected: {passworder.name} ({passworder.influence} influence)")
                print(f"Passworder does NOT have sufficient influence. Cost to password is {self.endState.getCosts()[0]}")

            targets = sorted(self.endState.nonWANations, key=lambda x: x.influence) + sorted(self.endState.WANations, key=lambda x: x.influence)
            delegate = self.endState.delegateNation
            # Sort targets by influence - cheapest first

            mindex = 0
            # If we need another target, and we have another to pick from, launch the attack
            while self.endState.getCosts()[0] > passworder.influence and len(targets) > mindex:
                # Remove cheapest remaining target and assign to targetlist
                considered = targets[mindex]

                if considered.influence < 0:
                    considered.influence = 0
#                print(f"Considering {considered.name} -> {considered.influence}")
                # If they are an RO, delegate, or anyone else we want to keep around, skip
                if standardize(considered.name) in self.endState.donotban or standardize(considered.name) in exempt:
                    mindex += 1
                    continue
                # Otherwise, they are the lowest on the totem pole! Make em go away.
                else:
                    target = targets.pop(mindex)
#                    print(f"Hitting {target.name}")
                    self.firingSolution.addTarget(target)
                    self.endState.remove(target.name)

            if self.endState.getCosts()[0] > passworder.influence:
                # Should never happen unless NOBODY has like, ANY influence
                print("Error: Exhausted target list with semifuture strategy (somehow)")
                print(f"Cost is {self.endState.getCosts()[0]}, we have {passworder.influence}")
                print(f"Estimated gap: {self.endState.getCosts()[0]-passworder.influence}")

                self.firingSolution = None
                return None

            else:
                print("Found potential target list via semifuture strategy.")
                print(f"Password cost is {self.endState.getCosts()[0]}, we have {passworder.influence}")
                print(f"Transition cost is {self.endState.getCosts()[1]}, we have {delegate.influence}")
                print(f"Requires banjecting {len(self.firingSolution.targets)} targets out of {len(self.startState.nations)}, leaving {len(self.endState.nations)}")

                hitlists = {}
                for RO in self.endState.RONations:
                    if RO.name == passworder.name:
               #         print(f"{RO.name} must stay above {math.password(len(self.endState.nations))}")
                        hitlists[RO.name] = Hitlist(RO, cutoff=ceil(math.password(len(self.endState.nations))))
                    else:
                        hitlists[RO.name] = Hitlist(RO)

                if delegate:
                    hitlists[delegate.name] = Hitlist(delegate, cutoff=0, delegate=True)
                    #hitlists[delegate.name] = Hitlist(delegate, cutoff=ceil(self.endState.getCosts()[1]), delegate=True)

                self.firingSolution.setHitlists(hitlists)
                if self.firingSolution.buildFiringSolution():
                    print("[+] SUCCESSFULLY BUILT FIRING SOLUTION")
                    print()
                    print("Firing solution result summary:")
                    print(f"Password cost is {self.endState.getCosts()[0]}; The passworder will have {passworder.influence} remaining")
                    print(f"Transition cost is {self.endState.getCosts()[1]}; The delegate will have {delegate.influence} remaining")
                    print("=== END OF REPORT ===")
                    print()
                    return self.firingSolution
                else:
                    print("[!] FAILED TO BUILD FIRING SOLUTION")
                    print("=== END OF REPORT ===")
                    print()
                    return None

        # We will prioritize non-WA, UNLESS banjecting the number of WA
        # that that influence buys us reduces TRANSITION influence cost
        # Just going by influence may be most efficient to password, 
        # But password+transition will require a little forward thinking
        def future(self, exempt=[], transitionLookahead=True):
            print("===== Computing future password strategy =====")
            print("**********************************************")

            self.endState = deepcopy(self.startState)
            self.firingSolution = FiringSolution()
            print(f"Ruthless Mode: {'OFF' if exempt else 'ON'}")

            canPassword = [RO for RO in self.endState.RONations if RO.influence > self.endState.getCosts()[0]]
            if canPassword:
                passworder = min(canPassword, key=lambda x: x.influence)
                print(f"Passworder selected: {passworder.name} ({passworder.influence} influence)")
                print(f"Passworder HAS sufficient influence! No purge necessary! Cost is {self.endState.getCosts()[0]}")
                print()
                # Empty...
                return self.firingSolution
            else:
                # Whoever is closest to being able to set will set
                passworder = max([RO for RO in self.endState.RONations], key=lambda x: x.influence)
                print(f"Passworder selected: {passworder.name} ({passworder.influence} influence)")
                print(f"Passworder does NOT have sufficient influence. Cost to password is {self.endState.getCosts()[0]}")

            #targets = #sorted(self.endState.nonWANations, key=lambda x: x.influence) + sorted(self.endState.WANations, key=lambda x: x.influence)
            delegate = self.endState.delegateNation

            lennonWA = len(self.endState.nonWANations)
            lenWA = len(self.endState.WANations)

            targetsnonWA = sorted([nation for nation in self.endState.nonWANations if nation.name not in self.endState.donotban and nation.name not in exempt], key=lambda x: x.influence)
            targetsWA = sorted([nation for nation in self.endState.WANations if nation.name not in self.endState.donotban and nation.name not in exempt], key=lambda x: x.influence)

            # Used to adjust for skipped targets
            skippednonWA = lennonWA - len(targetsnonWA)
            skippedWA = lenWA - len(targetsWA)

            # We would prefer to banject WA, bc it has a greater impact on transition cost
            for target in targetsWA:
                if self.endState.getCosts()[0] < passworder.influence:
                    print("Reached sufficient influence to password")
                    break

                WAfluence = target.influence
                NWAfluence = 0
                tindex = 0

                # If we are out of non-WA, proceed to WA
                if len(targetsnonWA) <= tindex:
                    target = targetsWA.pop(0)
                    self.endState.remove(target.name)
                    self.firingSolution.addTarget(target)
                    continue

                # How many non-WA could we boot for the same amount of influence?
                while NWAfluence < WAfluence and tindex < len(targetsnonWA):
                    NWAfluence += targetsnonWA[tindex].influence
                    tindex += 1

                # NWAfluence ~= WAfluence
                # Which one will reduce our TRANSITION cost more?
                # (Password will just go to whoever has more count, 
                # which will be the non-WA bc it's sheer volume)

                # Same influence cost
                WAcost = math.transition((len(targetsWA) + skippedWA) - 1, (len(targetsnonWA) + skippednonWA) )
                nWAcost = math.transition((len(targetsWA) + skippedWA), (len(targetsnonWA) + skippednonWA) - tindex )
                
                # Banning WA will make for more of a transition cost than the non-WA - ban non-WA
                if WAcost > nWAcost:
                    # Ban that many non-WA
                    for i in range(tindex):
                        target = targetsnonWA.pop(0)
                        self.endState.remove(target.name)
                        self.firingSolution.addTarget(target)
                else:
                    target = targetsWA.pop(0)
                    self.endState.remove(target.name)
                    self.firingSolution.addTarget(target)

            # We are out of WA nations to boot! Proceed to boot non-WA to patch deficit
            if len(targetsWA) <= skippedWA:
                print("boop")
                while self.endState.getCosts()[0] >= passworder.influence and len(targetsnonWA) != 0:
                    target = targetsnonWA.pop(0)
                    self.endState.remove(target.name)
                    self.firingSolution.addTarget(target)


            if self.endState.getCosts()[0] > passworder.influence:
                # Should never happen unless NOBODY has like, ANY influence
                print("Error: Exhausted target list with future strategy (somehow)")
                print(f"Cost is {self.endState.getCosts()[0]}, we have {passworder.influence}")
                print(f"Estimated gap: {self.endState.getCosts()[0]-passworder.influence}")
                print()

                self.firingSolution = None
                return None

            else:
                print("Found potential target list via future strategy.")
                print(f"Password cost is {self.endState.getCosts()[0]}, we have {passworder.influence}")
                print(f"Transition cost is {self.endState.getCosts()[1]}, we have {delegate.influence}")
                print(f"Requires banjecting {len(self.firingSolution.targets)} targets out of {len(self.startState.nations)}, leaving {len(self.endState.nations)}")

                hitlists = {}
                for RO in self.endState.RONations:
                    if RO.name == passworder.name:
               #         print(f"{RO.name} must stay above {math.password(len(self.endState.nations))}")
                        hitlists[RO.name] = Hitlist(RO, cutoff=ceil(math.password(len(self.endState.nations))))
                    else:
                        hitlists[RO.name] = Hitlist(RO)

                if delegate:
                    hitlists[delegate.name] = Hitlist(delegate, cutoff=0, delegate=True)
                    #hitlists[delegate.name] = Hitlist(delegate, cutoff=ceil(self.endState.getCosts()[1]), delegate=True)

                self.firingSolution.setHitlists(hitlists)
                if self.firingSolution.buildFiringSolution():
                    print("[+] SUCCESSFULLY BUILT FIRING SOLUTION")
                    print()
                    print("Firing solution result summary:")
                    print(f"Password cost is {self.endState.getCosts()[0]}; The passworder will have {passworder.influence} remaining")
                    print(f"Transition cost is {self.endState.getCosts()[1]}; The delegate will have {delegate.influence} remaining")
                    print("=== END OF REPORT ===")
                    print()
                    return self.firingSolution
                else:
                    print("[!] FAILED TO BUILD FIRING SOLUTION")
                    print("=== END OF REPORT ===")
                    print()
                    return None


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
        self.RONames = [standardize(RO) for RO in regionInfo.BCROnames]
        
        self.passwordCost = math.password(len(self.nations))
        self.transitionCost = math.transition(len(self.WANations), len(self.nonWANations))

        self.donotban = self.RONames
        self.donotban.append(standardize(self.delegateName))

        # Who is endorsing a delegate or RO?
        # Read only, used as a target exclusion list
        self.endorsers = []

        self.RONations = []
        self.delegateNation = None
        for nation in self.nations:
            if standardize(nation.name) == standardize(self.delegateName):
                self.delegateNation = nation
                self.delegateNation.influence = int(self.delegateNation.influence)
                for endorser in self.delegateNation.endorsers:
                    if standardize(endorser) not in self.endorsers:
                        self.endorsers.append(standardize(endorser))

                break

        seenBefore = []
        for nation in self.nations:
            if standardize(nation.name) in self.RONames and standardize(nation.name) != self.delegateName:
                self.RONations.append(nation)

                for endorser in nation.endorsers:
                    if standardize(endorser) not in seenBefore and standardize(endorser) not in self.endorsers:
                        seenBefore.append(standardize(endorser))

                    # If this endo is endorsing at least one other RO, or the delegate
                    elif standardize(endorser) not in self.endorsers:
                        self.endorsers.append(standardize(endorser))

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
    def __init__(self, cache, allNations, WANations, nonWANations, regionInfo, doPassword, doTransition, ghosts=[], safe=[], chaos=False, chaosEjections=False):
        self.cache = cache
        self.allNations = allNations
        self.WANations = WANations
        self.nonWANations = nonWANations
        self.regionInfo = regionInfo
        self.doPassword = doPassword
        self.doTransition = doTransition
        self.startState = State(self.regionInfo, self.allNations, self.WANations, self.nonWANations)

        # Remove ghosts from the startState
        if ghosts:
            for ghost in ghosts:
                self.startState.remove(standardize(ghost))

        self.recipes = []

        self.passwords = []
        self.transitions = []

    def generateChaos(self):
        chaos = Chaos(self.startState)
        return [chaos]

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

