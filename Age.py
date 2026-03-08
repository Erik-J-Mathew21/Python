age = int(input("Enter your age: "))
if age <= 0 or age > 120:
    print("Error: Invalid age entered.")
else:
    print("Age entered is valid.")
    if age % 2 == 0:
        print("Age is even.")
    else:
        print("Age is odd.")
bm = str(input("Enter your birthday month: "))
if bm == "April":
    print("You are born in the best month.")
else:
    print("You are born in", bm)