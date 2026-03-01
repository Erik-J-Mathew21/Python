def shutdown():
    password = input("Enter password to shutdwn: ")
    if password == "Erik123":
        print("Shutting down...")
        exit()
    else:
        print("Incorrect password. Shutdown aborted.")
shutdown()