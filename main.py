#!/usr/bin/python3

import _thread
from time import sleep
from mcrcon import MCRcon
from random import randint


# displaying a message on everyone's screen
# if console is True, the text will be send to everyone's console instead
# a message can also be send to only one player
def text(mcr, msg, col, recipient="@a", console=False):
    if console:
        mcr.command('/tellraw {} title {{"text":"","extra":[{{"text":"{}","color":"{}"}}]}}'.format(recipient, msg, col))
    else:
        mcr.command('/title {} title {{"text":"","extra":[{{"text":"{}","color":"{}"}}]}}'.format(recipient, msg, col))


# playing a sound for everyone
def play(mcr, sound, pitch):
    mcr.command("/playsound {} voice @a ~ ~ ~ 1000 {}".format(sound, pitch))


# setting players with to many deaths into spectator mode and taking care of victory
def kill_control():
    global stats_control_ok, death_count_check_time, max_deaths, server_ip, server_password, player_count
    # connecting to the server
    with MCRcon(server_ip, server_password) as mcr:
        # running for as long as allowed
        while stats_control_ok:

            # when there is only one or fewer player left
            if player_count <= 1:
                # seeking alive player
                for player in players:
                    # ignoring every terminated player
                    if player.terminated:
                        continue
                    # displaying win
                    # first not yet terminated player wins
                    text(mcr, "{} WINS".format(player.name), "yellow")
                    play(mcr, "minecraft:entity.ender_dragon.death", 1)
                    # ending round
                    stats_control_ok = False
                    return
                # if nobody is still alive
                # displaying draw
                text(mcr, "DRAW", "yellow")
                play(mcr, "minecraft:entity.ender_dragon.death", 1)
                # ending round
                stats_control_ok = False
                return

            # updating every players death counter
            for player in players:
                # every player that died too often will not be tracked
                if player.terminated:
                    continue

                # requesting information
                resp = mcr.command("/scoreboard players get {} deathCount".format(player.name))
                # extracting current value
                if "none is set" in resp:
                    player.stats["deathCount"] = 0
                else:
                    # when deathCount is unknown it is 0
                    player.stats["deathCount"] = int(resp.split(" has ")[1].split(" [")[0])

                # every player that has reached the max allowed death count loses
                if player.stats["deathCount"] >= max_deaths:
                    # setting player into spectator mode
                    mcr.command("/gamemode spectator {}".format(player.name))
                    # terminating player
                    player.terminated = True
                    # showing lost to other players
                    text(mcr, "{} LOST".format(player.name), "blue")
                    play(mcr, "minecraft:entity.wither.spawn", 2)
                    # removing one from the player count
                    player_count -= 1

            # waiting until next check
            sleep(death_count_check_time)


# move border to designated target
def move_border(old_center, old_border_diameter, center, border_diameter, delta_time, steps=1):
    global server_ip, server_password
    # connect to server
    with MCRcon(server_ip, server_password) as mcr:
        # one step per second (starting by 1; ending by delta_time)
        for n in range(1, delta_time + 1):
            # calculating new diameter with a linear equation
            # y=m*x+n
            # m=gradient=(delta y)/(delta x)=(border_diameter - old_border_diameter) / delta_time
            # x=current step=n
            # n=offset=old_border_diameter
            temp_diameter = ((border_diameter - old_border_diameter) / delta_time) * n + old_border_diameter

            # calculation a new temporary center, similar t temp_diameter
            temp_x = ((center[0] - old_center[0]) / delta_time) * n + old_center[0]
            temp_z = ((center[1] - old_center[1]) / delta_time) * n + old_center[1]

            # apply new values
            mcr.command("/worldborder center {} {}".format(temp_x, temp_z))
            mcr.command("/worldborder set {} {}".format(str(temp_diameter), str(int(steps))))

            # wait for one step; default is 1sec.
            sleep(int(steps))


