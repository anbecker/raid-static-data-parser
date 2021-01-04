import parser
import json
import numpy as np
import pandas as pd
import re

STAT_GAIN_PER_LEVEL_BY_RANK = [
    -1,
    -1,  # I don't have estimates for champs other than rank 6 ones.
    -1,  # I'm certain that the rates differ, though.
    -1,
    -1,
    1.00903337867813  # Estimated. Would love to have closed form of this.
]

HP_DIVISOR = 26002616.5  # Estimated but close. In-game displayed values round to nearest 15.
ATK_DEF_DIVISOR = 390039247.5  # Estimated but close. In-game displayed values round to nearest 1.

DIFFICULTY_CODES = {
    "1": "Normal",
    "2": "Hard",
    "3": "Brutal",
    "4": "Nightmare"
}

ARTIFACT_SET_BASE_PRICES = [
    6000,  # Life
    6000,  # Offense
    7200,  # Defense
    9000,  # Speed
    7200,  # Critical Rate
    18000,  # Crit Damage
    7200,  # Accuracy
    9000,  # Resistance
    9000,  # Lifesteal
    11400,  # Fury
    18000,  # Daze
    18000,  # Cursed
    18000,  # Frost
    18000,  # Frenzy
    18000,  # Regeneration
    18000,  # Immunity
    18000,  # Shield
    18000,  # Relentless
    18000,  # Savage
    11400,  # Destroy
    18000,  # Stun
    18000,  # Toxic
    18000,  # Taunting
    11400,  # Retaliation
    18000,  # Avenging
    18000,  # Stalwart
    18000,  # Reflex
    14400,  # Curing
    18000,  # Cruel
    18000,  # Immortal
    18000,  # Divine Offense
    18000,  # Divine Critical Rate
    18000,  # Divine Life
    18000,  # Divine Speed
    18000,  # Swift Parry
    18000,  # Deflection
    18000,  # Resilience
    18000,  # Perception
    18000,  # Fatal
    18000,  # Untouchable
    18000,  # Affinitybreaker
    18000   # Frostbite
]

ITEM_TYPE_VALUE_MULTIPLIERS = [
    0.75,
    0.8,
    0.85,
    0.9,
    0.95,
    1,
    1.1,
    1.2,
    1.4
]

ITEM_RARITY_VALUE_MULTIPLIERS = [
    1,
    1.25,
    1.5,
    2,
    3
]

ITEM_RANK_VALUE_MULTIPLIERS = [
    1,
    2,
    5,
    10,
    25,
    40
]

ITEM_RANK_SELL_VALUE_MULTIPLIERS = [
    0.1111111,
    0.1,
    0.07692307692,
    0.0625,
    0.05555555556,
    0.05
]

FACTIONS = [
    'N/A',
    'Bannerlords',
    'High Elves',
    'Sacred Order',
    'N/A',
    'Ogryn Tribes',
    'Lizardmen',
    'Skinwalkers',
    'Orcs',
    'Demonspawn',
    'Undead Hordes',
    'Dark Elves',
    'Knights Revenant',
    'Barbarians',
    'N/A',
    'N/A',
    'Dwarves',
]

AFFINITIES = [
    '',
    'Magic',
    'Force',
    'Spirit',
    'Void',
]

CHAMP_TYPES = [
    'Attack',
    'Defense',
    'HP',
    'Support',
]

CHAMP_RARITIES = [
    '',
    'Common',
    'Uncommon',
    'Rare',
    'Epic',
    'Legendary',
]

EFFECT_TARGET_TYPES = [
    'Single Target',
    'Self',
    'Target(s) of main effect',
    'Originator of relation',
    'Self',
    'Random ally (allies)',
    'Random enemy (enemies)',
    'All allies',
    'All enemies',
    'All dead allies',
    '10',
    '11',
    '12',
    'Random dead ally (allies)',
    '14',
    '15',
    '16',
    '17',
    '18',
    'Most damaged ally (by percent)',
    'Most damaged enemy (by percent)',
    '21',
    'Boss',
    '23',
    '24',
    'Random dead ally (allies)',
    '26',
    '27',
    '28',
    'All allies and enemies',
    'Ally that begins turn',
    '31',
    'Ally with lowest MAX HP',
    '33',
    'Enemy that killed this champion',
    'Champs with same champ ID as target',
    '36',
    '37',
    'Enemy with lowest turn meter',
    'Enemy with highest turn meter',
    '40'
]

STAT_TYPES = [
    "HP",
    "Attack",
    "Defense",
    "Speed",
    "Resist",
    "Accuracy",
    "Crit Rate",
    "Crit Damage"
]

AURA_AREAS = [
    "All Battles",
    "Campaign",
    "Dungeons",
    "Arena",
    "UNKNOWN",
    "Faction Crypts",
    "UNKNOWN",
    "Doom Tower"
]

