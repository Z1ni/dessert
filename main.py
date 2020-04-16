from dessert.wiki import WikiSource, WikiParser
from dessert.model import Ingredient
from dessert.nlp import IngredientProcessor


if __name__ == "__main__":
    ws = WikiSource()
    wp = WikiParser()
    ip = IngredientProcessor()

    # Get list of all available desserts
    dessert_pages = ws.get_dessert_list()

    # Get each dessert as wikitext
    wikitexts = ws.get_dessert_wikitexts(dessert_pages)

    parsed_count = 0
    total_desserts = len(dessert_pages)
    last_line_len = 0
    with open("list.txt", "w", encoding="utf-8") as f:
        # Parse ingredients from the wikitext
        for title, wt in wikitexts:
            # Print some status info
            line = "Parsing ingredients: %s" % title
            print(" " * last_line_len, end="\r")
            last_line_len = len(line)
            print(line, end="\r")

            # Parse ingredients
            ingredients = wp.get_dessert_ingredients(wt)
            if len(ingredients) > 0:
                # Try to process ingredients (normalize names)
                normalized_ingredients = ip.normalize_ingredients(ingredients)
                f.write("\n")
                f.write("%s:\n" % title)
                for i in normalized_ingredients:
                    f.write("- %s\n" % i.name)
                parsed_count += 1
    print()

    print("Got ingredients for %d desserts (%d / %d, %.2f %%)"
          % (parsed_count,
             parsed_count,
             total_desserts,
             (float(parsed_count) / float(total_desserts) * 100.0)))
