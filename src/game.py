import asyncio
from decimal import Clamped
from math import ceil, floor
import pygame
import random
from src.grid import Grid
from perlin_noise import PerlinNoise

def timer_function(progress):
    # progress is a value between 0 and 1
    # 200 to 100, quadratic, max speed at 0.2
    progress = max(0, min(1, progress * 5))
    print(progress, round(200 - 100 * progress ** 0.7))
    return round(200 - 100 * progress ** 0.7)

def get_star_opacity(noise: PerlinNoise, x, y, time):
    return (noise([x, y, time / 2]) + 1) / 2

star_fade_duration = 1000
apple_color = pygame.Color(255, 0, 0)
trail_color = pygame.Color(1, 0, 1)

def get_star_fade_opacity(time):
    diff = abs(time - star_fade_duration / 2) / (star_fade_duration / 2)

    return max(min((diff ** 0.7) * 2.5 - 1.5, 1), 0)

class Game:
    def __init__(self, grid_size):
        self.screen = pygame.display.set_mode((800, 600))
        self.running = True
        self.state = 'waiting' # waiting: before start, with stars / running: game running / dead: game over, star transtion with increasing circle effect from died position / 
        self.died_position = pygame.Vector2(0, 0)
        self.die_radius = 0
        self.die_transition = 0
        self.die_phase = 0
        self.prev_snake_history = []
        self.snake_history = []
        self.grid_size = grid_size
        self.grid = Grid(grid_size)
        self.stars = {}
        self.prev_stars = {}
        self.noise = PerlinNoise()
        # test stars
        # for x in range(0, grid_size):
        #     self.stars[x] = {}
        #     for y in range(0, grid_size):
        #         self.stars[x][y] = max(random.randint(-10, 10), 0)

    def show_dead_effect(self):
        self.dead_position = self.snake_head.copy()
        self.state = 'dead'
        self.die_radius = 0
        self.die_transition = 0
        self.die_phase = 0
        pygame.time.set_timer(pygame.USEREVENT, 100)

    def new_game(self): # transition to dead -> running
        self.state = 'running'
        self.prev_snake_history = self.snake_history.copy()
        self.snake_history = []
        self.snake_head = pygame.Vector2(self.grid_size // 2, self.grid_size // 2)
        self.snake = [self.snake_head.copy()]
        self.movement = pygame.Vector2(1, 0)
        self.movement_queue = []
        self.last_key = pygame.K_0
        self.apple = pygame.Vector2(0, 0)
        self.new_apple()

    async def run(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.USEREVENT:
                    if self.state == 'dead':
                        if self.die_phase == 0:
                            self.die_radius += 1
                            if self.die_radius > self.grid_size * 1.5:
                                self.die_phase = 1
                                self.die_transition = pygame.time.get_ticks()
                    elif self.state == 'running':
                        if len(self.movement_queue) > 0:
                            new_movement = self.movement_queue.pop(0)
                            if new_movement.x != 0 or new_movement.y != 0:
                                if len(self.snake) == 1 or (new_movement.x != -self.movement.x and new_movement.y != -self.movement.y):
                                    self.movement = new_movement

                        self.snake_head += self.movement
                        if self.snake_head.x == -1 or self.snake_head.x == self.grid_size or self.snake_head.y == -1 or self.snake_head.y == self.  grid_size or self.snake_head in self.snake:
                            self.snake_head -= self.movement
                            self.game_over()

                        if self.snake_head == self.apple:
                            self.new_apple()
                        else:
                            self.snake.pop(0)

                        self.snake.append(self.snake_head.copy())
                        self.snake_history[len(self.snake) - 1].append(self.snake_head.copy())
                    self.update_grid()
                if event.type == pygame.QUIT:
                    self.running = False
                if event.type == pygame.KEYDOWN:
                    new_movement = pygame.Vector2(0, 0)
                    if event.key == pygame.K_UP:
                        new_movement = pygame.Vector2(0, -1)
                    elif event.key == pygame.K_DOWN:
                        new_movement = pygame.Vector2(0, 1)
                    elif event.key == pygame.K_LEFT:
                        new_movement = pygame.Vector2(-1, 0)
                    elif event.key == pygame.K_RIGHT:
                        new_movement = pygame.Vector2(1, 0)
                    if self.state == 'waiting':
                        self.new_game()
                        if new_movement != pygame.Vector2(0, 0):
                            self.movement = new_movement
                    elif self.state == 'running' and new_movement != pygame.Vector2(0, 0):
                        self.movement_queue.append(new_movement)

            if self.state == 'dead' and self.die_phase == 1:
                diff = pygame.time.get_ticks() - self.die_transition
                if diff > star_fade_duration:
                    self.prev_stars = self.stars.copy()
                    self.state = 'waiting'
            self.update_grid()
            self.screen.fill((10, 10, 10))
            self.grid.update_screen(self.screen)
            pygame.display.flip()
            await asyncio.sleep(1 / 120)
        
        pygame.quit()

    def new_apple(self):
        # randomize apple position
        apple = pygame.Vector2(random.randint(0, self.grid_size - 1), random.randint(0, self.grid_size - 1))
        while apple in self.snake:
            apple = pygame.Vector2(random.randint(0, self.grid_size - 1), random.randint(0, self.grid_size - 1))
        self.apple = apple

        if len(self.snake_history) > 0 and len(self.snake_history) <= len(self.prev_snake_history):
            cur_trail = self.snake_history[len(self.snake_history) - 1]
            prev_trail = self.prev_snake_history[len(self.snake_history) - 1]
            for p in cur_trail:
                if p in prev_trail:
                    if p.x in self.stars:
                        if p.y in self.stars[p.x]:
                            self.stars[p.x][p.y] += 1
                        else:
                            self.stars[p.x][p.y] = 1
                    else:
                        self.stars[p.x] = {}
                        self.stars[p.x][p.y] = 1
                    break
        
        pygame.time.set_timer(pygame.USEREVENT, timer_function(len(self.snake) / (self.grid_size * self.grid_size)))
        self.snake_history.append([])

    def update_grid(self):
        self.grid.reset()

        if self.state == 'dead':
            if self.die_phase == 0:
                # draw snake, and stars in circle

                # snake
            
                if len(self.snake) > 0 and len(self.snake) < len(self.prev_snake_history):
                    for pos in self.prev_snake_history[len(self.snake) - 1]:
                        self.grid.set_color(pos.x, pos.y, trail_color)
                    for pos in self.snake_history[len(self.snake) - 1]:
                        self.grid.set_color(pos.x, pos.y, trail_color)

                for pos in self.snake:
                    self.grid.set_color(pos.x, pos.y, pygame.Color(255, 255, 255))

                self.grid.set_color(self.apple.x, self.apple.y, apple_color)

                # emptify inner
                
                for x in range(self.grid_size):
                    for y in range(self.grid_size):
                        p = pygame.Vector2(x, y)
                        distance = (p - self.snake_head).length()
                        if distance < self.die_radius:
                            self.grid.set_color(x, y, pygame.Color(0, 0, 0))
                # stars

                for x in self.prev_stars:
                    for y in self.prev_stars[x]:
                        p = pygame.Vector2(x, y)
                        # radius check
                        if (p - self.snake_head).length_squared() > self.die_radius * self.die_radius:
                            continue
                        intensity = self.prev_stars[x][y]
                        star_color = pygame.Color(0, 0, 0)
                        if intensity <= 3:
                            v = 1 if intensity == 1 else (7 if intensity == 2 else 255)
                            star_color = pygame.Color(v, v, 0)
                        elif intensity <= 6:
                            v = max(min((intensity - 4) / 3, 1), 0)
                            star_color = pygame.Color(255, 255, floor(v * 255))
                        elif intensity <= 8:
                            v = max(min((intensity - 7) / 2, 1), 0)
                            star_color = pygame.Color(floor((1 - v) * 255), floor((1 - v) * 255), 255)
                        else:
                            star_color = pygame.Color(0, 0, 255)
                        star_opacity = get_star_opacity(self.noise, x, y, pygame.time.get_ticks() / 1000)
                        star_color.r = ceil(star_color.r * star_opacity)
                        star_color.g = ceil(star_color.g * star_opacity)
                        star_color.b = ceil(star_color.b * star_opacity)
                        self.grid.set_color(p.x, p.y, star_color)

                # draw circle
                for x in range(self.grid_size):
                    for y in range(self.grid_size):
                        p = pygame.Vector2(x, y)
                        distance = (p - self.snake_head).length()
                        if abs(distance - self.die_radius) < .5:
                            self.grid.set_color(x, y, pygame.Color(255, 0, 0))
            elif self.die_phase == 1:
                # transition from prev_star to cur_star
                diff = pygame.time.get_ticks() - self.die_transition
                opacity = max(min(abs(diff - star_fade_duration / 2) / (star_fade_duration / 2), 1), 0)
                if diff < star_fade_duration / 2:
                    # prev_star
                    for x in self.prev_stars:
                        for y in self.prev_stars[x]:
                            p = pygame.Vector2(x, y)
                            # radius check
                            if (p - self.snake_head).length_squared() > self.die_radius * self.die_radius:
                                continue
                            intensity = self.prev_stars[x][y]
                            star_color = pygame.Color(0, 0, 0)
                            if intensity <= 3:
                                v = 1 if intensity == 1 else (7 if intensity == 2 else 255)
                                star_color = pygame.Color(v, v, 0)
                            elif intensity <= 6:
                                v = max(min((intensity - 4) / 3, 1), 0)
                                star_color = pygame.Color(255, 255, floor(v * 255))
                            elif intensity <= 8:
                                v = max(min((intensity - 7) / 2, 1), 0)
                                star_color = pygame.Color(floor((1 - v) * 255), floor((1 - v) * 255), 255)
                            else:
                                star_color = pygame.Color(0, 0, 255)
                            # apply opacity
                            star_opacity = get_star_opacity(self.noise, x, y, pygame.time.get_ticks() / 1000) * opacity
                            star_color.r = ceil(star_color.r * star_opacity)
                            star_color.g = ceil(star_color.g * star_opacity)
                            star_color.b = ceil(star_color.b * star_opacity)
                            self.grid.set_color(p.x, p.y, star_color)
                else:
                    for x in self.stars:
                        for y in self.stars[x]:
                            p = pygame.Vector2(x, y)
                            # radius check
                            if (p - self.snake_head).length_squared() > self.die_radius * self.die_radius:
                                continue
                            intensity = self.stars[x][y]
                            star_color = pygame.Color(0, 0, 0)
                            if intensity <= 3:
                                v = 1 if intensity == 1 else (7 if intensity == 2 else 255)
                                star_color = pygame.Color(v, v, 0)
                            elif intensity <= 6:
                                v = max(min((intensity - 4) / 3, 1), 0)
                                star_color = pygame.Color(255, 255, floor(v * 255))
                            elif intensity <= 8:
                                v = max(min((intensity - 7) / 2, 1), 0)
                                star_color = pygame.Color(floor((1 - v) * 255), floor((1 - v) * 255), 255)
                            else:
                                star_color = pygame.Color(0, 0, 255)
                            # apply opacity
                            star_opacity = get_star_opacity(self.noise, x, y, pygame.time.get_ticks() / 1000) * opacity
                            star_color.r = ceil(star_color.r * star_opacity)
                            star_color.g = ceil(star_color.g * star_opacity)
                            star_color.b = ceil(star_color.b * star_opacity)
                            self.grid.set_color(p.x, p.y, star_color)
        elif self.state == 'running':
            # only snakes
            if len(self.snake) > 0 and len(self.snake) < len(self.prev_snake_history):
                for pos in self.prev_snake_history[len(self.snake) - 1]:
                    self.grid.set_color(pos.x, pos.y, trail_color)
                for pos in self.snake_history[len(self.snake) - 1]:
                    self.grid.set_color(pos.x, pos.y, trail_color)

            for pos in self.snake:
                self.grid.set_color(pos.x, pos.y, pygame.Color(255, 255, 255))

            self.grid.set_color(self.apple.x, self.apple.y, apple_color)
        elif self.state == 'waiting':
            # only stars

            for x in self.stars:
                for y in self.stars[x]:
                    p = pygame.Vector2(x, y)
                    intensity = self.stars[x][y]
                    star_color = pygame.Color(0, 0, 0)
                    if intensity <= 3:
                        v = 1 if intensity == 1 else (7 if intensity == 2 else 255)
                        star_color = pygame.Color(v, v, 0)
                    elif intensity <= 6:
                        v = max(min((intensity - 4) / 3, 1), 0)
                        star_color = pygame.Color(255, 255, floor(v * 255))
                    elif intensity <= 8:
                        v = max(min((intensity - 7) / 2, 1), 0)
                        star_color = pygame.Color(floor((1 - v) * 255), floor((1 - v) * 255), 255)
                    else:
                        star_color = pygame.Color(0, 0, 255)
                    star_opacity = get_star_opacity(self.noise, x, y, pygame.time.get_ticks() / 1000)
                    star_color.r = ceil(star_color.r * star_opacity)
                    star_color.g = ceil(star_color.g * star_opacity)
                    star_color.b = ceil(star_color.b * star_opacity)
                    self.grid.set_color(p.x, p.y, star_color)

    def game_over(self):
        self.show_dead_effect()