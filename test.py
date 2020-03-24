### Import our module
from mcuuid.api import GetPlayerData
from mcuuid.tools import is_valid_minecraft_username
from mcuuid.tools import is_valid_mojang_uuid

### Import some other necessary modules
import sys

### Which input method should we use?
# Are there some arguments brought by the console use the first after the filename as identifier
timestamp = None
if len(sys.argv) > 1:
    identifier = sys.argv[1]

    if len(sys.argv) > 2:
        if sys.argv[2].isdigit():
            timestamp = int(sys.argv[2])


# Else, ask for a identifier by userinput
else:
    print("Please enter a username or UUID: ")
    identifier = input()

### Is the identifier a valid value?
if is_valid_minecraft_username(identifier) or is_valid_mojang_uuid(identifier):
    # Print the type of the identifier
    if is_valid_minecraft_username(identifier):
        print('Valid username')
    if is_valid_mojang_uuid(identifier):
        print('Valid UUID')

    ### Obtaining the playerinformation using our module
    player = GetPlayerData(identifier, timestamp)
    # Check if the request was valid and the user exists
    if player.valid is True:
        # Getting UUID
        uuid = player.uuid
        # Getting real Username
        name = player.username

        # Print everything
        print('UUID: ' + uuid)
        print('correct name: ' + name)


    # Error message
    else:
        print("That player was not found.")

else:
    print('identifier is not valid')