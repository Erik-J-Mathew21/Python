bill_amount = float(input("Enter the total bill amount: "))
amount_paid = float(input("Enter the amount paid: "))
sub = amount_paid - bill_amount
if sub > 0:
    print("Change to return to customer:", sub)
elif sub < 0:
    print("Amount due from customer:", abs(sub))
else:
    print("Payment complete. No due or change.")