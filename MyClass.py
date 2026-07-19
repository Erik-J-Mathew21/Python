class myClass:
    __privateVar = 27;
    def __privMeth(self):
        print("I'm inside class myClass.")
        # Wow! I didn't now you were in class myClass!
        # Sarcasm involved
    def hello(self):
        print("Private Variable value: ", myClass.__privateVar)
foo = myClass()
foo.hello()
foo.__privMeth