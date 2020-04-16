from enum import Enum
from typing import Optional
import wikitextparser as wtp
from bs4 import BeautifulSoup as BS
from dessert.model import Ingredient

# TODO: Logging

# Monkey patch wikitextparser WikiText with a couple helpers
# =============================================================================


def _wtp_get_template(self, template_name: str) -> Optional[wtp.Template]:
    for temp in self.templates:
        if temp.name == template_name:
            return temp
    return None


def _wtp_has_template(self, template_name: str) -> bool:
    return self.get_template(template_name) is not None


wtp.WikiText.get_template = _wtp_get_template
wtp.WikiText.has_template = _wtp_has_template
# =============================================================================


class State(Enum):
    # States for the wikitext ingredient parser state machine
    normal = 1
    possible_link = 2
    in_link = 3
    possible_link_end = 4
    link_ended = 5
    possible_template = 6
    in_template = 7
    possible_template_end = 8
    template_ended = 9
    possible_split = 10


class WikiParser:

    def __init__(self):
        pass

    @staticmethod
    def _trim_wikitext(wt):
        return wt.replace(r"{{Non breaking hyphen}}", "-")

    def _trim_extra_wikitext(self, ingredients: [Ingredient]) -> [Ingredient]:
        trimmed = []
        for ingredient in ingredients:
            new_name = WikiParser._trim_wikitext(ingredient.name)
            new_ingredients = self._trim_extra_wikitext(ingredient.ingredients)
            trimmed.append(Ingredient(new_name, new_ingredients))
        return trimmed

    def _add_ingredient(self, l, name, sub):
        name = name.strip()
        if len(name) == 0:
            return l
        l.append(Ingredient(name, sub))
        return l

    def _in_split_list(self, s: str) -> bool:
        return s in [" /", " or", " and", " and/or"]

    def _parse_wikitext_ingredients_list(self, wt, idx=0, open_lists=0):
        # Change <br> tags to commas to split after them
        remove_list = ["<br>", "<BR>", "<br />", "<BR />", "<br/>", "</BR>"]
        for entry in remove_list:
            wt = wt.replace(entry, ",")

        # Remove other tags (<ref> etc.) before additional parsing
        wt_orig = wt
        soup = BS(wt_orig, "html.parser")
        wt = "".join(soup.findAll(text=True, recursive=False)) or wt_orig

        # Remove formatting (naively)
        wt = wt.replace("'''''", "").replace("'''", "").replace("''", "")

        # TODO: Handle "and", "or", "and/or" and "/"

        # Text parser state machine
        state = State.normal
        ingredients = []
        temp = ""
        link_temp = ""
        template_temp = ""
        split_temp = ""
        sublist = []
        split_now = False
        while idx < len(wt):
            c = wt[idx]
            if c == "[":
                if state == State.possible_link:
                    state = State.in_link
                elif state != State.in_link and state != State.in_template:
                    state = State.possible_link
                    link_temp = ""
            elif c == "]":
                if state == State.possible_link_end:
                    state = State.link_ended
                elif state == State.in_link:
                    state = State.possible_link_end
            elif c == "{":
                if state == State.possible_template:
                    state = State.in_template
                elif state != State.in_template and state != State.in_link:
                    state = State.possible_template
                    template_temp = ""
            elif c == "}":
                if state == State.possible_template_end:
                    state = State.template_ended
                elif state == State.in_template:
                    state = State.possible_template_end
            else:
                if state in [State.possible_link, State.possible_link_end, State.possible_template, State.possible_template_end]:
                    state = State.normal
                    if link_temp:
                        temp += link_temp
                        link_temp = ""
                    elif template_temp:
                        temp += template_temp
                        template_temp = ""

            if state != State.possible_split and len(split_temp) > 0:
                temp += split_temp
                split_temp = ""

            if c == " " and state == State.possible_split:
                # Check split temp
                if self._in_split_list(split_temp):
                    # Split here
                    split_now = True
                else:
                    # No need to split, add to temp and start a new possible split (since e.g. "foo or bar" wouldn't be parsed otherwise)
                    temp += split_temp
                    split_temp = c
                    idx += 1
                    continue
            elif c == " " and state == State.normal:
                state = State.possible_split
                split_temp = c
                idx += 1
                continue

            # Split on "," even if we are possibly in a "split" (e.g. "and", "or")
            if split_now or (c == "," and (state == State.normal or state == State.possible_split)):
                state = State.normal
                if len(split_temp) > 0:
                    # Check if we need to ignore the contents of split_temp
                    if not self._in_split_list(split_temp):
                        # No need to ignore, add to temp
                        temp += split_temp
                split_temp = ""
                ingredients = self._add_ingredient(ingredients, temp, sublist)
                temp = ""
                sublist = []
                idx += 1
                split_now = False
                continue

            if c == "(" and (state == State.normal or state == State.possible_split):
                # Sublist of ingredients
                state = State.normal
                temp += split_temp
                split_temp = ""
                sublist, idx = self._parse_wikitext_ingredients_list(
                    wt, idx+1, open_lists+1)
                idx += 1
                continue

            if open_lists > 0 and c == ")" and state == State.normal:
                open_lists -= 1
                ingredients = self._add_ingredient(ingredients, temp, sublist)
                temp = ""
                sublist = []
                if open_lists == 0:
                    return ingredients, idx
                idx += 1
                continue

            if state in [State.possible_link, State.in_link, State.possible_link_end, State.link_ended]:
                link_temp += c
            elif state in [State.possible_template, State.in_template, State.possible_template_end, State.template_ended]:
                template_temp += c
            elif state == State.possible_split:
                split_temp += c
            else:
                temp += c
            idx += 1

            if state == State.link_ended:
                # Parse link in link_temp
                wt_link = wtp.parse(link_temp).wikilinks[0]
                # Add link text to temp
                temp += wt_link.text or wt_link.title
                link_temp = ""

            if state == State.template_ended:
                # Discard all templates for now
                template_temp = ""

            if state in [State.link_ended, State.template_ended]:
                state = State.normal

        if len(split_temp) > 0:
            temp += split_temp
        if len(temp) > 0:
            ingredients = self._add_ingredient(ingredients, temp, sublist)

        return ingredients, idx

    def _get_ingredients_from_infobox(self, infobox: wtp.WikiText):
        if not infobox.has_arg("main_ingredient"):
            return []
        wt_str = infobox.get_arg("main_ingredient").value.strip()
        wt = wtp.parse(wt_str)
        flatlist = wt.get_template("flatlist")
        ubl = wt.get_template("ubl")
        plainlist = wt.get_template("plainlist")
        if flatlist or plainlist:
            lst = flatlist or plainlist
            # Parse wikitext list
            list_items = lst.get_lists()[0].items
            # HACK: Join with commas and parse with our own wikitext parser to handle links and templates correctly
            wt_str = ",".join(list_items)
            return self._parse_wikitext_ingredients_list(wt_str)[0]
        if ubl:
            # Parse ubl list
            # HACK: Join with commas and parse with our own wikitext parser to handle links and templates correctly
            wt_str = ",".join([a.value.strip() for a in ubl.arguments])
            return self._parse_wikitext_ingredients_list(wt_str)[0]
        # Parse the wikitext ingredients
        return self._parse_wikitext_ingredients_list(wt_str)[0]

    def get_dessert_ingredients(self, wikitext: wtp.WikiText) -> [Ingredient]:
        # Not all dessert pages follow the same structure
        # The best pages are those that use the "infobox prepared food" or "infobox food" templates
        # Check if the page contains either "infobox food" or "infobox prepared food" templates
        infobox_list: [wtp.Template] = [
            t for t in wikitext.templates if t.name.strip().lower() in ["infobox food", "infobox prepared food"]
        ]
        if len(infobox_list) > 0:
            # Infobox found, parsing it
            infobox = infobox_list[0]
            ingredients = self._get_ingredients_from_infobox(infobox)
            if len(ingredients) > 0:
                return self._trim_extra_wikitext(ingredients)
            # No ingredients, fall though
        # TODO
        # print("Page \"%s\" has no food infobox, handling not implemented" % page_title)
        return []
