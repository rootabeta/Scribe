import requests
import config
from defusedxml import ElementTree as ET


class RegionInfo:
    region = ""  # Region name
    delegate = None  # NationInfo type to store delegate info
    targetInf = (
        0  # influence to transition, or something else if we wanna override it later
    )
    delEndos = []  # more straightup list
    WA = []  # Just a straight list, we can compare against later
    nonWA = []  # See WA
    BCROs = []  # Nationlist


class NationInfo:
    nation = ""  # Nation name
    influence = 0  # Nation inf
    WA = False  # Is WA? Good for targetting
    endorsers = []  # Who is endorsing? Flat list.
    daysSince = 0  # Days since login. Larger numbers = more likely to CTE - try ejecting rather than banning
    excempt = False  # Skip banning altogether
    conserve = 0  # Only ban until influence > threshhold


class API:
    def __init__(self, mainNation):
        self.mainNation = mainNation
        self.headers = {
            "User-Agent": f"Scribe/{config.VERSION}; developer=(Volstrostia); user={self.mainNation.replace(' ','_').lower()}"
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
            return r  # In case we need to extract other data
        elif r.status_code == 404:
            return None  # Oops! No data

        elif r.status_code == 429:  # Too many requests!
            if "Retry-After" in r.headers:
                time.sleep(
                    int(r.headers["Retry-After"]) + 0.5
                )  # Extra half a second to ensure we don't hit against the wall
            else:
                if "Ratelimit-Reset" in r.headers:
                    time.sleep(int(r.headers["Ratelimit-Reset"]) + 0.5)
                else:
                    time.sleep(
                        31
                    )  # Well, we tried. Sleeping a full 31 seconds as a last resort.

            # We have now slept - give it a second go.

            if not data:
                r = requests.get(url, headers=headers)
            else:
                r = requests.post(url, headers=headers, data=data)

            if r.status_code == 200:
                return r

            elif r.status_code == 404:
                return None

            else:
                raise requests.exceptions.RetryError(
                    "Request failed twice in a row! Please file a bug report."
                )

        else:  # Some other bad evil status code we should never see
            raise requests.exceptions.RequestException(
                "ERROR: Response code {}".format(r.status_code)
            )

    def download_file(self, url):
        print(f"Downloading {url}")
        local_filename = url.split("/")[-1]
        with requests.get(url, stream=True, headers=self.headers) as r:
            with open(local_filename, "wb") as f:
                shutil.copyfileobj(r.raw, f)

        return local_filename

    # Del inf + endos (remember, we must subtract endocount from inf)
    # https://www.nationstates.net/cgi-bin/api.cgi?nation=Lave%20Deldederady&q=census+endorsements&mode=score&scale=65+66

    def regionInfo(self, target):
        regioninfo = RegionInfo()

        r = self.perform_request(
            f"https://www.nationstates.net/cgi-bin/api.cgi?region={target}&q=wanations+nations+officers+delegate"
        )
        regionBlock = ET.fromstring(r.text)

        delegate = regionBlock.findtext("DELEGATE")
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

        nonWA = [
            nation for nation in nations if nation not in WAnations
        ]  # Get comprehended, nerd

        regioninfo.nonWA = nonWA
        regioninfo.WA = WAnations
        regioninfo.targetInf = Math.transitionCost(nonWA=len(nonWA), WA=len(WAnations))

        delInfo = self.get_nationdata(delegate)
        regioninfo.delegate = delInfo  # delegate

        # r = self.perform_request(f"https://www.nationstates.net/cgi-bin/api.cgi?nation={delegate}&q=census+endorsements&mode=score&scale=65+66")
        # delBlock = ET.fromstring(r.text)

        # delInf = float(delBlock.find("CENSUS").find("SCALE[@id='65']").findtext("SCORE"))
        # delEndos = float(delBlock.find("CENSUS").find("SCALE[@id='66']").findtext("SCORE")) # Too lazy to count endos :P
        # regioninfo.delInf = delInf - delEndos

        for RO in regionBlock.find("OFFICERS"):
            if "B" in RO.findtext("AUTHORITY") and RO.findtext(
                "NATION"
            ).lower().replace(" ", "_") != delegate.lower().replace(" ", "_"):
                # ROnation = NationInfo()
                # ROnation.nation = RO.findtext("NATION").lower().replace(" ")
                RONation = self.get_nationdata(RO.findtext("NATION"))
                if RONation:
                    regioninfo.BCROs.append(RONation)

        #                regioninfo.BCROs.append(RO.findtext("NATION"))

        return regioninfo

    def get_nationdata(self, target):
        nationinfo = NationInfo()
        target = target.lower().replace(" ", "_")
        nationinfo.nation = target

        r = self.perform_request(
            f"https://www.nationstates.net/cgi-bin/api.cgi?nation={target}&q=census+endorsements&mode=score&scale=65+66"
        )
        if not r:
            return None  # CTEd

        infBlock = ET.fromstring(r.text)

        endorsers = infBlock.findtext("ENDORSEMENTS")
        if not endorsers:
            endorsers = []
        elif "," in endorsers:
            endorsers = endorsers.split(",")
        else:
            endorsers = [endorsers]

        nationinfo.endorsers = endorsers

        nationinfo.influence = float(
            infBlock.find("CENSUS").find("SCALE[@id='65']").findtext("SCORE")
        )
        nationinfo.influence -= float(
            infBlock.find("CENSUS").find("SCALE[@id='66']").findtext("SCORE")
        )  # Delete endos, to account for the game's estimate

        return nationinfo


class Math:
    # 20 x non-WAs + 80 x WAs. Minimum cost of 500. Only up to 200 non-WAs counted.
    def transitionCost(nonWA=0, WA=0):
        if nonWA > 200:
            nonWA = 200

        rawCost = (20 * nonWA) + (80 * WA)
        if rawCost < 500:
            return 500
        return rawCost
