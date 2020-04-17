import re

import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

from dessert.model import Ingredient


class IngredientProcessor:

    def __init__(self):
        # Initialize NLTK resources
        nltk.download("stopwords")
        nltk.download("punkt")
        # Extend NLTK stopwords
        self._stopwords = stopwords.words("english")
        self._stopwords.extend([
            ".", "etc.", "etc", "sometimes"
        ])

    def _normalize(self, ingredient_name: str) -> str:
        # TODO: Use a stemmer and/or dictionary
        # If the name begins with something that ends with ":", remove everything before the ":"
        # This removes cases like "Filling: something" and "Crust: something", etc.
        ingredient_name = re.sub(r"^.*?:", "", ingredient_name)
        # Tokenize
        tokens = word_tokenize(ingredient_name)
        # Remove stop words
        filtered = [w for w in tokens if not w in self._stopwords]

        filtered_name = " ".join(filtered)
        return filtered_name

    def normalize_ingredients(self, ingredients: [Ingredient]) -> [Ingredient]:
        normalized = []
        for ingredient in ingredients:
            normalized.append(Ingredient(self._normalize(
                ingredient.name), self.normalize_ingredients(ingredient.ingredients)))
        return normalized
