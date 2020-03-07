import _thread
from time import sleep

n = 0


def test():
    global n
    while True:
        n += 1
        if n >= 20000000000000:
            _thread.exit()


_thread.start_new_thread(test, ())

while True:
    print(n)
