class DailyMessage:

    def __init__(self):
        self.message = ""

    def get_message(self):
        self.message = input("Enter today's message: ")

    def print_message(self):
        print("Message in uppercase:", self.message.upper())


daily_text = DailyMessage()
daily_text.get_message()
daily_text.print_message()


class HelperSession:

    def __init__(self):
        print("Daily Data Helper session created")

    def __del__(self):
        print("Daily Data Helper session ended")


def create_session():
    print("Making helper session...")
    session = HelperSession()
    print("Session is ready...")
    return session


print("")
print("Calling create_session() function...")
session_obj = create_session()
print("Program is still running...")


class PairFinder:

    def find_pair(self, numbers, target):
        lookup = {}

        for index, number in enumerate(numbers):
            needed_number = target - number

            if needed_number in lookup:
                return (lookup[needed_number], index)

            lookup[number] = index

        return None


numbers = (10, 20, 30, 40, 50, 60, 70)

target_value = int(input("Enter target sum to search: "))

result = PairFinder().find_pair(numbers, target_value)

if result is not None:
    print("Index1=%d, Index2=%d" % result)
else:
    print("No matching pair found.")

del session_obj
print("Program End")