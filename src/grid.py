from math import floor
import pygame
import pyartnet

class Grid:
    def __init__(self, grid_size, cell_size=4, cell_space=24):
        self.grid_size = grid_size
        self.cell_size = cell_size
        self.cell_space = cell_space
        self.reset()

    def reset(self):
        self.grid = [[pygame.Color(0, 0, 0, 255) for x in range(self.grid_size)] for y in range(self.grid_size)]

    def set_color(self, x, y, color):
        self.grid[floor(x)][floor(y)] = color

    def update_screen(self, screen: pygame.Surface):
        for x in range(self.grid_size):
            for y in range(self.grid_size):
                # pygame.draw.rect(screen, self.grid[x][y], (x * self.cell_space, y * self.cell_space, self.cell_size, self.cell_size))
                pygame.draw.circle(screen, self.grid[x][y], (x * self.cell_space + self.cell_space / 2, y * self.cell_space + self.cell_space / 2), self.cell_size / 2)

    async def update_artnet(self, channels: 'list[pyartnet.Channel]'):
        # print("update_artnet")
        # 4 channels, each for 64 pixels
        # zig-zag
        values = [[] for i in range(4)] # type: list[list[int]]
        for channel in range(4):
            y_offset = (3 - channel) * 4
            for y in range(3 + y_offset, y_offset - 1, -1):
                if y % 2 == 0:
                    for x in range(self.grid_size):
                        values[channel].append(self.grid[x][y].r)
                        values[channel].append(self.grid[x][y].g)
                        values[channel].append(self.grid[x][y].b)
                else:
                    for x in range(self.grid_size - 1, -1, -1):
                        values[channel].append(self.grid[x][y].r)
                        values[channel].append(self.grid[x][y].g)
                        values[channel].append(self.grid[x][y].b)

        for i in range(len(channels)):
            channels[i].set_values(values[i])