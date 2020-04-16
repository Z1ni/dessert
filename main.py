import nltk
from nltk import ngrams

from dessert.nlp import IngredientProcessor
from dessert.wiki import WikiSource, WikiParser

lemma = nltk.wordnet.WordNetLemmatizer()

def sim(word1, word2):
    w1 = set(["".join(i) for i in ngrams(word1, 2)])
    w2 = set(["".join(i) for i in ngrams(word2, 2)])
    jaettava = w1.intersection(w2)
    jakaja = w1.union(w2)
    return len(jaettava) / len(jakaja)

# mandatoryIngredients, recipe must include all these ingredients to be returned
def filterDessertByMandatoryIngredients(mandatoryIngredients, ingredients):
    if len(mandatoryIngredients) == 0:
        return True
    # haha nested for loop go brrrrrr
    for ingredient in ingredients:
        for mandatoryIngredient in mandatoryIngredients:
            # try using the ingredient name directly
            if sim(lemma.lemmatize(ingredient.name.lower()), mandatoryIngredient.lower()) > 0.5:
                mandatoryIngredients.remove(mandatoryIngredient)
                if (len(mandatoryIngredients) == 0):
                    return True
            else:
                # check ingredient's ingredients
                # Remove any non str-chars and tokenize word
                for partIngredient in ingredient.ingredients:
                    if sim(lemma.lemmatize(partIngredient.name.lower()), mandatoryIngredient.lower()) > 0.5:
                        mandatoryIngredients.remove(mandatoryIngredient)
                        if (len(mandatoryIngredients) == 0):
                            return True
    return False

def getMandatoryIngredients():
    return ["milk", 'almond']

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
                if filterDessertByMandatoryIngredients(getMandatoryIngredients(), normalized_ingredients):
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
