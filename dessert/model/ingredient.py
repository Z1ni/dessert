class Ingredient:

    def __init__(self, name, ingredients=[]):
        self.name = name
        self.ingredients = ingredients

    def __str__(self):
        if len(self.ingredients) == 0:
            return self.name
        return "%s (%s)" % (self.name, ", ".join([str(i) for i in self.ingredients]))

    def __repr__(self):
        if len(self.ingredients) > 0:
            return "<Ingredient \"%s\", contains [%s]>" % (self.name, ", ".join([repr(i) for i in self.ingredients]))
        else:
            return "<Ingredient \"%s\">" % self.name
