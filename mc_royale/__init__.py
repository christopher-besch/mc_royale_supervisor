import _thread
from time import sleep
from mcrcon import MCRcon
from random import randint
from config import Config
from mcuuid.api import GetPlayerData


# displaying a message on everyone's screen
# a message can also be send to only one player
def text(mcr, msg, col, recipient="@a", console=False):
    # if console is True, the text will be send to everyone's console instead
    if console:
        mcr.command('/tellraw {} {{"text":"{}","color":"{}"}}'.format(recipient, msg, col))
    else:
        mcr.command('/title {} title {{"text":"","extra":[{{"text":"{}","color":"{}"}}]}}'.format(recipient, msg, col))


# playing a sound for everyone or a single player if demanded
def play(mcr, sound, pitch, recipient="@a"):
    mcr.command("/playsound {} voice {} ~ ~ ~ 1000 {}".format(sound, recipient, pitch))


def get_player_names():
    # connect to RCON server
    with MCRcon(Config.MC_SERVER_IP, Config.MC_SERVER_PASSWORD) as mcr:
        # get list of every player on the server
        player_names = mcr.command("/list")
        player_names = player_names.split(": ")[1].split(", ")

        return player_names


# class for minecraft users
class Player:
    # terminated = lost
    terminated = False

    def __init__(self, match, name):
        # saving player name
        self.name = name
        # get uuid
        player = GetPlayerData(self.name)
        if player.valid:
            self.uuid = player.uuid
        else:
            self.uuid = None
        # copying stats from match object into dictionary
        self.stats = {}
        for stat in match.stats:
            self.stats[stat] = None


# class for minecraft effects
class Effect:
    def __init__(self, name, duration, strength):
        self.name = name
        self.duration = duration
        self.strength = strength


# class for saving the changes necessary for a particular stage change
class Stage:
    def __init__(self, index, time_until_shrink, delta_time, after_time,
                 effects=None, border_diameter=None, weather=None, time=None):
        # index of the stage
        self.index = index

        # list of every effect that has to be applied at the start of the stage
        if effects is None:
            effects = []
        self.effects = effects

        # environment variables
        self.weather = weather
        self.time = time

        # final border diameter
        self.border_diameter = border_diameter
        # time until the border starts shrinking
        self.time_until_shrink = time_until_shrink
        # time the border is allowed to use for shrinking
        self.delta_time = delta_time
        # time between shrinking ending and start of next stage
        self.after_time = after_time

    # executing orders
    def execute(self, match, mcr):
        # elevating stage
        match.current_stage = self.index
        # updating the stage objective
        mcr.command("/scoreboard players set @a stage {}".format(self.index))
        # sending warning
        text(mcr, "STAGE ELEVATED", "red")
        # playing sound
        play(mcr, "minecraft:entity.elder_guardian.curse", 0.1)

        # change weather and time of day if necessary
        if self.weather is not None:
            mcr.command("/weather {}".format(self.weather))
        if self.time is not None:
            mcr.command("/time set {}".format(self.time))

        # when effects have to be applied
        for effect in self.effects:
            # applying every requested effect to every player (except for the supervisor)
            for player in match.players:
                # every terminated player will be ignored
                if not player.terminated:
                    cmd = "/effect give {} {} {} {}".format(player.name, effect.name, effect.duration, effect.strength)
                    mcr.command(cmd)

        # when the border is supposed to shrink, a warning will be send and a new center will be calculated
        if self.border_diameter is not None:
            # calculating where the new center can be; it must be inside the ld border
            # old_center[0] - (old_border_diameter / 2) gives the x coordinate of one side of the current border
            # + (border_diameter / 2) going the radius of the new border back into the old border
            x_range_1st = match.current_center[0] - (match.current_border_diameter / 2) + (self.border_diameter / 2)
            x_range_2nd = match.current_center[0] + (match.current_border_diameter / 2) - (self.border_diameter / 2)
            x_range = [x_range_1st, x_range_2nd]

            z_range_1st = match.current_center[1] - (match.current_border_diameter / 2) + (self.border_diameter / 2)
            z_range_2nd = match.current_center[1] + (match.current_border_diameter / 2) - (self.border_diameter / 2)
            z_range = [z_range_1st, z_range_2nd]

            # picking a location
            center = [randint(x_range[0], x_range[1]), randint(z_range[0], z_range[1])]
            # set world spawn into the new middle -> new location for compass
            mcr.command("/setworldspawn {} ~ {}".format(center[0], center[1]))

            small_x = center[0] - (self.border_diameter / 2)
            big_x = center[0] + (self.border_diameter / 2)
            small_z = center[1] - (self.border_diameter / 2)
            big_z = center[1] + (self.border_diameter / 2)

            msgs = [["WARNING: the border is about to shrink in {} seconds!".format(self.time_until_shrink), "red"],
                    ["Center: {} {}".format(center[0], center[1]), "green"],
                    ["Corners:", "blue"],
                    ["{} {}     {} {} ↑N".format(small_x, small_z, small_x, big_z), "blue"],
                    ["{} {}     {} {}".format(big_x, small_z, big_x, big_z), "blue"]]

            for msg in msgs:
                text(mcr, msg[0], msg[1], console=True)

            # waiting until border shrink
            match.sleep(self.time_until_shrink)

            # send warning
            text(mcr, "WARNING: the border is shrinking!", "red", console=True)
            # shrinking the world border
            match.move_border(center, self.border_diameter, self.delta_time)

            # update current center and diameter values
            match.current_center = center
            match.current_border_diameter = self.border_diameter

            # wait the after time
            match.sleep(self.after_time)

        # when the border does not have to to move
        else:
            # the center and border diameter stays where it is if the border does not move
            match.sleep(self.time_until_shrink)
            match.sleep(self.delta_time)
            match.sleep(self.after_time)