STATUS_TYPES = {
    10: "Stun",
    20: "Freeze",
    30: "Sleep",
    40: "Provoke",
    50: "Counterattack",
    60: "Block Damage",
    70: "100% Heal Reduction",
    71: "50% Heal Reduction",
    80: "5% Poison",
    81: "2.5% Poison",
    90: "7.5% Continuous Heal",
    91: "15% Continuous Heal",
    100: "Block Debuffs",
    110: "Block Buffs",
    120: "25% Increase ATK",
    121: "50% Increase ATK",
    130: "25% Decrease ATK",
    131: "50% Decrease ATK",
    140: "30% Increase DEF",
    141: "60% Increase DEF",
    150: "30% Decrease DEF",
    151: "60% Decrease DEF",
    160: "15% Increase SPD",
    161: "30% Increase SPD",
    170: "15% Decrease SPD",
    171: "30% Decrease SPD",
    220: "25% Increase ACC",
    221: "50% Increase ACC",
    230: "25% Decrease ACC",
    231: "50% Decrease ACC",
    240: "15% Increase C. RATE",
    241: "30% Increase C. RATE",
    250: "15% Decrease C. RATE",
    251: "30% Decrease C. RATE",
    260: "15% Increase C. DMG",
    261: "30% Increase C. DMG",
    270: "15% Decrease C. DMG",
    271: "30% Decrease C. DMG",
    280: "Shield",
    290: "Block Cooldown Skills",
    300: "Revive on Death",
    310: "50% Ally Protection",
    311: "25% Ally Protection",
    320: "Unkillable",
    330: "Bomb",
    350: "25% Weaken",
    351: "15% Weaken",
    360: "Block Revive",
    410: "15% Reflect Damage",
    411: "30% Reflect Damage",
    440: "Hex",
    460: "Leech",
    470: "HP Burn",
    480: "Veil",
    481: "Perfect Veil",
    490: "Fear",
    491: "True Fear",
    500: "25% Poison Sensitivity",
    501: "50% Poison Sensitivity",
    510: "15% Strengthen",
    511: "25% Strengthen"
}

EFFECT_TYPES = {
    0: "Revive",
    # Ex. Raglin A3: "Revives an ally with 75% HP and a full Turn Meter." (Id: 16041)
    1000: "Heal",
    # Ex. Hexweaver A2: "Heals all allies by 15% of their MAX HP." (Id: 197021)
    4000: "Place buff",
    # Ex. Vulpine A2: "Places a 25% [Increase ATK] buff on all allies for 2 turns." (Id: 119021)
    4001: "Fill turn meter",
    # Ex. Raglin A3: "Revives an ally with 75% HP and a full Turn Meter." (Id: 16041)
    4002: "Transfer Debuff",
    # Ex. Fang Cleric A1: "Attacks 1 enemy. Has a 75% chance of transferring 1 random debuff from this Champion to the target." (Id: 455012)
    4003: "Remove Debuff",
    # Ex. Gator A3: "Removes all debuffs from all allies." (Id: 274031)
    4004: "Avtivate other skill",
    # Ex. Zargala A2: "Attacks 1 enemy. Instantly activates the Crack Armor Skill if the target is killed by this attack." (Id: 174022)
    4005: "Unlock secret skill",
    # Ex. Baron A3: "Attacks 1 enemy. Damage increases according to the number of buffs on this Champion. Has a 40% chance to unlock a secret skill, Skypiercer, for 1 turn." (Id: 38032)
    4006: "Ally attack",
    # Ex. Longbeard A3: "Attacks 1 enemy with 4 allies. Increases the damage inflicted by allies by 20%." (Id: 271041)
    4007: "Extra turn",
    # Ex. Dhampir A1: "Attacks 1 enemy. Grants an Extra Turn if the target is killed." (Id: 50012)
    4008: "HP Equalize",
    # Ex. Mystic Hand A3: "Heals the ally with the lowest HP by 25%, then equalizes the HP levels of all allies." (Id: 6042)
    4009: "Decrease skill cooldown",
    # Ex. Pain Keeper A3: "Decreases the cooldowns of all ally skills by 1 turn." (Id: 314031)
    4010: "Decrease debuff duration",
    # Ex. Valerie A2: "Increases the duration of all buffs on all allies by 1 turn. Also decreases the duration of all debuffs on all allies by 1 turn. Places a 25% [Increase ATK] buff on all allies for 2 turns." (Id: 45043)
    4011: "Increase buff duration",
    # Ex. Valerie A2: "Increases the duration of all buffs on all allies by 1 turn. Also decreases the duration of all debuffs on all allies by 1 turn. Places a 25% [Increase ATK] buff on all allies for 2 turns." (Id: 45043)
    4012: "Counterattack",
    # Ex. Khoronar A4: "Counterattacks when hit by enemies under [Decrease ATK], [Decrease DEF], or [Decrease SPD] debuffs. Always counterattacks when hit if Minaya is on the same team." (Id: 477042)
    4013: "Increase stat",
    # Ex. Rock Breaker A1: "Attacks 1 enemy. Increases this Champion's DEF by 4% each time this Skill is used. Stacks up to 20%." (Id: 416012)
    4014: "Immunity",
    # Ex. Archmage Hellmut A4: "Immune to Turn Meter decreasing effects." (Id: 505041)
    4017: "Reflect Damage",
    # Ex. Warchief A3: "Reflects 60% of the damage taken back to the attacker. DEF increases by 15% for each dead ally." (Id: ,94032)
    4018: "Transfer damage from allies",
    # Ex. Ursuga Warcaller A4: "Decreases the damage all allies receive from critical hits by 30%. This Champion will receive that damage instead." (Id: 533043)
    5000: "Place debuff",
    # Ex. Drokgul the Gaunt A1: "Attacks 1 enemy. Has a 20% chance of placing a [Stun] debuff for 1 turn." (Id: 479012)
    5001: "Decrease Turn Meter",
    # Ex. Wyvernbane A2: "Attacks 1 enemy. Has a 35% chance of decreasing the target's Turn Meter by 20%." (Id: 518022)
    5002: "Steal buff",
    # Ex. Slitherbrute A2: "Attacks 1 enemy and steals 1 random buff from them." (Id: 293022)
    5003: "Remove buff",
    # Ex. Skinner A2: "Attacks 1 enemy. Removes 2 random buffs from the target." (Id: 108022)
    5004: "Increase cooldown of target's skill(s)",
    # Ex. Hurler A3: "Attacks 1 enemy. Puts the target's skills on cooldown." (Id: 114032)
    5005: "Decrease buff duration",
    # Ex. Arbiter A2: "Attacks all enemies 1 time. Has a 75% chance of decreasing the duration of all enemy buffs by 1 turn." (Id: 356022)
    5007: "Exchange HP",
    # Ex. Centurion A3: "Exchanges remaining HP levels with a target enemy, then equalizes the HP of all allies." (Id: 311041)
    5008: "Increase debuff duration",
    # Ex. Bombardier A1: "Attacks 1 enemy. Has a 5% chance of increasing the duration of all debuffs by 1 turn." (Id: 385042)
    5009: "Decrease target's stat (always max HP so far)",
    # Ex. Outrider A2: "Attacks 1 enemy. Decreases enemy MAX HP by 15% of damage dealt." (Id: 199022)
    5010: "Decrease bomb timer",
    # Ex. Souldrinker A1: "Attacks 1 enemy. Decreases [Bomb] debuff detonation countdowns by 1 turn." (Id: 162012)
    5011: "Debuff spread",
    # Ex. Zavia A4: "Attacks 1 enemy. Applies a [Debuff Spread] effect, taking 4 random debuffs from the target and placing them on all enemies. [...]" (Id: 348052)
    6000: "Damage",
    # Ex. Valerie A1: "Attacks 1 enemy." (Id: 45011)
    7000: "Guaranteed Crit",
    # Ex. Drake A2: "Attacks 1 enemy. If the target has less than 30% HP, this attack is always critical." (Id: 135022)
    7001: "Ignore DEF",
    # Ex. Marksman A3: "Attacks 4 times at random. Each hit has a 25% chance to Ignore DEF." (Id: 11032)
    7002: "Passively decrease enemy ACC",
    # Ex. Kantra the Cyclone A3: "Decreases each enemy's ACC by 10 for each debuff they are under. [...]" (Id: 298041)
    7003: "Increase chance of other effect",
    # Ex. Vergumkaar A1: "Attacks 1 enemy. Has a 35% chance of placing a [Stun] debuff for 1 turn. The chance increases by 15% for each buff on the target." (Id: 532013)
    7004: "Increase damage",
    # Ex. Lord Shazar A1: "Attacks 1 enemy 3 times. Damage increases by 15% for each debuff on the target." (Id: 143012)
    7005: "Ignore certain buffs if certain debuffs present on enemy team or target",
    # Ex. Hound Spawn A3: "Attacks all enemies. Will Ignore DEF and [Block Damage] buffs if the target has a [Freeze] debuff. [Only available when Hellfang is on the same team.]" (Id: 146033)
    7006: "Adjust damage by some value that isn't a function of the ability's damage multiplier",
    # Ex. Corpulent Cadaver A1: "Attacks 1 enemy. Inflicts additional damage if this Champion is under a [Shield] buff. The damage is equal to 30% of the value of the [Shield]." (Id: 441012)
    7007: "Scale ability with number of debuffs on allies",
    # Ex. Grunch Killjoy A3: "Removes all debuffs from all allies, then places one 15% [Continuous Heal] buff for 1 turn on each ally for every debuff removed from them." (Id: 552033)
    9000: "Redirect debuff onto owner",
    # Ex. Pyxniel A4: "Whenever an enemy places a [Freeze] debuff on an ally, has a 20% chance of stealing the [Freeze] debuff and placing it on this Champion instead. [...]" (Id: 553041)
    9001: "Revive self while dead",
    # Ex. Lydia the Deathsiren A6: "[...] If this Champion is dead when an enemy revive is denied, revives this Champion with 50% HP and 50% Turn Meter. [...]" (Id: 471041)
    11000: "Special",
    # Ex. Ma'Shalled A1: "Attacks 1 enemy. Heals this Champion by 30% of the damage inflicted. Will then attack enemies under [Leech] debuffs." (Id: 2103014)
    11001: "Special",
    # Ex. Belanor A4: "Activates this Champion's Swordleader skill. Also activates Zavia's Poison Rain Skill when Zavia is on the same team." (Id: 349053)
}


