import sqlite3
from nsapi import API, standardize, Nation, Region
from datetime import datetime, timedelta
import json

class Cache():
    def __init__(self, mainNation, region):
        if not mainNation:
            raise RuntimeError("Main nation is required!")
        self.mainNation = standardize(mainNation)
        self.region = standardize(region)
        self.api = API(mainNation)

        # Set up operating environment
        self.build_database()
        self.loadAPI()

        # Build the nation list from cache
        # This way, even if we never refresh, we can still use data
        #self.nationList = self.buildNationLists() 

        self.nationList = []
        self.nationListNonWA = []
        self.nationListWA = []


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

        # Clear nationlist
        self.nationList = []

        for nation in self.regionData.WAnations:
            nationData = self.fetch_nation(nation)
            self.nationList.append(nationData)
            self.nationListWA.append(nationData)

        for nation in self.regionData.nonWAnations:
            nationData = self.fetch_nation(nation)
            self.nationList.append(nationData)
            self.nationListNonWA.append(nationData)

        self.nationList = sorted(self.nationList, key=lambda x: x.influence)
        self.nationListWA = sorted(self.nationListWA, key=lambda x: x.influence)
        self.nationListNonWA = sorted(self.nationListNonWA, key=lambda x: x.influence)

        return self.nationList

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

            return True

        # We found a nation, and its timestamp was recent
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

        for nation in (self.regionData.WAnations + self.regionData.nonWAnations): 
            if self.refresh_nation(nation, age, self.regionData.BCROnames):
                verb = "Refreshed"
            else:
                verb = "Found cached data for"
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
            secondsEstimated = secondsElapsed / percentComplete # 15s, 0.5 complete
            remainingEstimated = secondsEstimated - secondsElapsed

            elapsed = timedelta(seconds=int(secondsElapsed))
            remaining = timedelta(seconds=int(remainingEstimated))

            statusBar = f"[{spinner[count % len(spinner)]}] {progress} refreshed. Last operation: {verb} {nation}. Time elapsed: {elapsed}. Est. Time Remaining: {remaining}"

            while len(statusBar) < lastLen: 
                statusBar += " "

            lastLen = len(statusBar)
            print(statusBar, end="\r", flush=True)

        
        print(f"[+] Finished updating cache! Time taken: {elapsed}" + " " * lastLen)
        print("Compiling nation lists")
        self.buildNationLists()
        print("Cache refresh complete.")
