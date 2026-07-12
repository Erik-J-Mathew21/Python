class Bird:
    def __init__(self):
        print("Bird is ready.")
    def whoisThis(self):
        print("This is Bird.")
    def swim(self):
        print("Swim faster.")
class Penguin(Bird):
    def __init__(self):
        super().__init__()
        print("Penguin is ready.")
    def whoisThis(self):
        print("This is Penguin.")
    def run(self):
        print("Run faster.")
Peggy = Penguin()
Peggy.whoisThis()
Peggy.swim()
Peggy.run()