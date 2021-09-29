from typing import TYPE_CHECKING

import tcod

from UI import color
from engine import Engine

if TYPE_CHECKING:
    from Entities.Components.skill import FS_CONNECTORS_LIST, BS_CONNECTORS_LIST


def draw_skill(console, engine: Engine, y_offset, skill, selected=False):
    col = skill.unlocked_color
    if not engine.player.skill_with_name(skill.name):
        # player does not have skill
        if skill.unlockable(engine.player):
            # skill is unlockable
            col = skill.color
        else:
            col = color.unselected_skill

    # if selected:
    #    col=color.selected_skill

    if selected:
        console.draw_frame(
            skill.x - 1, skill.y + y_offset - 1, 7, 7, fg=color.selected_skill
        )
    console.draw_frame(
        skill.x, skill.y + y_offset, 5, 5, fg=col
    )
    # 9 chars per skill
    for i, line in enumerate(skill.char_string.split(":")):
        console.print(
            skill.x + 1, skill.y + y_offset + 1 + 1 * i, line, fg=col
        )


def render_skills(console: tcod.Console, engine: Engine, y_offset, selected_skill_index):
    from Entities.Components.skill import FS_CONNECTORS_LIST, BS_CONNECTORS_LIST, VS_CONNECTORS_LIST
    player = engine.player
    BOTTOM_BOX_HEIGHT = 15
    y_offset = -y_offset
    for i, skill in enumerate(engine.skills_list):
        if skill.y + y_offset + 2 > -4:
            draw_skill(console, engine, y_offset + 2, skill, selected_skill_index == i)

    for pos in VS_CONNECTORS_LIST:
        if pos[1] + y_offset + 1 > -4:
            console.print(
                pos[0], pos[1] + y_offset + 1, "|", fg=color.unselected_skill
            )

    for pos in FS_CONNECTORS_LIST:
        if pos[1] + y_offset + 1 > -4:
            console.print(
                pos[0], pos[1] + y_offset + 1, "/", fg=color.unselected_skill
            )

    for pos in BS_CONNECTORS_LIST:
        if pos[1] + y_offset + 1 > -4:
            console.print(
                pos[0], pos[1] + y_offset + 1, "\\", fg=color.unselected_skill
            )

    console.draw_frame(
        0, console.height - BOTTOM_BOX_HEIGHT, console.width, BOTTOM_BOX_HEIGHT, fg=color.selected_skill
    )
    console.print_box(
        0, console.height - BOTTOM_BOX_HEIGHT, console.width, 1, f"┤{engine.skills_list[selected_skill_index].name}├",
        alignment=tcod.CENTER
    )
    lvl = 0
    max_lvl = engine.skills_list[selected_skill_index].max_level
    skill = engine.player.skill_with_name(engine.skills_list[selected_skill_index].name)
    if skill is not False:
        lvl = skill.level
    if lvl > 0:
        console.print(
            2, console.height - BOTTOM_BOX_HEIGHT + 3, f"Points Invested: {lvl}", fg=color.selected_skill
        )

    if skill is not False:
        console.print(
            2, console.height - BOTTOM_BOX_HEIGHT + 2, f"Energy Cost: {skill.cost}",
            fg=color.selected_skill
        )
    else:
        console.print(
            2, console.height - BOTTOM_BOX_HEIGHT + 2, f"Energy Cost: {engine.skills_list[selected_skill_index].cost}",
            fg=color.selected_skill
        )
    if lvl > 0:
        console.print(
            2, console.height - BOTTOM_BOX_HEIGHT + 3, f"Points Invested: {lvl}/{max_lvl}", fg=color.selected_skill
        )
    points = engine.player.skill_points
    col = color.skill_points
    if points < 1:
        col = color.unselected_skill
    console.print(
        2, console.height - BOTTOM_BOX_HEIGHT - 2, f"Skill Points Remaining: {points}", fg=col
    )
    console.print(
        2, console.height - 3, f"(Esc) Back", fg=color.selected_skill
    )
    console.draw_rect(30, console.height - BOTTOM_BOX_HEIGHT + 1, 1, BOTTOM_BOX_HEIGHT - 2, ord('|'))

    if skill is not False:
        skill.render_description(32, console.height - BOTTOM_BOX_HEIGHT + 2, 46,
                                                                    BOTTOM_BOX_HEIGHT - 2, console,engine)
    else:
        engine.skills_list[selected_skill_index].render_description(32, console.height - BOTTOM_BOX_HEIGHT+2,46,
                                                                    BOTTOM_BOX_HEIGHT-2,console,engine)
