import os
from pathlib import Path
from urllib.parse import quote
import requests
import wikitextparser as wtp


class WikiSource:

    def __init__(self):
        session = requests.Session()
        session.headers.update({
            "User-Agent": "dessertFetcher/0.1.0",
            "Accept-Encoding": "gzip"
        })
        self._s = session
        self._wiki_request_count = 0

    def _request_raw_wikitext(self, page_titles: [str]) -> [(str, wtp.WikiText)]:
        cache_path = Path("wikitext")
        wts = []
        titles = page_titles[:]

        # Create wikitext cache folder if needed
        try:
            os.mkdir("wikitext")
        except FileExistsError:
            pass

        # Check wikitext cache
        for page in page_titles:
            wt_path = cache_path / ("%s.txt" % quote(page))
            if os.path.isfile(wt_path):
                with open(wt_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    wts.append((page, wtp.parse(content)))
                titles.remove(page)

        if len(titles) == 0:
            return wts

        # Request wikitext for the given pages
        # We request multiple pages at the same time to reduce request load to the
        # Wikipedia servers. See https://www.mediawiki.org/wiki/API:Etiquette
        url = "https://en.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "format": "json",
            "titles": "|".join(titles),
            "prop": "revisions",
            "formatversion": "2",
            "rvprop": "content",
            "rvslots": "*",
            "redirects": "1",
            "maxlag": "5"
        }

        self._wiki_request_count += 1

        r = requests.get(url, params=params)
        r.raise_for_status()

        j = r.json()

        if not j["batchcomplete"]:
            # This has not happened during development, so it's probably fine to not handle this
            raise Exception("Batch not complete")

        normalizations = j["query"].get("normalized") or []
        redirects = j["query"].get("redirects") or []
        orig_titles = {}
        # Convert the redirect / normalization dicts to our own dict
        # Example:
        # {
        #   "from": "Ice cream soda",
        #   "to": "Ice cream float"
        # }
        # becomes:
        # {
        #   "Ice cream float": "Ice cream soda"
        # }
        for ls in [redirects, normalizations]:
            for key, value in {entry["to"]: entry["from"] for entry in ls}.items():
                orig_titles[key] = value

        for page in j["query"]["pages"]:
            if page.get("missing"):
                # We tried to get a page that does not exist, move to the next page
                # TODO: Log
                continue
            title = page["title"]
            orig_title = orig_titles.get(title) or title
            content = page["revisions"][0]["slots"]["main"]["content"]
            # Parse the wikitext and add it to the list
            wts.append((title, wtp.parse(content)))
            # Store to naive filesystem cache
            # The cache won't expire on its own, so the user must delete the cache folder to expire the cache
            # The filename will be the URLEncoded version of the title
            wt_path = cache_path / ("%s.txt" % quote(orig_title))
            with open(wt_path, "w", encoding="utf-8") as f:
                f.write(content)

        return wts

    def _get_wikitext(self, page_title: str) -> wtp.WikiText:
        return self._request_raw_wikitext([page_title])[0][1]

    def _get_multiple_wikitext(self, page_titles: [str]) -> [(str, wtp.WikiText)]:
        print("Getting %d wiki pages" % len(page_titles))
        work_items = []
        wikitexts = []
        got_count = 0
        total_count = len(page_titles)
        start_req_count = self._wiki_request_count
        for title in page_titles:
            work_items.append(title)
            # Request 50 pages at once (the maximum allowed by MediaWiki)
            if len(work_items) >= 50:
                # Request pages
                result = self._request_raw_wikitext(work_items)
                wikitexts.extend(result)
                got_count += len(result)
                work_items = []
                print("%d / %d (%.2f %%)"
                      % (got_count, total_count, (float(got_count) / float(total_count) * 100.0)))
        if len(work_items) > 0:
            # Request pages
            result = self._request_raw_wikitext(work_items)
            wikitexts.extend(result)
            got_count += len(result)
            work_items = []
            print("%d / %d (%.2f %%)"
                  % (got_count, total_count, (float(got_count) / float(total_count) * 100.0)))
        print()

        end_req_count = self._wiki_request_count
        print("Made %d request(s) to Wikipedia" %
              (end_req_count - start_req_count,))

        return wikitexts

    def get_dessert_list(self) -> [str]:
        dessert_page = self._get_wikitext("List of desserts")

        print("Parsing dessert list page")
        # Get section named "By type"
        by_type = [s for s in dessert_page.sections if s.title == "By type"][0]
        # Get all lists in the section
        lists = by_type.get_lists()
        # Flatten the lists
        dessert_pages = set()
        for letter_list in lists:
            for item in letter_list.items:
                # Parse page WikiLinks
                link = wtp.parse(item).wikilinks[0]
                # Add the page title to the title list
                dessert_pages.add(link.title)

        print("Found %d dessert pages" % len(dessert_pages))

        return list(dessert_pages)

    def get_dessert_wikitext(self, page_title) -> wtp.WikiText:
        return self._get_wikitext(page_title)

    def get_dessert_wikitexts(self, page_titles: [str]) -> [(str, wtp.WikiText)]:
        return self._get_multiple_wikitext(page_titles)
