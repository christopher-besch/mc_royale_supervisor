from mc_royale import start_game
import _thread

# initiating game start
_thread.start_new_thread(start_game, ("Stromel1x", [0, 0], 100))

while True:
    pass

# start_game("Stromel1x", [0, 0], 100)
