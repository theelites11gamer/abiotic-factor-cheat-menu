# Cheat Menu for Abiotic Factor (Mod Editor project)

This is the editor source of the **Cheat Menu** mod, made with the official Abiotic Factor Mod Editor. To play it, you don't need this repo: subscribe to the mod in the game's mod browser. This repo is for people who want to open, change or rebuild it.

What the mod does and how to use it in game: [ResearchDirectorI7yTl/README.md](ResearchDirectorI7yTl/README.md).

Status: 0.8.4 was play-tested in the Mod Editor, and its mod.io cloud cook succeeded. It has not been played in the Steam game yet.

## What's not in this repo, and why

The menu's commands are the Mod Editor's own cheat-command Blueprints (`/Game/Blueprints/GameCommands/...`). They are Deep Field Games' work and ship only with the Mod Editor, so this repo doesn't include copies of them. Instead, `setup/copy_game_commands.py` makes the 139 copies from your own Mod Editor install. The finished mod on mod.io contains them in cooked form, the way every Mod Editor mod ships game content it builds on.

## License

The mod's own work in this repo (the menu, the Cheat Remote, the scripts and the docs) is under the [MIT License](LICENSE). That doesn't cover Abiotic Factor itself. The game's assets, the command Blueprints the setup script copies, and the game text and item data the mod refers to all belong to Deep Field Games.

## Setup

You need the Abiotic Factor Mod Editor (free, from the Epic Games launcher).

1. Clone or download this repo. The `ResearchDirectorI7yTl` folder is the Mod Editor project.
2. Open it in the Mod Editor.
3. **Before you open any of its assets**, type this into the **Cmd** box at the bottom of the editor window, using your own path:

   ```
   py "C:/path/to/this/repo/setup/copy_game_commands.py"
   ```

   The Output Log should end with `CHEATMENU_SETUP: 139 command Blueprints present, 139 copied now.`
4. Close the editor. If it offers to save anything else, choose **Don't Save**. Then open the project again.

Until step 3 has run, the menu widget and the command rows point at Blueprints that don't exist yet. Opening or saving them before then can wipe those references for good, and you'd have to re-clone.

## Uploading your own version

`ResearchDirectorI7yTl.abfmod` is empty here, as in the Mod Editor's templates. The Mod Management Tool fills it in when you upload to your own mod.io listing. The upload's Asset Audit checks every Blueprint against the official Blueprint filter (https://cdn.abfmods.com/blueprint-filter/1.5/BlueprintFilter.txt), and the cloud cook rebuilds Blueprints without the editor-only cheat assets. That's why 52 of the built-in commands are left out. `build/commands-08.json` lists them, each with its reason.

## Layout

- `ResearchDirectorI7yTl/`: the Mod Editor project.
  - `Widgets/W_DirectorMenu` is the menu, `W_DirectorItemEntry` is one item search result, and `W_DirectorCmdEntry` is one row of the ALL tab.
  - `Blueprints/BP_DirectorRemote` is the Cheat Remote, a child of the game's `Abiotic_Item_ParentBP`. Its `UseItem_LocalFX` opens the menu. Its item row `Remote_ResearchDirector` copies the Personal Teleporter's look, and `Recipe_CheatRemote` is its recipe.
  - `Commands/` is made by the setup script (see above).
- `setup/`: `copy_game_commands.py` and `game-commands.json` (each copy's source and parent, parents first).
- `build/`: how the menu was generated.
  - `build_menu_08.py` builds the widget layouts from `menu-spec-08.json`. Run it in the editor.
  - `generate_graphs_08.py` (run with normal Python) writes the event graphs as Blueprint clipboard text: `graphs/menu-08-pass1..5.txt` for the menu and `graphs/remote-08-pass1.txt` for the remote.
  - `commands-08.json` is the ALL tab's command list (labels, descriptions, categories, inputs), and `commands-08-classes.json` maps each command to its copied class.
- `tools/`: helpers for driving the editor from outside.
  - `editor_bridge.py`: run it once in the editor (`py ".../tools/editor_bridge.py"` in the Cmd box). After that, `py tools/run.py script.py` runs scripts in the editor and prints their output.
  - `paste.py` pastes a graph file into the Blueprint graph that is open, using real clicks and keys (`win.py`; set `CM_WINDOW` to the asset editor's window title).
  - `errs.py` and `t3dpins.py` check exported graphs.
  - `give_test_items.py` gives you the Cheat Remote during Play.

## How the graphs are built

Python in this Mod Editor can't create Blueprint nodes. So the graphs are generated as clipboard text and pasted into the graph editor in passes, compiling after each one. Every custom event has to exist before anything calls it: a call to a function that doesn't exist yet is dropped without any warning.

- The ALL tab holds its command list as literal class arrays. This also makes the cooker ship every copied class.
- Option lists come from each command's own `GetFirstParamOptions` / `GetSecondParamOptions`.
- Parameters go through `ConvertParamToOriginal`, the way the game's own menu does it.
- The state line uses `GetCurrentState` / `GetCurrentValue`.
- The menu's input priority is 10 with Stop Action on, which blocks the game's own input. So the menu listens for HotbarSlot1-10, NextHotbarItem and PreviousHotbarItem itself and calls the character's `RefreshSelectedHotbarSlot`.
