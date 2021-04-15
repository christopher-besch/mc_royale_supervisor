import mc_royale

stages = [mc_royale.Stage(1, 0, 0, 20,
                          effects=[mc_royale.Effect("minecraft:invisibility", 20, 1)]),
          mc_royale.Stage(2, 0, 10, 60,
                          border_diameter=10, weather="thunder", time="night")]

# start game
mc_royale.Match("IDIOT", [0, 0], 100, stages)
