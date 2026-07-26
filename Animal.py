from abc import ABC, abstractmethod
class Water_Animal(ABC):
    def move(self):
        pass
class Vaquita(Water_Animal):
    def move(self):
        print("I can swim 2nd slowest.")
class Porpoise(Water_Animal):
    def move(self):
        print("I can swim 2nd fastest.")
class Seahorse(Water_Animal):
    def move(self):
        print("I can swim slowest.")
class Marlin(Water_Animal):
    def move(self):
        print("I can swim fastest.")
X = Vaquita()
X.move()
Y = Porpoise()
Y.move()
X = Seahorse()
X.move()
Y = Marlin()
Y.move()