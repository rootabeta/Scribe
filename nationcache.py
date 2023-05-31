import sqlite3
from nsapi import API, standardize, Nation, Region
from datetime import datetime, timedelta
import json
from os import get_terminal_size
import random

class Cache():
    def __init__(self, mainNation, region):
        if not mainNation:
            raise RuntimeError("Main nation is required!")
        self.mainNation = standardize(mainNation)
        self.region = standardize(region)
        self.api = API(mainNation)


        self.nationList = []
        self.nationListNonWA = []
        self.nationListWA = []

        # Build the nation list from cache
        # This way, even if we never refresh, we can still use data

        # Set up operating environment
        self.build_database()
        self.loadAPI()

        # Build nationlists
        self.buildNationLists()

    def fastForward(self, updates):
        # Go through cache and build nation list
        # DOES NOT make requests

        # Clear nationlist
        self.nationList = []
        self.nationListNonWA = []
        self.nationListWA = []

        for nation in self.regionData.WAnations:
            nationData = self.fetch_nation_cached(nation)
            if not nationData:
                continue

            influenceAdjustment = len(nationData.endorsers) 
            influenceAdjustment += 1

            nationData.influence += (influenceAdjustment * updates)

            self.nationList.append(nationData)
            self.nationListWA.append(nationData)

        for nation in self.regionData.nonWAnations:
            nationData = self.fetch_nation_cached(nation)
            if not nationData:
                continue

            influenceAdjustment = len(nationData.endorsers) # 0
            influenceAdjustment += 1 # Natural growth

            nationData.influence += influenceAdjustment * updates

            self.nationList.append(nationData)
            self.nationListNonWA.append(nationData)

        self.nationList = sorted(self.nationList, key=lambda x: x.influence)
        self.nationListWA = sorted(self.nationListWA, key=lambda x: x.influence)
        self.nationListNonWA = sorted(self.nationListNonWA, key=lambda x: x.influence)

    # Instantiate API and set regionData 
    def loadAPI(self):
        self.regionData = self.api.regionInfo(self.region)

    def dateRange(self, region=None):
        if not region:
            region = self.region
        else:
            region = standardize(region)

        #select cacheRefreshed from cache where region = 'violetia' order by cacheRefreshed
        con = sqlite3.connect("cache.db")
        cur = con.cursor()
        res = cur.execute("select cacheRefreshed from cache where region = ? order by cacheRefreshed", (region,))
        rows = res.fetchall()
        con.close()

        times = [row[0] for row in rows]
        newest = max(times)
        oldest = min(times)
        
        return newest, oldest

    def fetch_nation(self, nation):
        seeker = standardize(nation)
        for nation in self.nationList:
            if seeker == nation.name:
                return nation

        return None

    # Return TRUE value from DB. Does not account for forecast!
    # However, it does not require an existing nation list, and is faster!
    def fetch_nation_cached(self, nation):
        nation = standardize(nation)
        nationData = Nation()

        con = sqlite3.connect("cache.db")
        cur = con.cursor()
        cur.execute("SELECT region, influence, residency, daysSinceLogin, endorsers, WA, isBCRO, isDel, infUnreliable FROM cache WHERE nation = ?",
            (
             nation, 
            )
        )

        row = cur.fetchone()

        # Guardian against empty data
        if not row:
            print(f"{nation} not in DB!")
            return None

        nationData.name = nation
        nationData.region = row[0]
        nationData.influence = row[1]
        nationData.residency = row[2]
        nationData.daysSinceLogin = row[3]
        nationData.endorsers = json.loads(row[4])
        nationData.WA = True if row[5] == 1 else False

        # These two can be fetched from the region data directly for maximum accuracy
        #nationData.isBCRO = True if row[6] == 1 or nation in self.region.BCROnames else False
        #nationData.isDel = True if row[7] == 1 or nation == self.region.delegate else False

        nationData.isBCRO = True if nation in self.regionData.BCROnames else False
        nationData.isDel = True if nation == self.regionData.delegate else False

        nationData.infUnreliable = True if row[8] == 1 else False

        return nationData

    def buildNationLists(self):
        # Go through cache and build nation list
        # DOES NOT make requests

        # Clear nationlists
        self.nationList = []
        self.nationListNonWA = []
        self.nationListWA = []

        for nation in self.regionData.WAnations:
            nationData = self.fetch_nation_cached(nation)
            if not nationData:
                continue
            self.nationList.append(nationData)
            self.nationListWA.append(nationData)

        for nation in self.regionData.nonWAnations:
            nationData = self.fetch_nation_cached(nation)
            if not nationData:
                continue
            self.nationList.append(nationData)
            self.nationListNonWA.append(nationData)

        self.nationList = sorted(self.nationList, key=lambda x: x.influence)
        self.nationListWA = sorted(self.nationListWA, key=lambda x: x.influence)
        self.nationListNonWA = sorted(self.nationListNonWA, key=lambda x: x.influence)

    def fetchRegionInfo(self):
        return self.regionData

    # Return nation list for other targeting to make use of
    def fetchNationLists(self):
        return self.nationList, self.nationListWA, self.nationListNonWA

    # Ensure DB exists in good format
    def build_database(self):
        statement = "CREATE TABLE IF NOT EXISTS cache(nation TEXT NOT NULL PRIMARY KEY, region TEXT, influence INTEGER, residency INTEGER, daysSinceLogin INTEGER, endorsers TEXT, WA INTEGER, isBCRO INTEGER, isDel INTEGER, infUnreliable INTEGER, cacheRefreshed INTEGER)"
        con = sqlite3.connect("cache.db")
        cur = con.cursor()
        cur.execute(statement)
        con.commit()
        con.close()

    # Determine if a nation needs to be refreshed, and if so, do so
    def refresh_nation(self, nation, age, bcronames=[], verbose=False):
        nation = standardize(nation)
        timestamp = int(datetime.now().timestamp())
        doRefresh = False

        con = sqlite3.connect("cache.db")
        cur = con.cursor()
        cur.execute("SELECT nation, region, cacheRefreshed FROM cache WHERE nation = ?",
            (
             nation,
            )
        )

        row = cur.fetchone()
        nationinfo = None

        if not row:
            if verbose:
                print(f"Nation {nation} not found in cache for {self.region}")
            nationinfo = self.api.nationInfo(nation)
            if nationinfo:
                cur.execute("INSERT INTO cache (nation, region, influence, residency, daysSinceLogin, endorsers, WA, isBCRO, isDel, infUnreliable, cacheRefreshed) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                    (
                     nationinfo.name,
                     nationinfo.region,
                     nationinfo.influence,
                     nationinfo.residency,
                     nationinfo.daysSinceLogin,
                     json.dumps(nationinfo.endorsers),
                     1 if nationinfo.WA else 0,
                     1 if nationinfo.name in bcronames else 0,
                     1 if nationinfo.isDel else 0,
                     1 if nationinfo.infUnreliable else 0,
                     timestamp
                    )
                )
                con.commit()
            con.close()
            return True
        
        elif row[2] < timestamp - age:
            if verbose:
                print(f"Nation {nation} out of date")
            nationinfo = self.api.nationInfo(nation)
            # TODO: UPDATE cache SET crap = val, crap2 = val2 WHERE name = nation
            # I mean, if it moves elsewhere, we already made the request, might as well stick it in
            # Who knows, maybe it happened to move to another region we care about
            nationinfo = self.api.nationInfo(nation)
            if nationinfo:
                cur.execute("UPDATE cache SET region = ?, influence = ?, residency = ?, daysSinceLogin = ?, endorsers = ?, WA = ?, isBCRO = ?, isDel = ?, infUnreliable = ?, cacheRefreshed = ? WHERE nation = ?",
                    (
                     nationinfo.region,
                     nationinfo.influence,
                     nationinfo.residency,
                     nationinfo.daysSinceLogin,
                     json.dumps(nationinfo.endorsers),
                     1 if nationinfo.WA else 0,
                     1 if nationinfo.name in bcronames else 0,
                     1 if nationinfo.isDel else 0,
                     1 if nationinfo.infUnreliable else 0,
                     timestamp,
                     nationinfo.name
                    )
                )
                con.commit()

            con.close()
            return True

        # We found a nation, and its timestamp was recent
        con.close()
        return False

    def purge(self, routine=True):
        if routine:
            print(f"[*] Purging nations that are no longer in {self.region} from cache")
        else:
            print(f"[!] Initiating purge of all regions in {self.region} from cache!")

        purged = 0
        con = sqlite3.connect("cache.db")
        cur = con.cursor()
        # Select cached nations that we previously saw in target
        res = cur.execute("SELECT nation FROM cache WHERE region = ?",(self.region,))  
        rows = res.fetchall()
        cachedNations = [row[0] for row in rows]
        for nation in cachedNations:
            # Is that nation in the list of nations last time we checked the API?
            # Alternatively, in the event of a non-routine purge (i.e. user requested), delete no matter what
            if not routine or (nation not in self.regionData.WAnations and nation not in self.regionData.nonWAnations):
                cur.execute("DELETE FROM cache WHERE nation = ?", (nation,))
                con.commit()
                purged += 1
        con.close()

        print(f"[+] Cache purge complete - purged {purged} nations from cache")

    # Refresh all nations in the region that do not have a valid and current cache entry
    # Age is how many seconds before a cache entry should expire and be considered invalid
    # Default is 6 hours
    def refresh(self, age=21600): 
        print(f"Refreshing cache for {self.region}, please wait")
        print("This may take anywhere from several minutes to hours or even overnight")
        self.loadAPI()
        numNationsTotal = len(self.regionData.WAnations + self.regionData.nonWAnations)

        # Whenever we instantiate a Cache, we get a fresh list of nations
        # This can then be used to update the cache. 
        # Any items in the cache but not in the site list will be removed from the cache.
        self.purge()

        print("Ready to refresh cache")
        print(f"Estimated maximum number of requests: {numNationsTotal}")
        seconds = numNationsTotal # About 1 request per second, mb a little more, for a worst-case ceiling
        # People prefer being done ahead of schedule as opposed to the alternative
        # Still, I strive for accuracy in all things

        print("ESTIMATED WORST-CASE TIMES:")
        worstTime = timedelta(seconds=int(seconds))
        print(f"Time: {worstTime}")
        print(f"Time in seconds: {int(seconds)}s")
        print("Running after a cache has been established will accelerate refreshes")
        print("Cache is updated continuously, so immediately resuming the refresh later will pick up roughly where you left off")
        print("Press Ctrl-C at any time to interrupt the refresh")

        count = 0
        spinner = ["/","-","\\","|"]
        startTime = int(datetime.now().timestamp())

        bootMsg = "[|] Starting cache refresh. This may take a while."
        lastLen = len(bootMsg)
        print(bootMsg,end="\r",flush=True)
        requested = 0
        skipped = 0
        allNationsInRegion = self.regionData.WAnations + self.regionData.nonWAnations
        # Randomize order
        random.shuffle(allNationsInRegion)
        #for nation in (self.regionData.WAnations + self.regionData.nonWAnations): 

        for nation in allNationsInRegion:
            if self.refresh_nation(nation, age, self.regionData.BCROnames):
                verb = "Refreshed"
              #  requested += 1

            else:
                verb = "Found cached data for"
              #  skipped += 1

            count += 1
            progress = f"{count}/{numNationsTotal}"
            secondsElapsed = int(datetime.now().timestamp()) - startTime
            #elapsed = timedelta(seconds=secondsElapsed)
            # 30 seconds to process 15 requests
            # We have 30 requests, so 2x 

            # X% of the way done took Y seconds
            # Therefore Y seconds is X% of the total time
            # Thus, Y / (doneR/totalR) = Final
            # As (doneR/totalR) -> 1, Final -> Y
            # Then, Final - Y will give the estimated number of seconds remaining

            percentComplete = (float(count) / float(numNationsTotal))

            if numNationsTotal - skipped > 0:
                requestsCompleted = (float(count - skipped) / float(numNationsTotal - skipped))
            else:
                requestsCompleted = 0

            if requestsCompleted > 0:
                secondsEstimated = secondsElapsed / requestsCompleted # Factor out DB cached lookups
            else:
                secondsEstimated = secondsElapsed / percentComplete

            remainingEstimated = secondsEstimated - secondsElapsed

            elapsed = timedelta(seconds=int(secondsElapsed))
            remaining = timedelta(seconds=int(remainingEstimated))

            if secondsElapsed:
                # Now that nation order is randomized, we can use this as an accurate example again
                reqspersec = round(percentComplete,2) 
                #reqspersec = round(float(requested) / float(secondsElapsed), 2)
            else:
                reqspersec = "1.00" # Sure, whatever
            

            reqspersecMsg = " (currently getting {reqspersec} r/s)"
            statusBar = f"[{spinner[count % len(spinner)]}] {progress} refreshed. Last operation: {verb} {nation}. Time elapsed: {elapsed}. Estimated Time Remaining: {remaining}"

            if len(statusBar + reqspersecMsg) < get_terminal_size()[1]:
                statusBar += reqspersecMsg

            while len(statusBar) < lastLen: #and len(statusBar) < get_terminal_size()[1]: 
                statusBar += " "

            lastLen = len(statusBar)

            print(statusBar, end="\r", flush=True)

        print(f"[+] Finished updating cache! Time taken: {elapsed}" + " " * lastLen)
        print("Compiling nation lists")
        self.buildNationLists()
        print("Cache refresh complete.")
