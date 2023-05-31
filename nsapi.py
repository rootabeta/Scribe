import requests
import time
import config
from defusedxml import ElementTree as ET
import json

def standardize(string):
    return string.lower().replace(" ","_")

# We interact with these directly
# We will get a list of these from which targetting can be done

class Nation(): # This is a frontend to the database which acts as a cache between boots
    name = ""

    # Corrected for siteside estimation - i.e., siteReported-(len(endorsers) + 1). Estimated if infUnreliable is True
    influence = 0 

    # Stats that will affect targeting beyond mere influence
    residency = 0

    # Poorly named, this is actually a unix timestamp, but I am not changing it for backwards compatability reasons
    daysSinceLogin = 0

    # Shows if this nation is in the WA, a BCRO office, and the delegacy respectively
    WA = False
    isBCRO = False
    isDel = False

    # Is the influence data deemed unreliable 
    # True when influence > 1.5 * ( ( len(endorsers) + residency) * 2)
    # This indicates that the value in influence is estimated to be that ceiling value
    # and is not the same as what the site reports; i.e., do not trust. 
    # However, it should be a safe ceiling, which is what we want anyway. Better
    # to spend less influence and have some left over that we didn't expect, than to spend
    # more than we have and only realize it too late
    infUnreliable = False 

    # This is a JSON string when packed into the database, but an array at all other times
    endorsers = ""


class Region():
    name = ""
    delegate = ""

    # Cloned region objects simulate execution of firing solutions
    # All of the below are NAMES, not Nation()
    # We can synthesize all nations by simply adding the two together
    WAnations = []
    nonWAnations = []

    # Yknow what no no BCRO is exempt lets fuck shit uppppp
    BCROnames = [] 

class math:
    # Floor of 400
    # 40 inf per nation
    def password(numNations):
        cost = numNations * 40
        floor = 400

        # floor of 400
        if cost < floor:
            return floor

        else:
            return cost

    # Stronghold is:
    # (from here: https://forum.nationstates.net/viewtopic.php?p=40506358&sid=aecd0457f993419ad2dcc228fe778a15#p40506358)
    # 20 x non-WAs + 80 x WAs. Minimum cost of 500. Only up to 200 non-WAs counted.
    def transition(numWA, numNonWA):
        # Max of 200 nonWA counted
        maxNonWA = 200
        floor = 500

        if numNonWA > maxNonWA:
            numNonWA = maxNonWA

        # 20 * nonWA and 80 * WA
        cost = (20 * numNonWA) + (80 * numWA)

        # Floor of 500
        if cost < floor:
            return floor
        else:
            return cost

    # Note: thanks, souls!
    # eject - 1/3
    # ban - 1/6
    # combined - 1/2
    # doubles for ROs

    # How much would it cost to simply eject the target?
    def ROeject(target):
        cost = (target / 3.0) * 2.0
        return cost
    
    # How much to BAN, but not eject? Not really used directly, as we only care abt existing residents, but keeps code tidy
    def ROban(target):
        cost = (target / 6.0) * 2.0
        return cost

    # How much would it cost to both eject and ban (i.e., banject)?
    def RObanject(target):
        cost = ROban(target) + ROeject(target)
        return cost

    ### Same calculations, but with delegate, who does not have 200% cost increase

    # How much would it cost to simply eject the target?
    def DELeject(target):
        cost = (target / 3.0)
        return cost
    
    # How much to BAN, but not eject? Not really used directly, as we only care abt existing residents, but keeps code tidy
    def DELban(target):
        cost = (target / 6.0)
        return cost

    # How much would it cost to both eject and ban (i.e., banject)?
    def DELbanject(target):
        cost = ROban(target) + ROeject(target)
        return cost

