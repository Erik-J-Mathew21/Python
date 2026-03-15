import random
playing = True
num = str(random.randint(0,10))
print("I will generate a number from 0 to 10, and you have to guess the number one digit at a time.")
while playing:
    guess = input("Give me your best guess! \n")
    if num == guess:
        print("You win the game! The number was", num)
        break
    else:
        print("Your guess was incorrect. Please try again.")