import argparse
from re import L
from valvebsp import Bsp
from valvebsp.lumps import *
from random import randint

# There are ones I could think of, send in a PR/Issue if you think there are any more!
non_positional_ents = ["logic_auto", "env_entity_igniter", "filter_activator_name", "ai_speechfilter", "ai_goal_lead_weapon", "logic_compare", "game_player_equip", "env_fog_controller", "env_tonemap_controller", "logic_relay", "water_lod_control", "ai_goal_follow", "env_credits", "game_text", "filter_enemy", "material_modify_control", "shadow_control", "filter_damage_type", "logic_timer", "logic_branch", "ai_goal_standoff", "ai_relationship",
                       "tanktrain_aitarget", "filter_activator_class", "logic_case", "math_remap", "ai_changetarget", "filter_activator_team", "tanktrain_ai", "env_sun", "env_entity_dissolver", "light_environment", "game_score", "ai_goal_assault", "filter_multi", "ai_goal_lead", "ai_citizen_response_system", "ai_goal_actbusy_queue", "env_texturetoggle", "scripted_scene", "ai_ally_manager", "env_fade", "game_ui", "math_counter", "ai_script_conditions"]


def isbitset(val, bit):
    return (val & (1 << bit)) != 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("path", help="The path of the BSP to obfuscate.")
    parser.add_argument("-o", "--output", default="",
                        help="Where to save the obfuscated BSP, overrides by default.")

    # Obfuscation Options
    parser.add_argument("--brush", action="store_true",
                        help="Enables brush obfuscation.")
    parser.add_argument("--texture", action="store_true",
                        help="Enables texture obfuscation.")
    parser.add_argument("--entity_relocation", action="store_true",
                        help="Enables entity relocation. [Relocates before extraction!]")
    parser.add_argument("--entity_extraction",
                        action="store_true", help="Enables entity extraction.")
    parser.add_argument("--entity_garbage", action="store_true",
                        help="Enables entity garbage [REQUIRES ENTITY EXTRACTION].")
    parser.add_argument("--crash_game", action="store_true",
                        help="Enables crashing the game on map load [REQUIRES ENTITY GARBAGE].")
    parser.add_argument("--entity_tag", type=str, default="PROTECTED MAP. FUCK OFF.",
                        help="Message to display in game [REQUIRES ENTITY GARBAGE, MAX 48 CHARS].")

    args = parser.parse_args()

    print(f"Loading {args.path}...")
    bsp = Bsp(args.path)

    if args.brush:
        print("Obfuscating brushes...")
        for brush in bsp[LUMP_BRUSHES]:
            if brush.numSides == 6:
                # It's trivial really
                brush.numSides = 0

    if args.texture:
        print("Obfuscating brush textures...")
        upperbound = len(bsp[LUMP_TEXINFO]) - 1
        for side in bsp[LUMP_BRUSHSIDES]:
            flags = bsp[LUMP_TEXINFO][side.texInfo].flags
            # I don't know if more flags should be skipped
            if not (flags["SURF_SKY"] or flags["SURF_SKY2D"]):
                # Randomise the brush side texture
                side.texInfo = randint(0, upperbound)

    if args.entity_relocation:
        print("Relocating non-positional based entities...")

        for ent in bsp[LUMP_ENTITIES]:
            # This is some terrible code, but it works.
            for prop in ent:
                if prop[0] == "classname" and prop[1].lower() in non_positional_ents:
                    for prop2 in ent:
                        if prop2[0] == "origin":
                            prop2[1] = "0 0 0"

    # 21+ (incl.) doesn't have support for loading external lumps
    if bsp.header["version"] != 19 and bsp.header["version"] != 20:
        print("ERROR: CANNOT EXTRACT ENTITIES. ONLY WORKS WITH BSP VERSIONS 19 AND 20! SKIPPING...")
    elif args.entity_extraction:
        print("Extracting entities...")
        print("WARNING: This mode is a tiny bit experimental, should work 100% of the time though!")
        with open(args.path, "rb") as file:
            file.seek(bsp.header["lump_t"][0]["fileofs"])
            lump0_data = file.read(bsp.header["lump_t"][0]["filelen"])

            with open((args.output or args.path).replace(".bsp", "_l_0.lmp"), "wb") as outFile:
                # Write the output .lmp
                outFile.write(0x14.to_bytes(4, byteorder="little"))
                outFile.write(0x0.to_bytes(4, byteorder="little"))
                outFile.write(bsp.header["lump_t"][0]["version"].to_bytes(
                    4, byteorder="little"))
                outFile.write(bsp.header["lump_t"][0]["filelen"].to_bytes(
                    4, byteorder="little"))
                outFile.write(bsp.header["mapRevision"].to_bytes(
                    4, byteorder="little"))
                outFile.write(lump0_data)
                print("Wrote entites lump to " +
                      (args.output or args.path).replace(".bsp", "_l_0.lmp"))

        # Set the only entity to be the worldspawn ent
        bsp[LUMP_ENTITIES] = [bsp[LUMP_ENTITIES][0]]

        if args.entity_garbage:
            print("Adding garbage entities to the BSP...")
            # The main timer
            bsp[LUMP_ENTITIES].append([
                ["origin", "0 0 0"],
                ["RefireTime", "5"],
                ["classname", "logic_timer"],
                ["OnTimer", "point_*,Command,say test,0,-1"],
                ["OnTimer", "env_entity_maker,SetParent,!player,0,-1"],
                ["OnTimer", "env_entity_maker,ForceSpawn,,0,-1"],
                ["OnTimer", "ambient_generic,PlaySound,,0,-1"],
                ["OnTimer", "game_text,Display,,0,-1"],
                ["OnTimer", "env_entity_maker,SetParentAttachment,eyes,0,-1"]])

            bsp[LUMP_ENTITIES].append([
                ["origin", "0 0 0"],
                ["y", "-1"],
                ["x", "-1"],
                ["message", args.entity_tag.ljust(48)],
                ["holdtime", "3"],
                ["fxtime", "1"],
                ["fadeout", "1"],
                ["fadein", "1"],
                ["color2", "255 255 255"],
                ["color", "255 0 0"],
                ["channel", "3"],
                ["classname", "game_text"]
            ])

            bsp[LUMP_ENTITIES].append([
                ["origin", f"0 0 0"],
                ["volstart", "0"],
                ["spinup", "0"],
                ["spindown", "0"],
                ["spawnflags", "49"],
                ["radius", "100000"],
                ["preset", "0"],
                ["pitchstart", "100"],
                ["pitch", "100"],
                ["message",
                    "ambient/alarms/klaxon1.wav"],
                ["lfotype", "0"],
                ["lforate", "0"],
                ["lfomodvol", "0"],
                ["lfomodpitch", "0"],
                ["health", "10"],
                ["fadeoutsecs", "0"],
                ["fadeinsecs", "0"],
                ["cspinup", "0"],
                ["classname", "ambient_generic"]])

            for x in range(-16000, 18000, 4000):
                for y in range(-16000, 18000, 4000):
                    for z in range(-16000, 18000, 4000):
                        bsp[LUMP_ENTITIES].append([
                            ["origin", f"{x} {y} {z}"],
                            ["radius", "8192"],
                            ["message", args.entity_tag.ljust(48)],
                            ["classname", "point_message"]
                        ])

            for i in range(0, 16):
                bsp[LUMP_ENTITIES].append([
                    ["origin", f"0 0 0"],
                    ["EntityTemplate", "template"],
                    ["classname", "env_entity_maker"]])

                randomID = randint(384, 34384)
                bsp[LUMP_ENTITIES].append([
                    ["origin", f"0 0 0"],
                    ["Template01", f"{randomID}"],
                    ["targetname", "template"],
                    ["spawnflags", "2"],
                    ["classname", "point_template"]
                ])

                bsp[LUMP_ENTITIES].append([
                    ["origin", f"0 0 0"],
                    ["targetname", f"{randomID}"],
                    ["spawnflags", "25860"],
                    ["gmod_allowphysgun", "0"],
                    ["gmod_allowtools", "none"],
                    ["classname", "npc_manhack"]
                ])

            if args.crash_game:
                print("Removing worldspawn entity to crash game...")
                bsp[LUMP_ENTITIES].pop(0)

    print(f"Saving deobfuscated BSP as {args.output or args.path}...")
    bsp.save(args.output)
