class Cape_Verde():
    def capital(self):
        print("Praia is the capital of Cape Verde.")
    def language(self):
        print("Cape Verdean Creole is the most widely spoken language of Cape Verde.")
    def type(self):
        print("Cape Verde is a developing country.")
class Sierra_Leone():
    def capital(self):
        print("Freetown is the capital of Sierra Leone.")
    def language(self):
        print("Sierra Leone Krio is the most widely spoken language of Sierra Leone.")
    def type(self):
        print("Sierra Leone is a developing country.")
obj_cap = Cape_Verde()
obj_sie = Sierra_Leone()
for country in (obj_cap, obj_sie):
    country.capital()
    country.language()
    country.type()