# class for a whole match
class Match:
    # False when every thread used by this match should be terminated
    running = False
    # list with every player
    players = []
    # the current stage; it gets elevated after every stage change
    current_stage = 0
    # interval in seconds between death scans
    death_count_check_time = 2
    # interval in seconds between border nudges
    border_step_size = 2
    # minecraft stats that have to be tracked
    stats = ["deathCount",
             "totalKillCount",
             "playerKillCount",
             "level",
             "xp",
             "armor"]
    # name of the current supervisor
    supervisor_name = ""
    # current center of the play area
    current_center = []

    def __init__(self, diameter, stages, tp_height=120, max_deaths=3):
        # current diameter of the play area
        self.current_border_diameter = diameter
        # list with every stage that has to be executed
        self.stages = stages
        # height to teleport players to
        self.tp_height = tp_height
        # maximum of allowed death after which the player loses
        self.max_deaths = max_deaths

    def game_setup(self, supervisor_name):
        # update variables
        self.supervisor_name = supervisor_name

        # connect to RCON server
        with MCRcon(Config.MC_SERVER_IP, Config.MC_SERVER_PASSWORD) as mcr:

            # get list of every player on the server
            player_names = mcr.command("/list")
            player_names = player_names.split(": ")[1].split(", ")

            # removing the supervisor from the player list
            if self.supervisor_name in player_names:
                del player_names[player_names.index(self.supervisor_name)]

            # list with every player
            self.players = []
            # creating player objects
            for player_name in player_names:
                self.players.append(Player(self, player_name))

    def start_game(self, location):
        # update variables
        self.current_center = location
        # allow new threads
        self.running = True

        # connect to RCON server
        with MCRcon(Config.MC_SERVER_IP, Config.MC_SERVER_PASSWORD) as mcr:
            # get list of every objective
            rsp = mcr.command("/scoreboard objectives list")
            # when there are already objectives, they will be removed
            if "no objectives" not in rsp:
                objectives = rsp.split(": ")[1].replace("[", "").replace("]", "").split(", ")
                # removing every objective
                for objective in objectives:
                    mcr.command("/scoreboard objectives remove {}".format(objective))

            # setting the randomTickSpeed to a higher value
            mcr.command("/gamerule randomTickSpeed 6")
            # always keeping the current weather and time of day
            mcr.command("/gamerule doDaylightCycle false")
            mcr.command("/gamerule doWeatherCycle false")
            # making day
            mcr.command("/time set day")
            # clearing the weather
            mcr.command("/weather clear")
            # everyone in adventure mode
            mcr.command("/gamemode adventure @a")
            # set world spawn to the middle of the map
            mcr.command("/setworldspawn {} ~ {}".format(self.current_center[0], self.current_center[1]))
            # remove every advancement
            mcr.command("/advancement revoke @a everything")
            # deactivate keepInventory
            mcr.command("/gamerule keepInventory false")
            # kill everyone
            mcr.command("/kill @a")
            sleep(0.2)
            # kill every drop
            mcr.command("/kill @e[type=minecraft:item]")
            # reactivate keepInventory
            mcr.command("/gamerule keepInventory true")

            # wait 5 sec.
            self.sleep(5)

            # freeze everyone
            mcr.command("/effect give @a minecraft:jump_boost 10000 137")
            mcr.command("/effect give @a minecraft:slowness 10000 255")
            mcr.command("/effect give @a minecraft:absorption 10000 255")
            # give everyone a compass to find the middle of the map
            mcr.command("/give @a minecraft:compass")

            # calculation coordinates of borders
            x_range_1st = self.current_center[0] - (self.current_border_diameter / 2)
            x_range_2nd = self.current_center[0] + (self.current_border_diameter / 2)
            x_range = [x_range_1st, x_range_2nd]
            z_range_1st = self.current_center[1] - (self.current_border_diameter / 2)
            z_range_2nd = self.current_center[1] + (self.current_border_diameter / 2)
            z_range = [z_range_1st, z_range_2nd]
            # teleport the supervisor
            mcr.command("/tp {} {} {} {}".format(self.supervisor_name, self.current_center[0],
                                                 self.tp_height, self.current_center[1]))
            # teleport everyone else in a random location inside the border
            for player in self.players:
                # selecting new location
                next_location = [randint(x_range[0], x_range[1]), randint(z_range[0], z_range[1])]
                # teleporting player
                mcr.command("/tp {} {} {} {}".format(player.name, next_location[0], self.tp_height, next_location[1]))

            # set world border
            mcr.command("/worldborder center {} {}".format(self.current_center[0], self.current_center[1]))
            mcr.command("/worldborder set {}".format(self.current_border_diameter))

            # create objectives to track player stats
            for stat in self.stats:
                mcr.command("/scoreboard objectives add {} {}".format(stat, stat))
                mcr.command("/scoreboard objectives modify {} rendertype integer".format(stat))
            # show player deaths in TAB display
            mcr.command("/scoreboard objectives setdisplay list deathCount")
            # creating objective to show the current stage
            mcr.command("/scoreboard objectives add stage dummy")
            # show the current stage in the sidebar
            mcr.command("/scoreboard objectives setdisplay sidebar stage")
            # updating the stage objective
            mcr.command("/scoreboard players set @a stage {}".format(self.current_stage))

            # wait 10 sec.
            self.sleep(10)

            # remove every effect
            mcr.command("/effect clear @a")
            # set everyone into survival mode
            mcr.command("/gamemode survival @a")
            # set supervisor into spectator mode
            mcr.command("/gamemode spectator {}".format(self.supervisor_name))

            # creating second thread
            _thread.start_new_thread(self.kill_control, ())

            # executing every stage
            for stage in self.stages:
                # when the game is over, the script ends
                if not self.running:
                    return
                # execute stage
                stage.execute(self, mcr)

    # modified sleep function with integrated interrupt
    def sleep(self, delta_time):
        # check every second if the round is already over
        for i in range(0, delta_time):
            if not self.running:
                _thread.exit()
                break
            sleep(1)

    # get the amount of unterminated players
    def get_player_count(self):
        player_count = 0
        for player in self.players:
            if not player.terminated:
                player_count += 1
        return player_count

    # setting players with to many deaths into spectator mode and taking care of victory
    def kill_control(self):
        # connecting to the server
        with MCRcon(Config.MC_SERVER_IP, Config.MC_SERVER_PASSWORD) as mcr:
            # running for as long as allowed
            while self.running:

                # when there is only one or fewer player left
                if self.get_player_count() <= 1:
                    # seeking alive player
                    for player in self.players:
                        # ignoring every terminated player
                        if player.terminated:
                            continue
                        # displaying win
                        # first not yet terminated player wins
                        text(mcr, "{} WINS".format(player.name), "yellow")
                        play(mcr, "minecraft:entity.ender_dragon.death", 1)
                        # ending round
                        self.running = False
                        # kill thread
                        _thread.exit()
                        return

                    # if nobody is still alive
                    # displaying draw
                    text(mcr, "DRAW", "yellow")
                    play(mcr, "minecraft:entity.ender_dragon.death", 1)
                    # ending round
                    self.running = False
                    # kill thread
                    _thread.exit()
                    return

                # updating every players death counter when the round is not yet over
                for player in self.players:
                    # every player that died too often will not be tracked
                    if player.terminated:
                        continue

                    # requesting information
                    resp = mcr.command("/scoreboard players get {} deathCount".format(player.name))
                    # extracting current value
                    if "[deathCount]" in resp:
                        player.stats["deathCount"] = int(resp.split(" has ")[1].split(" [")[0])
                    else:
                        # when deathCount is unknown it is 0
                        player.stats["deathCount"] = 0

                    # every player that has reached the max allowed death count loses
                    if player.stats["deathCount"] >= self.max_deaths:
                        # setting player into spectator mode
                        mcr.command("/gamemode spectator {}".format(player.name))
                        # terminating player
                        player.terminated = True
                        # showing lost to other players
                        text(mcr, "{} LOST".format(player.name), "blue")
                        play(mcr, "minecraft:entity.wither.spawn", 2)

                # waiting until next check
                sleep(self.death_count_check_time)

    # move border to designated target
    def move_border(self, center, border_diameter, delta_time):
        # connect to server
        with MCRcon(Config.MC_SERVER_IP, Config.MC_SERVER_PASSWORD) as mcr:
            # one step per second (starting by 1; ending by delta_time)
            for n in range(1, delta_time + 1):
                # end shrink when someone won
                if not self.running:
                    break

                # calculating new diameter with a linear equation
                # y=m*x+n
                # m=gradient=(delta y)/(delta x)=(border_diameter - old_border_diameter) / delta_time
                # x=current step=n
                # n=offset=old_border_diameter
                temp_diameter = \
                    ((border_diameter - self.current_border_diameter) / delta_time) * n + self.current_border_diameter

                # calculation a new temporary center, similar t temp_diameter
                temp_x = ((center[0] - self.current_center[0]) / delta_time) * n + self.current_center[0]
                temp_z = ((center[1] - self.current_center[1]) / delta_time) * n + self.current_center[1]

                # apply new values
                mcr.command("/worldborder center {} {}".format(temp_x, temp_z))
                mcr.command("/worldborder set {} {}".format(str(temp_diameter), str(int(self.border_step_size))))

                # wait for one step; default is 1sec.
                sleep(int(self.border_step_size))
