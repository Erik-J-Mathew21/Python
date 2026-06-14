class Willy_Wagtail:
    species = "Invertabrate"
    def __init__(self, name, age):
        self.name = name
        self.age = age
Willy = Willy_Wagtail("Willy", 12)
Wagtail = Willy_Wagtail("Wagtail", 13)
print("Willy is an {}.".format(Willy.species))
print("Wagtail is also a {}.".format(Wagtail.species))
print("{} is {} years old.".format(Willy.name, Willy.age))
print("{} is {} years old.".format(Wagtail.name, Wagtail.age))