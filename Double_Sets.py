set1 = {1, 2, 3, 4}
set2 = {3, 4, 5, 6}
result = set1.symmetric_difference(set2)
print("Symmetric Difference (method 1):", result)
result2 = set1 ^ set2
print("Symmetric Difference (method 2):", result2)