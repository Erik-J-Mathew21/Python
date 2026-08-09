class RomanConverter:
    def to_roman(self, number):
        values = [1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1]
        symbols = ["M", "CM", "D", "CD", "C", "XC", "L", "XL", "X", "IX", "V", "IV", "I"]
        result = ""
        i = 0
        while number > 0:
            while number >= values[i]:
                result += symbols[i]
                number -= values[i]
            i += 1
        return result
num = int(input("Enter an integer: "))
converter = RomanConverter()
print("Roman value:", converter.to_roman(num))