# starting the game
def start_game(supervisor_name, location, diameter, tp_height=120):
    global server_ip, server_password, current_stage, stats_control_ok, stats, players, player_count
    # connect to RCON server
    with MCRcon(server_ip, server_password) as mcr:
        current_stage = 0

        # get list of every player on the server
        player_names = mcr.command("/list")
        player_names = player_names.split(": ")[1].split(", ")

        # removing the supervisor from the player list
        if supervisor_name in player_names:
            del player_names[player_names.index(supervisor_name)]

        # creating player objects
        for player_name in player_names:
            players.append(Player(player_name))
        # updating player counter
        player_count = len(players)

        # get list of every objective
        rsp = mcr.command("/scoreboard objectives list")
        # when there are already objectives, they will be removed
        if "no objectives" not in rsp:
            objectives = rsp.split(": ")[1].replace("[", "").replace("]", "").split(", ")
            # removing every objective
            for objective in objectives:
                mcr.command("/scoreboard objectives remove {}".format(objective))

        # making day
        mcr.command("/time set day")
        # clearing the weather
        mcr.command("/weather clear")
        # everyone in adventure mode
        mcr.command("/gamemode adventure @a")
        # set world spawn to the middle of the map
        mcr.command("/setworldspawn {} {} {}".format(location[0], tp_height, location[1]))
        # kill everyone
        mcr.command("/kill @a")

        # wait 5 sec.
        sleep(5)

        # freeze everyone
        mcr.command("/effect give @a minecraft:jump_boost 10000 137")
        mcr.command("/effect give @a minecraft:slowness 10000 255")
        mcr.command("/effect give @a minecraft:absorption 10000 255")

        # calculation coordinates of borders
        x_range_1st = location[0] - (diameter / 2)
        x_range_2nd = location[0] + (diameter / 2)
        x_range = [x_range_1st, x_range_2nd]
        z_range_1st = location[1] - (diameter / 2)
        z_range_2nd = location[1] + (diameter / 2)
        z_range = [z_range_1st, z_range_2nd]
        # teleport the supervisor
        mcr.command("/tp {} {} {} {}".format(supervisor_name, location[0], tp_height, location[1]))
        # teleport everyone else in a random location inside the border
        for player in players:
            # selecting new location
            next_location = [randint(x_range[0], x_range[1]), randint(z_range[0], z_range[1])]
            # teleporting player
            mcr.command("/tp {} {} {} {}".format(player.name, next_location[0], tp_height, next_location[1]))

        # set world border
        mcr.command("/worldborder center {} {}".format(location[0], location[1]))
        mcr.command("/worldborder set {}".format(diameter))

        # create objectives to track player stats
        for stat in stats:
            mcr.command("/scoreboard objectives add {} {}".format(stat, stat))
            mcr.command("/scoreboard objectives modify {} rendertype integer".format(stat))
        # show player deaths in TAB display
        mcr.command("/scoreboard objectives setdisplay list deathCount")
        # creating objective to show the current stage
        mcr.command("/scoreboard objectives add stage dummy")
        # show the current stage in the sidebar
        mcr.command("/scoreboard objectives setdisplay sidebar stage")
        # updating the stage objective
        mcr.command("/scoreboard players set @a stage {}".format(current_stage))

        # add countdown!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

        # wait 10 sec.
        sleep(10)

        # remove every effect
        mcr.command("/effect clear @a")
        # set everyone into survival mode
        mcr.command("/gamemode survival @a")
        # set supervisor into spectator mode
        mcr.command("/gamemode spectator {}".format(supervisor_name))

        # activating death monitoring
        stats_control_ok = True
        # creating second thread
        _thread.start_new_thread(kill_control, ())

        # executing every stage
        # initial border parameters
        old_center = location
        old_border_diameter = diameter
        for stage in stages:
            # the next stage needs the newly created border parameters as old values
            old_center, old_border_diameter = stage.execute(mcr, old_center, old_border_diameter)


class Player:
    stats = {}
    # terminated = lost
    terminated = False

    def __init__(self, name):
        global stats
        # saving player name
        self.name = name
        # copying stats from global into dictionary
        for stat in stats:
            self.stats[stat] = None


