# -*- coding: utf-8 -*-
# Copyright © 2022 Thales. All Rights Reserved.
# NOTICE: This file is subject to the license agreement defined in file 'LICENSE', which is part of
# this source code package.

import os
import sys
from tkinter import Tk, Canvas, NW
from PIL import Image, ImageTk

from .graphics_base import KesslerGraphics
from ..ship import Ship
from ..asteroid import Asteroid
from ..bullet import Bullet
from ..mines import Mine
from ..score import Score
from ..scenario import Scenario
from ..team import Team
from ..settings_dicts import UISettingsDict

class GraphicsTK(KesslerGraphics):
    def __init__(self, UI_settings: UISettingsDict | None = None) -> None:
        # UI settings
        # lives, accuracy, asteroids hit, shots taken, bullets left
        # default_ui = {'ships': True, 'lives_remaining': True, 'accuracy': True, 'asteroids_hit': True}
        UI_settings = {} if UI_settings is None else UI_settings
        self.show_ships = UI_settings.get('ships', True)
        self.show_lives = UI_settings.get('lives_remaining', True)
        self.show_accuracy = UI_settings.get('accuracy', True)
        self.show_asteroids_hit = UI_settings.get('asteroids_hit', True)
        self.show_shots_fired = UI_settings.get('shots_fired', False)
        self.show_bullets_remaining = UI_settings.get('bullets_remaining', True)
        self.show_mines_remaining = UI_settings.get('mines_remaining', True)
        self.show_controller_name = UI_settings.get('controller_name', True)
        self.scale = float(UI_settings.get('scale', 1.0))
        self.script_dir = os.path.dirname(__file__)
        self.img_dir = os.path.join(self.script_dir, "images")

    def sort_list(self, order: list[str], list_to_order: list[str]) -> list[str]:
        i = len(order)
        sorted_list: list[str | None] = [None] * (len(list_to_order) + (len(order)))
        for value in list_to_order:
            try:
                idx = order.index(value)
                sorted_list[idx] = value
            except ValueError:  # value not found in the list
                sorted_list[i] = value
                i = i + 1
        return [x for x in sorted_list if x != None]

    def start(self, scenario: Scenario) -> None:
        self.game_width = round(scenario.map_size[0] * self.scale)
        self.game_height = round(scenario.map_size[1] * self.scale)
        self.max_time = scenario.time_limit
        self.score_width = round(385 * self.scale)
        self.window_width = self.game_width + self.score_width
        ship_radius: int = int((scenario.ships()[0].radius * 2 - 5) * self.scale)

        # Set DPI Aware before anything else
        if sys.platform == "win32":
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(2)

        # create and center main window
        self.window = Tk()
        self.window.title('Kessler')
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        center_x = int(screen_width / 2 - self.window_width / 2)
        center_y = int(screen_height / 2 - self.game_height / 2)
        self.window.geometry(f'{self.window_width}x{self.game_height}+{center_x}+{center_y}')

        # create canvas for object and image display
        self.game_canvas = Canvas(self.window, width=self.window_width, height=self.game_height, bg="black")
        self.game_canvas.pack()
        self.window.update()

        # Grab and open sprite images in python
        default_images = ["playerShip1_green.png",
                          "playerShip1_orange.png",
                          "playerShip2_orange.png",
                          "playerShip3_orange.png"]

        img_list: list[str] = []
        for file in os.listdir(self.img_dir):
            if file.endswith(".png") or file.endswith(".jpg"):
                img_list.append(file)
        img_list2 = self.sort_list(default_images, img_list)
        self.image_paths = [os.path.join(self.img_dir, img) for img in img_list2]

        self.num_images = len(self.image_paths)
        self.ship_images = [(Image.open(image)).resize((ship_radius, ship_radius)) for image in self.image_paths]
        self.ship_sprites = [ImageTk.PhotoImage(img) for img in self.ship_images]
        self.ship_icons = [ImageTk.PhotoImage((Image.open(image)).resize((ship_radius, ship_radius))) for image in self.image_paths]

    def update(self, score: Score, ships: list[Ship], asteroids: list[Asteroid], bullets: list[Bullet], mines: list[Mine]) -> None:
        # Delete everything from canvas so we can re-plot
        self.game_canvas.delete("all")
        self._per_frame_images: list[ImageTk.PhotoImage] = []  # Keep PhotoImage references for this frame, to prevent GC

        # Plot shields, bullets, ships, and asteroids
        self.plot_shields(ships)
        self.plot_ships(ships)
        self.plot_bullets(bullets)
        self.plot_asteroids(asteroids)
        self.plot_mines(mines)

        # Update score box
        self.update_score(score, ships)

        # Push updates to graphics refresh
        self.window.update()

    def close(self) -> None:
        self.window.destroy()

    def update_score(self, score: Score, ships: list[Ship]) -> None:

        # offsets to deal with cleanliness and window borders covering data
        x_offset = round(5 * self.scale)
        y_offset = round(5 * self.scale)

        # outline and center line
        self.game_canvas.create_rectangle(
            self.game_width, 0, self.window_width, self.game_height,
            outline="white", fill="black",
        )
        self.game_canvas.create_line(
            self.window_width - self.score_width / 2, 0,
            self.window_width - self.score_width / 2, self.game_height, fill="white",
        )

        # show simulation time
        time_font_size = -round(20 * self.scale)
        time_text = "Time: " + f'{score.sim_time:.2f}' + " / " + str(self.max_time) + " sec"
        self.game_canvas.create_text(
            round(10 * self.scale), round(10 * self.scale),
            text=time_text, fill="white", font=("Courier New", time_font_size), anchor=NW
        )

        # index for loop: allows teams to be displayed in order regardless of team num skipping or strings for team name
        team_num = 0
        output_location_y = 0
        max_lines = 0

        for team in score.teams:
            # create text contents
            title = team.team_name + "\n"
            ships_text = "_________\n"

            # add each ship to text if enabled
            if self.show_ships:
                for ship in ships:
                    if ship.team == team.team_id:
                        ships_text += ("Ship " + str(ship.id))
                        if self.show_controller_name:
                            assert ship.controller is not None
                            ships_text += ": " + '\n' + str(ship.controller.name)
                        ships_text += '\n'

            team_info = self.format_ui(team)
            score_board = title + ships_text + team_info

            # determine output location based off order in team list
            if (team_num % 2) == 0:
                output_location_x = int(self.game_width + x_offset)

                # y location is based off the number of lines in the previous teams row
                output_location_y = output_location_y + (round(17 * self.scale) * max_lines) + y_offset

                # line separating team rows
                self.game_canvas.create_line(
                    self.game_width, output_location_y - round(10 * self.scale),
                    self.window_width, output_location_y - round(10 * self.scale), fill="white"
                )
                max_lines = score_board.count("\n")
            else:
                output_location_x = int(self.window_width + x_offset - self.score_width / 2)

                # change max lines in the row if odd team has more lines then even
                if score_board.count("\n") > max_lines:
                    max_lines = score_board.count("\n")

            # display of team information
            team_font_size = -round(16 * self.scale)
            self.game_canvas.create_text(
                output_location_x, output_location_y,
                text=score_board, fill="white", font=("Courier New", team_font_size), anchor=NW
            )
            icon_idx = team.team_id-1
            for ship in ships:
                if ship.custom_sprite_path and ship.team == team.team_id:
                    icon_idx = self.image_paths.index(os.path.join(self.img_dir, ship.custom_sprite_path))
            self.game_canvas.create_image(
                output_location_x + round(120 * self.scale),
                output_location_y + round(15 * self.scale),
                image=self.ship_icons[icon_idx % self.num_images]
            )
            team_num += 1

    def format_ui(self, team: Team) -> str:
        # lives, accuracy, asteroids hit, shots taken, bullets left
        team_info = "_________\n"
        if self.show_lives:
            team_info += "Lives: " + str(team.lives_remaining) + "\n"
        if self.show_accuracy:
            team_info += "Accuracy: " + str(round(team.accuracy * 100, 1)) + "\n"
        if self.show_asteroids_hit:
            team_info += "Asteroids Hit: " + str(team.asteroids_hit) + "\n"
        if self.show_shots_fired:
            team_info += "Shots Fired: " + str(team.shots_fired) + "\n"
        if self.show_bullets_remaining:
            team_info += "Bullets Left: " + str(team.bullets_remaining) + "\n"
        if self.show_mines_remaining:
            team_info += "Mines Left: " + str(team.mines_remaining) + "\n"

        return team_info

    def plot_ships(self, ships: list[Ship]) -> None:
        """
        Plots each ship on the game screen using cached sprites and rotating them
        """
        ship_id_font_size = -round(15 * self.scale)
        for idx, ship in enumerate(ships):
            if ship.alive:
                # plot ship image and id text next to it
                if ship.custom_sprite_path:
                    sprite_idx = self.image_paths.index(os.path.join(self.img_dir, ship.custom_sprite_path))
                else:
                    sprite_idx = idx % self.num_images
                rotated_ship_sprite = ImageTk.PhotoImage(self.ship_images[sprite_idx].rotate(180 - (-ship.heading - 90)))
                self._per_frame_images.append(rotated_ship_sprite)  # Storing a reference to this image will prevent Python from garbage collecting it
                self.game_canvas.create_image(
                    ship.position[0] * self.scale,
                    self.game_height - ship.position[1] * self.scale,
                    image=rotated_ship_sprite
                )
                self.game_canvas.create_text(
                    (ship.position[0] + ship.radius) * self.scale,
                    self.game_height - ((ship.position[1] + ship.radius) * self.scale),
                    text=str(ship.id),
                    fill="white",
                    font=("Courier New", ship_id_font_size)
                )

    def plot_shields(self, ships: list[Ship]) -> None:
        """
        Plots each ship's shield ring
        """
        for ship in ships:
            if ship.alive:
                # Color shield based on respawn time remaining
                full_invincibility_duration = 3.0  # For compatibility with mainline
                respawn_scaler = max(min(ship.respawn_time_left / full_invincibility_duration, 1.0), 0.0)
                r = int(120 + (respawn_scaler * (255 - 120)))
                g = int(200 + (respawn_scaler * (0 - 200)))
                b = int(255 + (respawn_scaler * (0 - 255)))
                color = "#%02x%02x%02x" % (r, g, b)
                # Plot shield ring
                self.game_canvas.create_oval(
                    (ship.position[0] - ship.radius) * self.scale,
                    self.game_height - (ship.position[1] + ship.radius) * self.scale,
                    (ship.position[0] + ship.radius) * self.scale,
                    self.game_height - (ship.position[1] - ship.radius) * self.scale,
                    fill="black", outline=color
                )

    def plot_bullets(self, bullets: list[Bullet]) -> None:
        """
        Plots each bullet object on the game screen
        """
        for bullet in bullets:
            self.game_canvas.create_line(
                bullet.position[0] * self.scale,
                self.game_height - bullet.position[1] * self.scale,
                bullet.tail[0] * self.scale,
                self.game_height - bullet.tail[1] * self.scale,
                fill="#EE2737", width=round(3 * self.scale)
            )

    def plot_asteroids(self, asteroids: list[Asteroid]) -> None:
        """
        Plots each asteroid object on the game screen
        """
        for asteroid in asteroids:
            self.game_canvas.create_oval(
                (asteroid.position[0] - asteroid.radius) * self.scale,
                self.game_height - (asteroid.position[1] + asteroid.radius) * self.scale,
                (asteroid.position[0] + asteroid.radius) * self.scale,
                self.game_height - (asteroid.position[1] - asteroid.radius) * self.scale,
                fill="grey"
            )

    def plot_mines(self, mines: list[Mine]) -> None:
        """
        Plots and animates each mine object on the game screen and their detonations
        """
        for mine in mines:
            self.game_canvas.create_oval(
                (mine.position[0] - mine.radius) * self.scale,
                self.game_height - (mine.position[1] + mine.radius) * self.scale,
                (mine.position[0] + mine.radius) * self.scale,
                self.game_height - (mine.position[1] - mine.radius) * self.scale,
                fill="yellow"
            )

            light_fill = "red" if mine.countdown_timer - int(mine.countdown_timer) > 0.5 else "orange"
            self.game_canvas.create_oval(
                (mine.position[0] - mine.radius * 0.3) * self.scale,
                self.game_height - (mine.position[1] + mine.radius * 0.3) * self.scale,
                (mine.position[0] + mine.radius * 0.3) * self.scale,
                self.game_height - (mine.position[1] - mine.radius * 0.3) * self.scale,
                fill=light_fill
            )

            # Detonations
            if mine.countdown_timer < mine.detonation_time:
                explosion_radius = mine.blast_radius * (1 - mine.countdown_timer / mine.detonation_time) ** 2
                self.game_canvas.create_oval(
                    (mine.position[0] - explosion_radius) * self.scale,
                    self.game_height - (mine.position[1] + explosion_radius) * self.scale,
                    (mine.position[0] + explosion_radius) * self.scale,
                    self.game_height - (mine.position[1] - explosion_radius) * self.scale,
                    # fill="#fa441b",
                    fill="", outline="white", width=round(10 * self.scale)
                )