class API():
    def __init__(self, mainNation):
        if not mainNation:
            raise RuntimeError("Expected main nation!")
            exit()
        self.mainNation = mainNation
        self.headers = {
            "User-Agent":f"Scribe/{config.VERSION}; Developed by Volstrostia; In use by {self.mainNation}"
        }

    def perform_request(self, url, data=None):
        # From https://www.nationstates.net/pages/api.html#ratelimits, retrieved on 13 April 2023
        #    RateLimit-Limit: Set to "50"; which means that there are a total of 50 requests available in the current time window. Use instead of hardcoding.
        #    RateLimit-Remaining: How many more requests can be made within the current time window.
        #    RateLimit-Reset: Number of seconds remaining in the current time window.
        #    Retry-After: Once blocked from accessing the API, your script should wait this amount of seconds before trying again.
        #
        # A "request" is an HTTP request to the site for any amount of information and any number of shards.
        # That is, an HTTP request like this is a single request, even though it gathers information on three shards.

        # r = requests.get("https://www.nationstates.net/cgi-bin/api.cgi?nation=testlandia&q=ping",headers={"User-Agent":"cURL", "X-Password":"lolnicetry")

        if not data:  # do we POST?
            r = requests.get(url, headers=self.headers)  # no :(
        else:
            r = requests.post(url, headers=self.headers, data=data)  # yes :3

        if r.status_code == 200:  # We did it! All done!
            # If we have 1 request remaining, and 30 seconds to the window close, we need to wait 30 seconds before issuing another requestp
            # Conversely, if we have 30 requests remaining and 5 before the window changes, we can shotgun them out almost instantaneously
            # This ensures that the ratelimit is obeyed at all times
            # The downside is it means that the response may not be returned at a consistent time
            # If we are close to the rate limit, issues may take longer
            # Conversely, this also adds variability to request times, and we rarely will run into the ratelimit, so I am not concerned

            remaining = 0
            window = 0

            if "RateLimit-Remaining" in r.headers:
                remaining = int(r.headers["RateLimit-Remaining"])
            elif "RateLimit-Limit" in r.headers:
                remaining = int(r.headers["RateLimit-Limit"])
            elif "RateLimit-Policy" in r.headers:
                remaining = int(r.headers["RateLimit-Policy"].split(";")[0])
            else:
                remaining = 50  # Failsafe

            if "RateLimit-Reset" in r.headers:
                window = int(r.headers["RateLimit-Reset"])
            elif "Retry-After" in r.headers:
                window = int(r.headers["Retry-After"])
            elif "RateLimit-Policy" in r.headers:
                window = int(r.headers["RateLimit-Policy"].split("=")[1])
            else:
                window = 30

            # 30 seconds, 50 requests, can make 50/30 requests per second, so each request should take 30/50 seconds to complete
            if remaining <= 0:
                delay = window
            else:
                delay = float(window) / float(remaining)

                if delay > 0.75:
                    delay = 0.75  # 30 second wait seems silly, we have other things to do! 0.75 is the usual cap for things like FattKatt, so we use that.

            time.sleep(delay) #window / remaining

            return r  # In case we need to extract other data
        elif r.status_code == 404:
            print("Error 404")
            return None  # Oops! No data

        elif r.status_code == 429:  # Too many requests!
            if "Retry-After" in r.headers:
                print(
                    f"Hit hard rate limit! Sleeping for {r.headers['Retry-After']} seconds"
                )
                time.sleep(
                    int(r.headers["Retry-After"]) + 0.5
                )  # Extra half a second to ensure we don't hit against the wall
            else:
                if "Ratelimit-Reset" in r.headers:
                    print(
                        f"Hit soft rate limit (no more requests). Sleeping for {r.headers['Ratelimit-Reset']} seconds"
                    )
                    time.sleep(int(r.headers["Ratelimit-Reset"]) + 0.5)
                else:
                    time.sleep(
                        31
                    )  # Well, we tried. Sleeping a full 31 seconds as a last resort.

            # We have now slept - give it a second go.

            if not data:
                r = requests.get(url, headers=self.headers)
            else:
                r = requests.post(url, headers=self.headers, data=data)

            if r.status_code == 200:
                # Sleemp - same code as above
                remaining = 0
                window = 0
                if "RateLimit-Remaining" in r.headers:
                    remaining = int(r.headers["RateLimit-Remaining"])
                elif "RateLimit-Limit" in r.headers:
                    remaining = int(r.headers["RateLimit-Limit"])
                elif "RateLimit-Policy" in r.headers:
                    remaining = int(r.headers["RateLimit-Policy"].split(";")[0])
                else:
                    remaining = 50  # Failsafe

                if "RateLimit-Reset" in r.headers:
                    window = int(r.headers["RateLimit-Reset"])
                elif "Retry-After" in r.headers:
                    window = int(r.headers["Retry-After"])
                elif "RateLimit-Policy" in r.headers:
                    window = int(r.headers["RateLimit-Policy"].split("=")[1])
                else:
                    window = 30

                if remaining <= 0:
                    delay = float(window)
                else:
                    delay = float(window) / float(remaining)

                    if delay > 0.75:
                        delay = 0.75

                time.sleep(delay)

                return r

            elif r.status_code == 404:
                print("Error 404")
                return None

            else:
                raise requests.exceptions.RetryError(
                    "Request failed twice in a row! Please file a bug report."
                )

        else:  # Some other bad evil status code we should never see
            raise requests.exceptions.RequestException(
                "ERROR: Response code {}".format(r.status_code)
            )

