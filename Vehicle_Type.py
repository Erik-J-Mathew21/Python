class Vehicle:
    def __init__(self, brand, max_speed):
        self.brand = brand
        self.max_speed = max_speed

    def show_details(self):
        print("Brand:", self.brand)
        print("Max Speed:", self.max_speed, "km/h")


class Car(Vehicle):

    def __init__(self, model, seats, brand, max_speed):
        self.model = model
        self.seats = seats
        super().__init__(brand, max_speed)

    def show_details(self):
        print("Model:", self.model)
        print("Seats:", self.seats)
        super().show_details()

    def fuel_type(self, fuel):
        print(self.model, "uses", fuel)


my_car = Car("City Rider", 5, "Honda", 180)

my_car.show_details()
my_car.fuel_type("petrol")

print("Is Car a subclass of Vehicle?", issubclass(Car, Vehicle))