# class for minecraft effects
class Effect:
    name = None
    duration = None
    strength = None

    def __init__(self, name, duration, strength):
        self.name = name
        self.duration = duration
        self.strength = strength


# class for saving the changes necessary for a particular stage change
class Stage:
    # index of the stage
    index = None

    # list of every effect that has to be applied at the start of the stage
    effects = []

    # border settings
    border_diameter = None

    # time until the border starts shrinking
    time_until_shrink = None
    # time the border is allowed to use for shrinking
    delta_time = None
    # time between shrinking ending and start of next stage
    after_time = None

    def __init__(self, index, effects, border_diameter, time_until_shrink, delta_time, after_time):
        self.index = index

        self.effects = effects

        self.border_diameter = border_diameter

        self.time_until_shrink = time_until_shrink
        self.delta_time = delta_time
        self.after_time = after_time

    # executing orders
    def execute(self, mcr, old_center, old_border_diameter):
        global players, current_stage
        # elevating stage
        current_stage = self.index
        # updating the stage objective
        mcr.command("/scoreboard players set @a stage {}".format(self.index))
        # sending warning
        text(mcr, "STAGE ELEVATED TO {}".format(self.index), "red")
        # playing sound
        play(mcr, "minecraft:entity.elder_guardian.curse", 0.1)

        # applying every requested effect to every player (except for the supervisor)
        for player in players:
            # every terminated player will be ignored
            if player.terminated:
                continue
            for effect in self.effects:
                mcr.command("/effect give {} {} {}".format(player.name, effect.name, effect.duration))

        # move border to random new location inside old border
        # calculating where the new center can be
        # old_center[0] - (old_border_diameter / 2) gives the x coordinate of one side of the current border
        # + (border_diameter / 2) going the radius of the new border back into the old border
        x_range_1st = old_center[0] - (old_border_diameter / 2) + (self.border_diameter / 2)
        x_range_2nd = old_center[0] + (old_border_diameter / 2) - (self.border_diameter / 2)
        x_range = [x_range_1st, x_range_2nd]

        z_range_1st = old_center[1] - (old_border_diameter / 2) + (self.border_diameter / 2)
        z_range_2nd = old_center[1] + (old_border_diameter / 2) - (self.border_diameter / 2)
        z_range = [z_range_1st, z_range_2nd]

        # picking a location
        center = [randint(x_range[0], x_range[1]), randint(z_range[0], z_range[1])]

        # shrinking the world border
        _thread.start_new_thread(move_border, (old_center, old_border_diameter, center, self.border_diameter, self.delta_time))

        # waiting until next stage
        sleep(self.after_time)
        # returning current state of the border
        return center, self.border_diameter


# minecraft rcon server details
server_ip = "YOUR_SERVER_IP"
server_password = "YOUR_RCON_PASSWORD"
# stats to track
stats = ["deathCount",
         "totalKillCount",
         "playerKillCount",
         "level",
         "xp",
         "armor"]
# list with every player as a Player instance
players = []
# amount of players
player_count = None
# current stage
current_stage = None
# list with every stage
stages = [Stage(1,
                [Effect("minecraft:invisibility", 10, 1),
                 Effect("minecraft:speed", 10, 1)],
                100, 0, 20, 25),
          Stage(2,
                [Effect("minecraft:invisibility", 10, 1),
                 Effect("minecraft:speed", 10, 255)],
                50, 0, 20, 25),
          Stage(3,
                [Effect("minecraft:invisibility", 10, 1),
                 Effect("minecraft:speed", 10, 255)],
                10, 0, 20, 25)]

# supervisor coins
coins = 0
# False to stop stats control
stats_control_ok = False
# amount of deaths after which the player will be set into spectator mode
max_deaths = 2
# time between every death count check in sec.
death_count_check_time = 1


# initiating game start
start_game("Stromel1x", [0, 0], 200)

while stats_control_ok:
    pass
