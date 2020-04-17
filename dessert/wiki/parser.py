from enum import Enum
from typing import Optional

import wikitextparser as wtp
from bs4 import BeautifulSoup
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
        # Strings that indicate a split. These are handled the same way
        # as commas.
        # All string here must start with a whitespace (" ")
        return s in [" /", " or", " and", " and/or"]

    def _parse_wikitext_ingredients_list(self, wt, idx=0, open_lists=0):
        # Change <br> tags and newlines to commas to split the ingredients after them
        remove_list = ["<br>", "<BR>", "<br />",
                       "<BR />", "<br/>", "</BR>", "\n"]
        for entry in remove_list:
            wt = wt.replace(entry, ",")

        # Remove other tags (<ref> etc.) before additional parsing
        wt_orig = wt
        soup = BeautifulSoup(wt_orig, "html.parser")
        wt = "".join(soup.findAll(text=True, recursive=False)) or wt_orig

        # Remove formatting (naively)
        wt = wt.replace("'''''", "").replace("'''", "").replace("''", "")

        # Text parser state machine
        # This will go through the wikitext character by character and parse links ("[[link]]"),
        # split on commas etc. and remove templates ("{{stuff}}").
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
                    # "[[" seen, we're in a link
                    state = State.in_link
                elif state != State.in_link and state != State.in_template:
                    # Links start with two "[", we're in the first one
                    state = State.possible_link
                    link_temp = ""
            elif c == "]":
                if state == State.possible_link_end:
                    # "]]" seen, link ended
                    state = State.link_ended
                elif state == State.in_link:
                    # Links end with two "]", we're in the first one
                    state = State.possible_link_end
            elif c == "{":
                if state == State.possible_template:
                    # "{{" seen, we're in a template
                    state = State.in_template
                elif state != State.in_template and state != State.in_link:
                    # Templates start with two "{", we're in the first one
                    state = State.possible_template
                    template_temp = ""
            elif c == "}":
                if state == State.possible_template_end:
                    # "}}" seen, template ended
                    state = State.template_ended
                elif state == State.in_template:
                    # Templates end with two "}", we're in the first one
                    state = State.possible_template_end
            else:
                if state in [State.possible_link, State.possible_link_end, State.possible_template, State.possible_template_end]:
                    # If the state is "possible" something after two characters, we're not in a link/template
                    # Set the state back to normal
                    state = State.normal
                    # If temporary variables have something in them, add them to the temp
                    if link_temp:
                        temp += link_temp
                        link_temp = ""
                    elif template_temp:
                        temp += template_temp
                        template_temp = ""

            # If the state changed from possible_split to some other, add split_temp
            # contents to the default temp variable.
            if state != State.possible_split and len(split_temp) > 0:
                temp += split_temp
                split_temp = ""

            # If the character is a space, check if we need to split
            if c == " " and state == State.possible_split:
                # Check if the split temp contains something that
                # warrants a split.
                if self._in_split_list(split_temp):
                    # Split here
                    split_now = True
                else:
                    # No need to split, add to temp and start a new possible split
                    # (since e.g. "foo or bar" wouldn't be parsed otherwise)
                    temp += split_temp
                    split_temp = c
                    idx += 1
                    continue
            elif c == " " and state == State.normal:
                # Space changes the state to possible split
                # In this state we collect all the seen characters to split_temp
                # and check on the next whitespace if we need to split there.
                # This is for splitting on "and" and "or" etc.
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
                # Temp contains now a one "ingredient", add it to the list
                ingredients = self._add_ingredient(ingredients, temp, sublist)
                # Reset variables and start parsing a new ingredient
                temp = ""
                sublist = []
                idx += 1
                split_now = False
                continue

            # "(" starts a "sublist", which is a list of ingredients that this
            # current ingredient contains. E.g. "juice (water, sugar, color)".
            if c == "(" and (state == State.normal or state == State.possible_split):
                # Sublist of ingredients
                state = State.normal
                temp += split_temp
                split_temp = ""
                # The list is parsed with this same method recursively
                sublist, idx = self._parse_wikitext_ingredients_list(
                    wt, idx+1, open_lists+1)
                idx += 1
                continue

            # ")" ends a "sublist" only if the state is normal and there are open lists.
            if open_lists > 0 and c == ")" and state == State.normal:
                # By using the opne_lists counter we can parse multiple nested lists without problems.
                open_lists -= 1
                ingredients = self._add_ingredient(ingredients, temp, sublist)
                temp = ""
                sublist = []
                if open_lists == 0:
                    return ingredients, idx
                idx += 1
                continue

            if state in [State.possible_link, State.in_link, State.possible_link_end, State.link_ended]:
                # If we're in a link, collect characters to link_temp
                link_temp += c
            elif state in [State.possible_template, State.in_template, State.possible_template_end, State.template_ended]:
                # If we're in a template, collect characters to template_temp
                template_temp += c
            elif state == State.possible_split:
                # If we're in a "split" ("and", "or", etc.), collect characters to split_temp
                split_temp += c
            else:
                # Otherwise collect characters to temp
                temp += c
            # Advance the position in the wikitext string
            idx += 1

            if state == State.link_ended:
                # Link ended
                # Parse link in link_temp
                wt_link = wtp.parse(link_temp).wikilinks[0]
                # Add link text to temp
                temp += wt_link.text or wt_link.title
                link_temp = ""

            if state == State.template_ended:
                # Template ended
                # Discard all templates for now
                template_temp = ""

            if state in [State.link_ended, State.template_ended]:
                # Change the state to be normal after link/template end
                state = State.normal

        # If the split temp variable has something in it, add it to temp
        if len(split_temp) > 0:
            temp += split_temp
        # If temp contains something, add it to the ingredients as we're done parsing the wikitext
        if len(temp) > 0:
            ingredients = self._add_ingredient(ingredients, temp, sublist)

        return ingredients, idx

    def _get_ingredients_from_infobox(self, infobox: wtp.WikiText):
        # Get ingredient wikitext string from the infobox template
        if not infobox.has_arg("main_ingredient"):
            return []
        wt_str = infobox.get_arg("main_ingredient").value.strip()
        # Parse the wikitext into a WikiText object
        wt = wtp.parse(wt_str)
        # Try to get possible templates from the wikitext
        flatlist = wt.get_template("flatlist")
        ubl = wt.get_template("ubl")
        plainlist = wt.get_template("plainlist")
        # If we found matching list templates, parse them directly
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
        # TODO: Handle pages that do not have food infobox
        # print("Page \"%s\" has no food infobox, handling not implemented" % page_title)
        return []
