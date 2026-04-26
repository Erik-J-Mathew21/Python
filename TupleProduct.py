def tuple_product(t):
    product = 1
    for num in t:
        product *= num
    return product
t = (1, 2, 3, 4, 5, )
print("Product of tuple elements:", tuple_product(t))