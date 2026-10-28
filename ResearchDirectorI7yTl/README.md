# Cheat Menu

A cheat menu for Abiotic Factor, made with the official Mod Editor. Version **0.8.4**. It has five tabs, and the **ALL** tab holds 133 of the Mod Editor's built-in cheat commands. The menu is a panel docked on the right edge of the screen.

## Use

Craft the **Cheat Remote** from **1 Tech Scrap + 1 Metal Scrap** (no bench needed). It shows up as a new recipe once you've picked up both kinds of scrap; on a save where you already have them, it appears when the world loads. Like the game's other new recipes, you may need to research it once before you can craft it.

Put the remote in your hotbar, hold it, and left-click to open the menu. **Esc** or the **CLOSE** button closes it. While it's open, the game ignores movement, mouse look and firing, but the hotbar keys **1-0** and the **mouse wheel** still switch the item in your hand. That is how you pick what the held-item actions work on: open the menu with the remote, press the number of the slot you want (say 1 for your gun), then click Refill ammo, Repair held item or Recharge held item. The status line says which slot you are holding. Number keys typed into a menu text box go into the box and do not switch items.

The menu has five tabs:

- **Player:** eight cheats you click on or off: god mode, infinite stamina, infinite ammo, free crafting, no hunger/thirst drain, enemies ignore you, ghost/noclip and master key. Each tile shows its current ON/OFF state, which it reads from your character. Quick actions: heal & revive, refill ammo, repair held item, recharge held item.
- **Survival:** **Restore everything**, plus a live bar and value for food, water, tiredness, bladder and radiation. Each stat has -25, +25 and Fill/Rest/Relieve/Clear buttons.
- **Items:** search by name or ID, for example `battery`. The first 60 matches are listed with icons. Click one, pick an amount (1, 5, 10, 25, 100, or type one), then **Add to inventory** or **Drop at my feet**.
- **World:** +1 hour, +6 hours, skip to morning or nightfall, the day/night cycle toggle, the six weather events, and clear weather.
- **ALL:** every cheat from the Mod Editor's own cheat menu that works in the released game (133 commands). Type in the search box to filter by name, description or category (Player, Teleport, Items, Skills & buffs, Look, NPCs & pets, World & time, Progress, Saves & HUD, Debug). Click a command to see what it does and, for switches and values, its current state. Commands that take input show one or two boxes, each with a list of the game's own options (items, NPCs, buffs, traits, weather, lighting presets, world flags, appearance parts and so on). Type in a box to filter its list, click an option to fill the box, then press **RUN**. Amount boxes start at the game's default and show the allowed range. Debug views are marked "(debug view)" and may show nothing in the released game, which strips debug drawing. For hours or days, use Add Time Minutes (60 = 1 hour, 1440 = 1 day).

The status line at the bottom says what the last click did. The menu works in single player and for the host. Other players see "Only the host can use cheats."

No Python, DLL or UE4SS is needed at runtime. Windows only.
