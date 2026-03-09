size = 20
for i in range(1, size + 1):
    spaces = " " * (size - i)
    stars = "*" * (2 * i - 1)
    print(spaces + stars)