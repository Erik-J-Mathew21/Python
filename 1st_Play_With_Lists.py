L = [4,5,1,2,9,7,10,8]
print("Original List :", L)
count = 0
for i in L:
    count += i
avg = count/len(L)
print("The sum is", count)
print("The average is", avg)
L.sort()