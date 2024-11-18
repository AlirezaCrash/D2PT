import json
import re
import os
import glob

# Function to normalize hero names
def normalize_hero_name(name):
    return name.replace('_', '').lower()

# Function to get the nearest minute (60-second interval)
def get_nearest_minute(time):
    return (time // 60) * 60

# Function to get or create hero data
def get_or_create_hero(heroes, hero_name):
    normalized_name = normalize_hero_name(hero_name)
    if normalized_name not in heroes:
        heroes[normalized_name] = {
            "heroName": normalized_name,
            "networths": {},
            "items": [],
            "positions": [],
            "last_networth": None,  # To store the last networth
            "last_time": None       # To store the time of the last networth
        }
    return heroes[normalized_name]

# Function to process a single file
def process_file(input_file):
    heroes = {}
    output_file = os.path.splitext(input_file)[0] + '.json'

    # Regular expressions for matching relevant lines
    interval_pattern = re.compile(r'"type":"interval","unit":"CDOTA_Unit_Hero_(\w+)"')
    purchase_pattern = re.compile(r'"type":"DOTA_COMBATLOG_PURCHASE".*"targetname":"npc_dota_hero_(\w+)".*"valuename":"(item_\w+)"')

    # Read the input file and process each line
    with open(input_file, 'r') as file:
        for line in file:
            data = json.loads(line.strip())
            
            # Process interval data (for networth and position)
            interval_match = interval_pattern.search(line)
            if interval_match:
                hero_name = interval_match.group(1)
                hero_data = get_or_create_hero(heroes, hero_name)
                
                # Record networth at 60-second intervals
                nearest_minute = get_nearest_minute(data["time"])
                if nearest_minute not in hero_data["networths"]:
                    hero_data["networths"][nearest_minute] = data["networth"]
                
                # Update last networth and its time
                hero_data["last_networth"] = data["networth"]
                hero_data["last_time"] = data["time"]

                hero_data["positions"].append({
                    "x": data["x"],
                    "y": data["y"],
                    "time": data["time"]
                })
            
            # Process purchase data
            purchase_match = purchase_pattern.search(line)
            if purchase_match:
                hero_name = purchase_match.group(1)
                item_name = purchase_match.group(2)
                hero_data = get_or_create_hero(heroes, hero_name)
                hero_data["items"].append({
                    "itemName": item_name,
                    "purchaseTime": data["time"]
                })

    # Convert networths from dict to list of dicts for each hero
    for hero in heroes.values():
        # Convert networths to a list of dicts
        hero["networths"] = [{"time": time, "networth": networth} for time, networth in sorted(hero["networths"].items())]
        
        # Add the last recorded networth if it exists
        if hero["last_networth"] is not None and hero["last_time"] is not None:
            hero["networths"].append({"time": hero["last_time"], "networth": hero["last_networth"]})

    # Convert the heroes dictionary to a list
    hero_list = list(heroes.values())

    # Write the combined JSON array to the output file
    with open(output_file, 'w') as file:
        json.dump(hero_list, file, indent=2)

    print(f"Processed {input_file} -> {output_file}")

# Main execution
if __name__ == "__main__":
    input_files = glob.glob("*.txt")

    if not input_files:
        print("No .txt files found in the current directory.")
    else:
        for input_file in input_files:
            process_file(input_file)

    print("All files processed.")