#
#        return nationinfo

    #Nation name, WA status, who is endorsing it, days since last active, influence, timestamp of last cache refresh, RO status, including delegacy
    # RO and delegacy are elsewhere
    def nationInfo(self, nation):
        nation = standardize(nation)

        r = self.perform_request(f"https://www.nationstates.net/cgi-bin/api.cgi?nation={nation}&q=lastlogin+census+wa+endorsements+region&mode=score&scale=65+66+80")
        if not r:
            return None

        nationinfo = Nation()
        # 0 - Name (duh)
        nationinfo.name = nation

        nationData = ET.fromstring(r.text)

        # 1 - Endorsers
        endorsers = nationData.findtext("ENDORSEMENTS")

        if not endorsers:
            endorsers = []
        elif "," in endorsers:
            endorsers = endorsers.split(",")
        else:
            endorsers = [endorsers]
        nationinfo.endorsers = [standardize(endorser) for endorser in endorsers]

        # 2 - Region
        nationinfo.region = standardize(nationData.findtext("REGION"))

        # 3 - WA
        if nationData.findtext("UNSTATUS") == "Non-member":
            nationinfo.WA = False
        else:
            nationinfo.WA = True

        # 4 - Delegate
        if nationData.findtext("UNSTATUS") == "WA Delegate":
            nationinfo.isDel = True
        else:
            nationinfo.isDel = False
        
        # 5 - Last login
        nationinfo.lastlogin = int(nationData.findtext("LASTLOGIN"))

        # 6 - Days resident in region
        nationinfo.residency = float(
            nationData.find("CENSUS").find("SCALE[@id='80']").findtext("SCORE")
        )

        # 7 - Influence
        # Get influence and reverse in-game estimation
        # Get estimated influence
        nationinfo.influence = float(
            nationData.find("CENSUS").find("SCALE[@id='65']").findtext("SCORE")
        )
        # Remove influence from endorsements next update
        nationinfo.influence -= float(
            nationData.find("CENSUS").find("SCALE[@id='66']").findtext("SCORE")
        )  # Delete endos, to account for the game's estimate
        # Remove standard influence growth next update
        nationinfo.influence -= 1 

        # Influence is too high for how many endos they have and how long they've been here
        # They are likely carrying influence from elsewhere. We will estimate it ourselves. 
        if nationinfo.influence > (10 * (( len(nationinfo.endorsers) + nationinfo.residency) * 2)):
            # This is the ceiling of where their influence is likely to be
            nationinfo.influence = (nationinfo.residency + len(nationinfo.endorsers)) * 2 
            nationinfo.influence *= 10 # Account for the possibility of endo loss. This is a ceiling measure, so bigger > smaller
            nationinfo.infUnreliable = True # We had to manually guess at influence - we could be way over or under
            # However, this value is a reasonable guess for an upper bound

        return nationinfo

    def regionInfo(self, region):
        region = standardize(region)

        r = self.perform_request(f"https://www.nationstates.net/cgi-bin/api.cgi?region={region}&q=wanations+nations+officers+delegate")
        if not r:
            return None
    
        regioninfo = Region()
        regioninfo.name = region

        regionBlock = ET.fromstring(r.text)

        delegate = standardize(regionBlock.findtext("DELEGATE"))
        nations = regionBlock.findtext("NATIONS")
        WAnations = regionBlock.findtext("UNNATIONS")

        if not nations:
            nations = []
        elif ":" in nations:
            nations = nations.split(":")
        else:
            nations = [nations]

        if not WAnations:
            WAnations = []
        elif "," in WAnations:
            WAnations = WAnations.split(",")
        else:
            WAnations = [WAnations]

        # Nation names are now standardized
        WAnations = [standardize(nation) for nation in WAnations]

        # Compare standardized nation list to WAnations, if it's being compared it's resident, so if not found, non-WA
        nonWA = [
            standardize(nation) for nation in nations if standardize(nation) not in WAnations
        ]  # Get comprehended, nerd


        regioninfo.nonWAnations = nonWA
        regioninfo.WAnations = WAnations

        regioninfo.delegate = standardize(delegate)

        for RO in regionBlock.find("OFFICERS"):
            # BCROs who are NOT the delegate
            if "B" in RO.findtext("AUTHORITY") and standardize(RO.findtext("NATION")) != delegate:
                regioninfo.BCROnames.append(standardize(RO.findtext("NATION")))

        return regioninfo