def campaign_drop_info(data):
    """
    Analyzes drop rates for rewards of all campaign stages, outputs a CSV with information on expected returns per
    run and per point of energy spent.

    :param data: static_data['StageData']['Stages']
    :return: Nothing. Writes result to "raid_campaign_farming_data.csv"
    """

    # Set up output DataFrame
    result_df = pd.DataFrame(columns=["id", "xp/e", "com/e", "unc/e", "rare/e", "silver/e", "shard/e", "e return/e",
                                      "real xp/e"])

    # Iterate stages
    for stage_dict in data:
        # Get internal ID.
        id_string = str(stage_dict["Id"])

        # Stage ID contains various bits of info. Stages not starting with "1" are non campaign stages. Ignore for
        # our present purposes.
        if id_string[0] != "1":
            continue

        # Resource "1" below is energy.
        energy_cost = stage_dict["StartCondition"]["Price"]["RawValues"]["1"]

        # Substring of stage ID indicates which of the 12 areas it's in
        zone = id_string[1:3]

        # Difficulty is encoded by the fourth digit of the ID (1-4)
        # Map this to something readable.
        difficulty = DIFFICULTY_CODES[id_string[3]]

        # End of id identifies which of the 7 stages it is
        substage = id_string[5:]

        # Format the stage into something prettier.
        # Difficulty currently uses first two chars to disambiguate Normal and Nightmare.
        readable_id = f"{zone}-{substage}-{difficulty[0:2]}"
        print(f"\nZone {zone} Stage {substage} {difficulty}")

        # Get amounts of account-level XP, champ XP and silver rewarded
        raw_silver_reward = 0
        reward_account_xp = 0  # Presently unused

        for rew in stage_dict["Rewards"]:
            if rew["Type"] == 3:
                raw_silver_reward = (rew["MaxCount"] + rew["MinCount"]) / 2
            if rew["Type"] == 5:
                reward_account_xp = (rew["MaxCount"] + rew["MinCount"]) / 2
        reward_xp = stage_dict.get("RewardHeroXp") if stage_dict.get("RewardHeroXp") else 0

        # Maintain the probabilities of each potential random reward
        reward_total_weight = 0
        reward_commmon_champ_weight = 0
        reward_uncommmon_champ_weight = 0
        reward_rare_champ_weight = 0
        reward_shard_weight = 0
        reward_shard_quantity = 0
        reward_item_weight = 0
        item_ranks = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        item_rarities = [0.0, 0.0, 0.0, 0.0, 0.0]

        for reward in stage_dict["Reward"]["Rewards"]:
            if reward["Type"] == 4:
                # Artifact drops
                reward_total_weight += reward["Probability"]
                reward_item_weight = reward["Probability"]
            elif reward["Type"] == 2:
                # Mystery shard drops
                # (or "Black Market" item drops, more generally, but in campaign this is always mystery shards)
                reward_total_weight += reward["Probability"]
                reward_shard_weight = reward["Probability"]
                reward_shard_quantity = (reward["MinCount"] + reward["MaxCount"]) / 2
            elif reward["Type"] == 1:
                # Champion drops
                if reward["HeroGrade"] == 1:
                    reward_total_weight += reward["Probability"]
                    reward_commmon_champ_weight += reward["Probability"]
                elif reward["HeroGrade"] == 2:
                    reward_total_weight += reward["Probability"]
                    reward_uncommmon_champ_weight += reward["Probability"]
                elif reward["HeroGrade"] == 3:
                    reward_total_weight += reward["Probability"]
                    reward_rare_champ_weight += reward["Probability"]

        # Get item rank probabilities
        for (rank, prob) in stage_dict["Reward"]["ArtifactProbsByRankId"].items():
            item_ranks[int(rank)-1] = prob/100.0

        # Get item rarity probabilities
        for (rarity, prob) in stage_dict["Reward"]["ArtifactProbsByRarityId"].items():
            item_rarities[int(rarity)-1] = prob/100.0

        # Multiply item rank and rarity probabilities to get probability of each rank/rarity combo
        item_probabilities = reward_item_weight / reward_total_weight * \
            np.matmul(np.array(item_ranks).reshape((6, 1)), np.array(item_rarities).reshape((1, 5)))

        # Get artifact set and kind (e.g. shield, helmet) as these affect the sell price
        item_kind = int(list(stage_dict["Reward"]["ArtifactProbsByKindId"].keys())[0])
        item_set = int(list(stage_dict["Reward"]["ArtifactProbsBySetKindId"].keys())[0])

        # Get the expected sell value of an artifact gained from the stage, weighted by drop chances
        item_sell_expected_value = calculate_expected_sell_value(item_probabilities, item_set-1, item_kind-1)
        # print(f"Expected item sell value per run: {item_sell_expected_value}")

        # This metric represents the amount of effective XP earned by picking up uncommons, rares, and mystery shards
        # in this stage. Each of those things can speed up your XP farming and has a rough energy worth, in terms of
        # the XP they effectively provide.
        energy_return_per_energy = ((reward_rare_champ_weight/reward_total_weight / energy_cost) * (47+1/3) +
                                    (reward_uncommmon_champ_weight/reward_total_weight / energy_cost) * (7+1/3) +
                                    (reward_shard_weight / reward_total_weight * reward_shard_quantity / energy_cost) *
                                    2.452)

        # Wrap it all up
        print(f"Energy cost: {energy_cost} " +
              f"XP per food champ (2x): {reward_xp / 2.0} " +
              f"Commons: {reward_commmon_champ_weight/reward_total_weight} " +
              f"Uncommons: {reward_uncommmon_champ_weight/reward_total_weight} " +
              f"Rares: {reward_rare_champ_weight/reward_total_weight} " +
              f"Silver: {raw_silver_reward + item_sell_expected_value} " +
              f"Shards: {reward_shard_weight/reward_total_weight * reward_shard_quantity}")

        # "id", "xp/e", "com/e", "unc/e", "rare/e", "silver/e", "shard/e", "e/e", "real xp/e"
        result_df.loc[readable_id] = [readable_id,
                                      reward_xp / 2.0 / energy_cost,
                                      reward_commmon_champ_weight/reward_total_weight / energy_cost,
                                      reward_uncommmon_champ_weight/reward_total_weight / energy_cost,
                                      reward_rare_champ_weight/reward_total_weight / energy_cost,
                                      (raw_silver_reward + item_sell_expected_value) / energy_cost,
                                      reward_shard_weight / reward_total_weight * reward_shard_quantity / energy_cost,
                                      energy_return_per_energy,
                                      reward_xp / 2.0 / (energy_cost-energy_return_per_energy)
                                      ]

    result_df.to_csv("raid_campaign_farming_data.csv")


