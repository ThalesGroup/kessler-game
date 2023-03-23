# -*- coding: utf-8 -*-
# Copyright © 2022 Thales. All Rights Reserved.
# NOTICE: This file is subject to the license agreement defined in file 'LICENSE', which is part of
# this source code package.

import os
from tkinter import *
from PIL import Image, ImageTk

from .graphics_base import KesslerGraphics


class GraphicsTK(KesslerGraphics):
    def __init__(self, UI_settings):
        # UI settings
        # lives, accuracy, asteroids hit, shots taken, bullets left
        # default_ui = {'ships': True, 'lives_remaining': True, 'accuracy': True, 'asteroids_hit': True}
        UI_settings = {} if UI_settings is None else UI_settings
        self.show_ships = UI_settings.get('ships', True)
        self.show_lives = UI_settings.get('lives_remaining', True)
        self.show_accuracy = UI_settings.get('accuracy', True)
        self.show_asteroids_hit = UI_settings.get('asteroids_hit', True)
        self.show_shots_fired = UI_settings.get('shots_fired', False)
        self.show_bullets_remaining = UI_settings.get('bullets_remaining', False)
        self.show_controller_name = UI_settings.get('controller_name', True)

    def start(self, scenario):
        self.game_width = scenario.map_size[0]
        self.height = scenario.map_size[1]
        self.max_time = scenario.time_limit
        self.score_width = 385
        self.window_width = self.game_width + self.score_width
        ship_radius = scenario.ships()[0].radius * 2 - 5

        # create and center main window
        self.window = Tk()
        self.window.title('Kessler')
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        center_x = int(screen_width / 2 - self.window_width / 2)
        center_y = int(screen_height / 2 - self.height / 2)
        self.window.geometry(f'{self.window_width}x{self.height}+{center_x}+{center_y}')

        # create canvas for object and image display
        self.canvas = Canvas(self.window, width=self.window_width, height=self.height, bg="black")
        self.canvas.pack()
        self.window.update()

        # grab and open images
        script_dir = os.path.dirname(__file__)
        self.images = ["images/playerShip1_green.png",
                       "images/playerShip1_orange.png",
                       "images/playerShip2_orange.png",
                       "images/playerShip3_orange.png"]
        self.num_images = len(self.images)
        self.ship_images = [(Image.open(os.path.join(script_dir, image))).resize((ship_radius, ship_radius)) for image in self.images]
        self.team_images = [ImageTk.PhotoImage(img) for img in self.ship_images]

    def update(self, score, ships, asteroids, bullets):
        # reset canvas
        self.canvas.delete("all")

        # initialize image list
        current_images = []

        # plot ships
        for ship in ships:
            current_images.append(ImageTk.PhotoImage(self.ship_images[(ship.team-1) % self.num_images].rotate(180-(-ship.heading - 90))))
            if ship.alive:

                # use respawn time to determine color of ring, ring shows ship radius
                temp_time = ship.respawn_time_left
                if temp_time > 1:
                    temp_time = 1
                elif temp_time < 0:
                    temp_time = 0

                r = int(120 + (temp_time * (255 - 120)))
                g = int(200 + (temp_time * (0 - 200)))
                b = int(255 + (temp_time * (0 - 255)))
                color = "#%02x%02x%02x" % (r, g, b)

                # plot ring
                self.canvas.create_oval(ship.position[0] - ship.radius, self.height - (ship.position[1] + ship.radius),
                                        ship.position[0] + ship.radius, self.height - (ship.position[1] - ship.radius),
                                        fill="black", outline=color)

                # plot image and ship number text
                self.canvas.create_image(ship.position[0], self.height - ship.position[1], image=current_images[ship.id-1])
                self.canvas.create_text(ship.position[0] + ship.radius, self.height - (ship.position[1] + ship.radius), text=str(ship.id), fill='white')

        # plot bullets
        for bullet in bullets:
            self.canvas.create_line(bullet.position[0], self.height - bullet.position[1],
                                    bullet.tail[0], self.height - bullet.tail[1],
                                    fill="red")

        # plot asteroids
        # create_oval(x0,y0,x1,y1) where (x0,y0) is the top left corner of the object and (x1,y1) is the bottom right
        for asteroid in asteroids:
            self.canvas.create_oval(asteroid.position[0]-asteroid.radius, self.height - (asteroid.position[1] + asteroid.radius),
                                    asteroid.position[0] + asteroid.radius, self.height - (asteroid.position[1] - asteroid.radius),
                                    fill="grey")

        self.update_score(score, ships)
        self.window.update()

    def close(self):
        self.window.destroy()

    def update_score(self, score, ships):

        # offsets to deal with cleanliness and window borders covering data
        x_offset = 5
        y_offset = 5

        # outline and center line
        self.canvas.create_rectangle(self.game_width, 0, self.window_width, self.height, outline="white", fill="black",)
        self.canvas.create_line(self.window_width - self.score_width / 2, 0,
                                self.window_width - self.score_width / 2, self.height, fill="white")

        # show simulation time
        time_text = "Time: " + f'{score.sim_time:.2f}' + " / " + str(self.max_time) + " sec"
        self.canvas.create_text(10, 10, text=time_text, fill="white", font=("Courier New", 10), anchor=NW)

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
                            ships_text += ": " + str(ship.controller.name)
                        ships_text += '\n'

            team_info = self.format_ui(team)
            score_board = title + ships_text + team_info

            # determine output location based off order in team list
            if (team_num % 2) == 0:
                output_location_x = self.game_width + x_offset

                # y location is based off the number of lines in the previous teams row
                output_location_y = output_location_y + (17 * max_lines) + y_offset

                # line separating team rows
                self.canvas.create_line(self.game_width, output_location_y - 10, self.window_width, output_location_y - 10, fill="white")
                max_lines = score_board.count("\n")
            else:
                output_location_x = self.window_width + x_offset - self.score_width / 2

                # change max lines in the row if odd team has more lines then even
                if score_board.count("\n") > max_lines:
                    max_lines = score_board.count("\n")

            # display of team information
            self.canvas.create_text(output_location_x, output_location_y,
                                    text=score_board, fill="white", font=("Courier New", 10), anchor=NW, )

            self.canvas.create_image(output_location_x + 120, output_location_y + 15,
                                     image=self.team_images[(team.team_id-1) % self.num_images])
            team_num += 1

    def format_ui(self, team):
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

        return team_info
