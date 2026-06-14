import random
import string
small_letters = string.ascii_lowercase
big_letters   = string.ascii_uppercase
numbers       = string.digits          
def make_password(length=12):
    password = [
        random.choice(small_letters),
        random.choice(big_letters),
        random.choice(numbers),
    ]
    all_chars = small_letters + big_letters + numbers
    for _ in range(length - 3):
        password.append(random.choice(all_chars))
    random.shuffle(password)
    return "".join(password)
print("Welcome to the Password Maker!")
length = int(input("How many characters do you want? (pick a number, like 8 or 12): "))
if length < 3:
    print("That's too short! Try a number bigger than 3.")
else:
    my_password = make_password(length)
    print("Here is your brand new password:")
    print(my_password)
    print("Save it somewhere safe!")