def calculate_expected_sell_value(probabilities, item_set, item_type):
    # Calculate the expected value of a piece of gear, given its item set ID, its artifact type ID, and probabilities
    # of its being various ranks/rarities represented as a probability matrix with 1-norm of 1.

    # Probability matrix should have 6 rows, 5 columns since there are 6 ranks and 5 rarities

    values = ARTIFACT_SET_BASE_PRICES[item_set] * probabilities * ITEM_TYPE_VALUE_MULTIPLIERS[item_type]
    for i in range(len(values)):
        for j in range(len(values[i])):
            values[i][j] = values[i][j] *\
                           ITEM_RARITY_VALUE_MULTIPLIERS[j] *\
                           ITEM_RANK_VALUE_MULTIPLIERS[i] *\
                           ITEM_RANK_SELL_VALUE_MULTIPLIERS[i]
    return np.sum(values)


def champ_abilities_and_multipliers(data):
    """
    Output way too much data on champs and their moves... but still not all of it.
    Writes to csv's.
    (As a side note, it bothers me so that the plural of an acronym requires an apostrophe. It just feels so dirty.)

    :param data: static data json object
    :return: nothing
    """

    # Create dict for quickly locating skill info
    skill_data_by_id = {}
    for skill in data["SkillData"]["SkillTypes"]:
        skill_data_by_id[skill.get("Id")] = skill

    # Initialize
    champ_info_df = pd.DataFrame(columns=["id", "name", "rarity", "affinity", "role", "faction",
                                          "hp", "atk", "def", "spd", "cr_rate", "cr_dmg", "res", "acc",
                                          "aura_stat", "aura_amt", "aura_area", "aura_affinity",
                                          "champ_status", "released", "hidden_name"  # , "cr_heal"
                                          ])

    # Initialize
    basics_df = pd.DataFrame(columns=[
        "champ_name", "rarity", "affinity", "role", "faction",
        "hp", "atk", "def", "spd", "cr_rate", "cr_dmg", "res", "acc",
        "aura_stat", "aura_amt", "aura_area", "aura_affinity",
        "skill_index", "skill_name", "skill_cd_booked", "skill_cd_unbooked",
        "skill_desc", "book_effects", "multiplier(s)",
        "skill_name_hidden", "skill_desc_hidden",
        "champ_status", "released", "hidden_name"  # , "cr_heal"
    ])

    # Initialize
    champ_move_df = pd.DataFrame(columns=["id", "name", "rarity", "affinity", "role", "faction",

                                          "skill_index", "skill_name", "skill_cd_booked", "skill_cd_unbooked",
                                          "skill_desc", "book_effects", "multiplier", "num_hits",
                                          "book_dmg_mul", "book_heal_mul", "book_shield_mul",
                                          "calculated_damage", "damage_per_turn",
                                          "status_type", "status_duration", "cd_minus_duration",
                                          "effect_chance_booked", "effect_chance_unbooked",
                                          "target_type", "target_type_code",
                                          "effect_type_desc", "effect_type_code", "condition", "effect_id",
                                          "skill_name_hidden", "skill_desc_hidden", "skill_id",

                                          "hp", "atk", "def", "spd", "cr_rate", "cr_dmg", "res", "acc",
                                          "aura_stat", "aura_amt", "aura_area", "aura_affinity",
                                          "champ_status", "released", "hidden_name"  # , "cr_heal"
                                          ])

    # Here goes nothing
    for champ in data["HeroData"]["HeroTypes"]:
        if not (champ.get("Id") % 10 == 6 or champ.get("Rarity") == 1) or not(champ.get("Fraction")):
            # Skip not-fully-ascended champs, common champs, factionless (i.e. non-playable) champs
            # Champs without factions seem to be bosses and NPCs.
            continue

        # Get localized name and default internal name
        champ_name = data.get("StaticDataLocalization").get(champ.get("Name").get("Key"))
        champ_name_hidden = champ.get("Name").get("DefaultValue")

        # Get basic info, map it to something human-friendly
        champ_rarity = CHAMP_RARITIES[champ.get("Rarity")]
        champ_affinity = AFFINITIES[champ.get("Element")]
        champ_type = CHAMP_TYPES[champ.get("Role")]
        champ_faction = FACTIONS[champ.get("Fraction")]

        # The "status" value seems to be related to whether or not a champ is in development.
        # 40 = champ is visible/playable. Shows up in champ Index.
        # 35 = champ not yet visible in game. Has all names and descriptions; seems like it just needs to be "turned on"
        # 30, 10 = seems farther from release, may be missing names and descriptions.
        champ_status = champ.get("Status")

        # Get aura info
        champ_aura_info = champ.get("LeaderSkill")
        champ_aura_stat = STAT_TYPES[champ_aura_info.get("StatKindId") - 1] if champ_aura_info else ""
        champ_aura_amt = champ_aura_info.get("Amount") / 4294967296 if champ_aura_info else ""
        if champ_aura_info and champ_aura_info.get("isAbsolute") == 0:
            champ_aura_amt *= 100
        if champ_aura_info and champ_aura_info.get("Element"):
            champ_aura_affinity = AFFINITIES[champ_aura_info.get("Element")]
        else:
            champ_aura_affinity = "All"
        if champ_aura_info and champ_aura_info.get("Area"):
            champ_aura_area = AURA_AREAS[champ_aura_info.get("Area")]
        else:
            champ_aura_area = "All Battles"

        # Get base stats, before dividing
        raw_hp = champ.get("BaseStats").get("Health")
        raw_atk = champ.get("BaseStats").get("Attack")
        raw_def = champ.get("BaseStats").get("Defence")

        # print(f'{champ_name},{raw_hp},{raw_atk},{raw_def}')

        # Get base stats
        champ_hp = raw_hp / HP_DIVISOR  # Divisors here estimated using all legendaries' displayed values
        champ_atk = raw_atk / ATK_DEF_DIVISOR  # as of 12-15-2020. In-game displayed values aren't always accurate.
        champ_def = raw_def / ATK_DEF_DIVISOR  # E.G. displayed base HP rounds to multiple of 15.
        champ_spd = champ.get("BaseStats").get("Speed") / 4294967296.  # Note: divisor is 2^32
        champ_res = champ.get("BaseStats").get("Resistance") / 4294967296.
        champ_acc = champ.get("BaseStats").get("Accuracy") / 4294967296.
        champ_crch = champ.get("BaseStats").get("CriticalChance") / 4294967296.
        champ_cd = champ.get("BaseStats").get("CriticalDamage") / 4294967296.
        # champ_cr_heal = champ.get("BaseStats").get("CriticalHeal") / 4294967296.  # Always 50. BOOORINGGGG.

        # Make our row
        this_champ = {
            "id": champ.get("Id"),
            "name": champ_name,
            "rarity": champ_rarity,
            "affinity": champ_affinity,
            "role": champ_type,
            "faction": champ_faction,
            "hp": round(champ_hp / 15) * 15,
            "atk": round(champ_atk),
            "def": round(champ_def),
            "spd": round(champ_spd),
            "cr_rate": round(champ_crch),
            "cr_dmg": round(champ_cd),
            "res": round(champ_res),
            "acc": round(champ_acc),
            "aura_stat": champ_aura_stat,
            "aura_amt": "" if isinstance(champ_aura_amt, str) else round(champ_aura_amt, 2),
            "aura_area": champ_aura_area if (champ_aura_stat != "") else "",
            "aura_affinity": champ_aura_affinity if (champ_aura_stat != "") else "",
            "hidden_name": champ_name_hidden,
            "champ_status": champ_status,
            "released": "Y" if champ_status == 40 else "N",
            # "cr_heal": champ_cr_heal,
            # "raw_hp": raw_hp,
            # "raw_atk": raw_atk,
            # "raw_def": raw_def,
        }

        # Add row for champ to basic champ info DF
        champ_info_df = champ_info_df.append(this_champ, ignore_index=True)

        # Get skill info for current champ
        skill_index = 0
        for skill_id in champ.get("SkillTypeIds"):

            this_champ_move = dict(this_champ)

            skill_index += 1  # A1, A2, A3, etc.
            this_champ_move["skill_index"] = "A" + str(skill_index)
            this_champ_move["skill_id"] = skill_id

            # Use that handy dict we made earlier
            skill_data = skill_data_by_id.get(skill_id)

            # Initialize book bonuses
            book_damage_multiplier = 1.0
            book_heal_multiplier = 1.0
            book_shield_multiplier = 1.0
            book_effect_increase = 0.0
            book_cdr = 0

            # Get basic skill info - names, descriptions, etc
            skill_name = data.get("StaticDataLocalization").get(skill_data.get("Name").get("Key"))
            this_champ_move["skill_name"] = skill_name
            skill_name_hidden = skill_data.get("Name").get("DefaultValue")
            this_champ_move["skill_name_hidden"] = skill_name_hidden
            skill_desc = data.get("StaticDataLocalization").get(skill_data.get("Description").get("Key")).\
                replace("\\r", " ").replace("\\n", " ").replace("\r", " ").replace("\n", " ")
            # Clean text color tags from skill descriptions
            this_champ_move["skill_desc"] = skill_desc.\
                replace("<color=#1ee600>", "").\
                replace("<color=#F3BC02>", "").\
                replace("<color=#E85CFC>", "").\
                replace("</color>", "")

            skill_desc_hidden = skill_data.get("Description").get("DefaultValue").\
                replace("\\r", " ").replace("\\n", " ").replace("\r", " ").replace("\n", " ")
            this_champ_move["skill_desc_hidden"] = skill_desc_hidden

            # Get unbooked CD
            skill_cooldown = skill_data.get("Cooldown")
            this_champ_move["skill_cd_unbooked"] = skill_cooldown

            book_increase_descriptions = []
            for book in skill_data.get("SkillLevelBonuses", []):

                if book.get("SkillBonusType") == 0:  # Damage
                    increase = book.get("Value") / 4294967296
                    book_damage_multiplier += increase
                    book_increase_descriptions.append(f"+{round(increase*100)}% Damage")

                elif book.get("SkillBonusType") == 1:  # Heal
                    increase = book.get("Value") / 4294967296
                    book_heal_multiplier += increase
                    book_increase_descriptions.append(f"+{round(increase*100)}% Heal")

                elif book.get("SkillBonusType") == 2:  # Effect chance
                    increase = book.get("Value") / 4294967296
                    book_effect_increase += increase
                    book_increase_descriptions.append(f"+{round(increase*100)}% Buff/Debuff Chance")

                elif book.get("SkillBonusType") == 3:  # Cooldown
                    decrease = book.get("Value") / 4294967296
                    book_cdr += decrease
                    book_increase_descriptions.append(f"-{int(round(decrease))} Cooldown")

                elif book.get("SkillBonusType") == 4:  # Shield. Recently split off from Heal/Shield.
                    increase = book.get("Value") / 4294967296
                    book_shield_multiplier += increase
                    book_increase_descriptions.append(f"+{round(increase*100)}% Shield")

                elif book.get("SkillBonusType"):
                    # This shouldn't happen, but it'd be very interesting if it did...
                    print(f"Non standard book effect {repr(book.get('SkillBonusType'))} found for skill ID {skill_id}")

            # Get aggregate effects of skill increases
            this_champ_move["skill_cd_booked"] = skill_cooldown - round(book_cdr)
            this_champ_move["book_effects"] = ", ".join(book_increase_descriptions)
            this_champ_move["book_dmg_mul"] = round(book_damage_multiplier, 2)
            this_champ_move["book_heal_mul"] = round(book_heal_multiplier, 2)
            this_champ_move["book_shield_mul"] = round(book_shield_multiplier, 2)

            # Make list of multipliers for condensed view
            multipliers = []

            # Make cumulative damage for moves with multiple damaging effects
            # TODO: this
            move_total_damage = 0

            # Add a row for each effect
            for effect in skill_data.get("Effects", []):

                this_champ_effect = dict(this_champ_move)

                # Get target type. This indicates which champs are affected.
                target_type_ind = effect.get('TargetParams').get('TargetType', None)

                # Make it readable.
                this_champ_effect["target_type_code"] = target_type_ind
                this_champ_effect["effect_id"] = effect.get("Id", None)

                # We're breaking new ground!
                if target_type_ind <= len(EFFECT_TARGET_TYPES):
                    target_type = EFFECT_TARGET_TYPES[target_type_ind]
                else:
                    target_type = str(target_type_ind)

                ###

                # Dead code, ew.
                # This is from when I was first writing this and only interested in AoE damage statistics.
                # Here for posterity's sake.
                # From humble beginnings.

                # if effect.get('MultiplierFormula'):
                #     print(f"MULTIPLIER: ({effect.get('MultiplierFormula', 0)}) * {effect.get('Count', 1)}")
                # print(f"TARGET: {target_type}")
                # if target_type_ind == 8 and effect.get('MultiplierFormula'):
                #     formula = effect.get('MultiplierFormula')
                #     formatted_formula = formula.replace("HP", str(int(champ_hp))).\
                #         replace("ATK", str(int(champ_atk))).\
                #         replace("DEF", str(int(champ_def)))
                #     formatted_formula_complete = f"({formatted_formula})" +\
                #                                  f"*{effect.get('Count', 1)}" +\
                #                                  f"*{round(book_damage_multiplier,2)}"
                #     try:
                #         result = eval(parser.expr(formatted_formula_complete).compile())
                #         print(f"{formatted_formula_complete} = {result}")
                #         print(f"{champ_name},{champ_rarity},{champ_affinity},A{skill_index},{round(result,3)}" +
                #               f",{formatted_formula_complete},{formula}," +
                #               f"{skill_cooldown - round(book_cdr)},\"{skill_desc}\"")
                #     except:
                #         print(f"Could not parse multiplier formula: {formatted_formula}")
                #         pass

                ###

                this_champ_effect["target_type"] = target_type
                this_champ_effect['multiplier'] = "'" + effect.get('MultiplierFormula', "")
                this_champ_effect['num_hits'] = effect.get("Count", 1)

                if effect.get('MultiplierFormula'):
                    multipliers.append(effect.get('MultiplierFormula'))

                # Effect KindId tells what the skill does. See the module level constant EFFECT_TYPES for details.
                effect_kind = effect.get("KindId", None)
                this_champ_effect["effect_type_desc"] = EFFECT_TYPES[effect_kind]
                this_champ_effect["effect_type_code"] = effect_kind

                # Add chance of bonus effect, if applicable
                if effect.get("Chance"):
                    this_champ_effect["effect_chance_unbooked"] = round(effect.get("Chance") / (2**32), 2)
                    this_champ_effect["effect_chance_booked"] = round(effect.get("Chance") / (2**32) +
                                                                      book_effect_increase, 2)
                else:
                    this_champ_effect["effect_chance_unbooked"] = 1.00
                    this_champ_effect["effect_chance_booked"] = 1.00

                if effect.get('MultiplierFormula'):
                    formula = effect.get('MultiplierFormula')
                    formatted_formula = formula.replace("MAX_STAMINA", "100.0"). \
                        replace("HERO_LEVEL", "60.0")

                    # There's surely a better way to do the below regex sub but I can't be bothered

                    formatted_formula = re.sub(r"^HP$", str(round(champ_hp)), formatted_formula)
                    formatted_formula = re.sub(r"^ATK$", str(round(champ_atk)), formatted_formula)
                    formatted_formula = re.sub(r"^DEF$", str(round(champ_def)), formatted_formula)
                    formatted_formula = re.sub(r"^HP([-*+/ ()])", str(round(champ_hp)) + r"\g<1>", formatted_formula)
                    formatted_formula = re.sub(r"^ATK([-*+/ ()])", str(round(champ_atk)) + r"\g<1>", formatted_formula)
                    formatted_formula = re.sub(r"^DEF([-*+/ ()])", str(round(champ_def)) + r"\g<1>", formatted_formula)
                    formatted_formula = re.sub(r"([-*+/ ()])HP$", r"\g<1>" + str(round(champ_hp)), formatted_formula)
                    formatted_formula = re.sub(r"([-*+/ ()])ATK$", r"\g<1>" + str(round(champ_atk)), formatted_formula)
                    formatted_formula = re.sub(r"([-*+/ ()])DEF$", r"\g<1>" + str(round(champ_def)), formatted_formula)
                    formatted_formula = re.sub(r"([-*+/ ()])HP([-*+/ ()])",
                                               r"\g<1>" + str(round(champ_hp)) + r"\g<2>", formatted_formula)
                    formatted_formula = re.sub(r"([-*+/ ()])ATK([-*+/ ()])",
                                               r"\g<1>" + str(round(champ_atk)) + r"\g<2>", formatted_formula)
                    formatted_formula = re.sub(r"([-*+/ ()])DEF([-*+/ ()])",
                                               r"\g<1>" + str(round(champ_def)) + r"\g<2>", formatted_formula)

                    if effect_kind in [5000, 6000]:
                        # do damage-y things
                        # 5000 included because bombs have multipliers

                        if target_type_ind == 6 \
                                and effect.get("TargetParams", {}).get("TargetType") == 6 \
                                and effect.get("TargetParams", {}).get("Exclusive") == 1:
                            # Count only the first hit for exclusive random hitters - each enemy can be hit only once
                            # This solves the weirdness with Galkut and Archmage Hellmut having ridiculous damage vals
                            formatted_formula_complete = f"({formatted_formula})" +\
                                                         f"*{round(book_damage_multiplier,2)}"
                        else:
                            formatted_formula_complete = f"({formatted_formula})" +\
                                                         f"*{effect.get('Count', 1)}" +\
                                                         f"*{round(book_damage_multiplier,2)}"

                        # Archmage Hellmut:
                        # TargetParams has
                        #   TargetType 6 (random enemies)
                        #   Exclusion 2
                        #   Exclusive 1
                        #   FirstHitInSelected 0
                        # Galkut does not have Exclusion 2, has FirstHitInSelected 1
                        # This is because Archmage Hellmut's will hit all enemies but the initial skill target (if crit)
                        # -> Exclusive means it doesn't hit an enemy twice
                        # -> Exclusion indicates a target type that will not be hit by the random attack

                    elif effect_kind in [0, 1000]:
                        # do revive-y heal-y things
                        formatted_formula_complete = f"({formatted_formula})" +\
                                                     f"*{effect.get('Count', 1)}" +\
                                                     f"*{round(book_heal_multiplier,2)}"
                    elif effect_kind in [4000]:
                        # do shield-y things
                        formatted_formula_complete = f"({formatted_formula})" +\
                                                     f"*{effect.get('Count', 1)}" +\
                                                     f"*{round(book_shield_multiplier,2)}"
                    else:
                        # do other, presumably turn meter-y things
                        formatted_formula_complete = f"({formatted_formula})" + \
                                                     f"*{effect.get('Count', 1)}"

                    try:
                        # Parse the multiplier formula and calculate result
                        result = eval(parser.expr(formatted_formula_complete).compile())
                        this_champ_effect['calculated_damage'] = round(result, 2)
                        # Get damage (or healing etc) per turn using booked cooldown
                        this_champ_effect['damage_per_turn'] = round(result/(max(skill_cooldown - round(book_cdr), 1)),
                                                                     2)
                    except:
                        # Encountered some nonstandard multiplier. There are many of these.
                        print(f"Could not parse multiplier formula: {formatted_formula}")
                        this_champ_effect['calculated_damage'] = None

                this_champ_effect['condition'] = effect.get("Condition", None)

                # Get info on the buff or debuff that is applied, if applicable
                if effect.get("ApplyStatusEffectParams"):
                    for status in effect.get("ApplyStatusEffectParams").get("StatusEffectInfos"):
                        this_champ_effect['status_type'] = STATUS_TYPES.get(status.get("TypeId"))
                        this_champ_effect['status_duration'] = status.get("Duration")
                        this_champ_effect['cd_minus_duration'] = skill_cooldown - round(book_cdr) -\
                            status.get("Duration")
                        champ_move_df = champ_move_df.append(this_champ_effect, ignore_index=True)
                else:
                    champ_move_df = champ_move_df.append(this_champ_effect, ignore_index=True)

            # Add row to basics df
            new_row = {
                "champ_name": champ_name,
                "rarity": champ_rarity,
                "affinity": champ_affinity,
                "role": champ_type,
                "faction": champ_faction,
                "hp": round(champ_hp / 15) * 15,
                "atk": round(champ_atk),
                "def": round(champ_def),
                "spd": round(champ_spd),
                "cr_rate": round(champ_crch),
                "cr_dmg": round(champ_cd),
                "res": round(champ_res),
                "acc": round(champ_acc),
                "aura_stat": champ_aura_stat,
                "aura_amt": "" if isinstance(champ_aura_amt, str) else round(champ_aura_amt, 2),
                "aura_area": champ_aura_area if (champ_aura_stat != "") else "",
                "aura_affinity": champ_aura_affinity if (champ_aura_stat != "") else "",
                "hidden_name": champ_name_hidden,
                "champ_status": champ_status,
                "released": "Y" if champ_status == 40 else "N",

                "skill_index": "A" + str(skill_index),
                "skill_name": skill_name,
                "skill_cd_booked": skill_cooldown - round(book_cdr),
                "skill_cd_unbooked": skill_cooldown,

                "skill_desc": skill_desc.\
                    replace("<color=#1ee600>", "").
                    replace("<color=#F3BC02>", "").
                    replace("<color=#E85CFC>", "").
                    replace("</color>", ""),
                "book_effects": ", ".join(book_increase_descriptions),
                "multiplier(s)": ", ".join(multipliers),

                "skill_name_hidden": skill_name_hidden,
                "skill_desc_hidden": skill_desc_hidden

            }

            basics_df = basics_df.append(new_row, ignore_index=True)

    champ_info_df.drop_duplicates(inplace=True, ignore_index=True)
    champ_move_df.drop_duplicates(inplace=True, ignore_index=True)
    basics_df.drop_duplicates(inplace=True, ignore_index=True)

    champ_info_df.to_csv("champ_basic_info.csv")
    champ_move_df.to_csv("champ_move_details.csv")
    basics_df.to_csv("champ_moves_basic.csv")


if __name__ == '__main__':

    with open("static_data.json") as json_in:
        static_data = json.loads(json_in.read())

    campaign_drop_info(static_data['StageData']['Stages'])

    champ_abilities_and_multipliers(static_data)
