def log(text):
    f = open("error.out", "a")
    f.write(text + '\n')
    f.close()
