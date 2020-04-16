import re
import nltk
from dessert.model import Ingredient


class IngredientProcessor:

    def __init__(self):
        pass

    def _normalize(self, ingredient_name: str) -> str:
        # TODO
        # Use a stemmer and/or dictionary
        # TODO: Remove stop words (e.g. ".")
        # Remove "and", "and/or" prefix left by the splitting
        # TODO: Move the prefix removing to the split stage, see WikiParser._parse_wikitext_ingredients_list in parser.py
        ingredient_name = re.sub(
            r"^and(/or)?\s", "", ingredient_name, flags=re.IGNORECASE)
        return ingredient_name

    def normalize_ingredients(self, ingredients: [Ingredient]) -> [Ingredient]:
        normalized = []
        for ingredient in ingredients:
            normalized.append(Ingredient(self._normalize(
                ingredient.name), self.normalize_ingredients(ingredient.ingredients)))
        return normalized
