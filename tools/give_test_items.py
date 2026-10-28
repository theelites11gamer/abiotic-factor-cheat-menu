"""Gives the Cheat Remote to the player in a running Play session.
In the Mod Editor, start Play, wait until you are in the world, then type into the Cmd box at the bottom of the editor:
    py "<this repo>/tools/give_test_items.py"
It opens the cheat menu, uses its own ADD TO INVENTORY button, then closes it again.
"""
import unreal

worlds = unreal.EditorLevelLibrary.get_pie_worlds(False)
if not worlds:
    unreal.log_warning('give_test_items: start Play first (green Play button), then run this again.')
else:
    world = worlds[0]
    pc = unreal.GameplayStatics.get_player_controller(world, 0)
    menu_class = unreal.load_class(None, '/ResearchDirectorI7yTl/Widgets/W_DirectorMenu.W_DirectorMenu_C')
    menus = unreal.WidgetLibrary.get_all_widgets_of_class(world, menu_class, True)
    if menus:
        menu = menus[0]
    else:
        menu = unreal.new_object(menu_class, outer=pc)
        menu.set_owning_player(pc)
        menu.add_to_viewport(100)
    menu.get_editor_property('SelectedItemId').set_text('NRHS8_Remote_ResearchDirector')
    menu.get_editor_property('SelectedItemName').set_text('Cheat Remote')
    menu.get_editor_property('ItemQty').set_text('1')
    menu.get_editor_property('I_Give').on_clicked.broadcast()
    menu.get_editor_property('CloseButton').on_clicked.broadcast()
    unreal.log('give_test_items: gave the Cheat Remote')
    print('GAVE_TEST_ITEMS')
