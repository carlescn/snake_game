""" An implementation of the Snake game using Pygame and NumPy arrays """

import sys
import random

import pygame
import numpy as np

import sprites

UP    = np.array(( 0, -1))
DOWN  = np.array(( 0,  1))
LEFT  = np.array((-1,  0))
RIGHT = np.array(( 1,  0))

# BEGIN Customize some game parameters:
## Graphics
CELL_WIDTH    =  6    # Width  of one "fake pixel", in actual pixels
CELL_HEIGHT   =  8    # Height of one "fake pixel", in actual pixels
BORDER_WIDTH  =  1    # Size of the empty space between cells, in actual pixels
GRID_WIDTH    = 20    # Width  of the screen, in sprites (see below)
GRID_HEIGHT   =  9    # Height of the screen, in sprites (see below)
SCREEN_BORDER =  6    # Size of borders at the edge of the screen, in cells
BG_COLOR      = pygame.Color((175, 215, 5))    # Color of the background
CELL_COLOR    = pygame.Color(( 35,  43, 1))    # Color of the "fake pixels"

## Starting position
START_X         = GRID_WIDTH//2     # Starting X position
START_Y         = GRID_HEIGHT//2    # Starting Y position
START_LENGTH    = 4                 # Starting size
START_DIRECTION = RIGHT             # Starting direction

## Difficulty
GAME_SPEED   = 200    # Milliseconds between game cycles
# END Customize


# BETTER DON'T TOUCH THIS!! (it *should* work with different sized sprites in sprites.py)
SPRITE_SIZE  =  4    # Hight and width of the game sprites, in cells (see above)
HUD_SPRITE_W =  4    # Width  of the HUD numbers sprites, in cells (see above)
HUD_SPRITE_H =  5    # Height of the HUD numbers sprites, in cells (see above)
HUD_BAR      =  3 + HUD_SPRITE_H    # Height of the HUD top bar, in cells (see above)


LEVEL_WIDTH  = GRID_WIDTH  * SPRITE_SIZE
LEVEL_HEIGHT = GRID_HEIGHT * SPRITE_SIZE


def check_sprites_size(sprites_list, height, width):
    for sprite in sprites_list:
        assert np.array(sprite).shape[0] == height
        assert np.array(sprite).shape[1] == width


class Cell:
    def __init__(self, rect_x, rect_y):
        rect_width  = CELL_WIDTH  - BORDER_WIDTH
        rect_height = CELL_HEIGHT - BORDER_WIDTH
        rect_x = rect_x * CELL_WIDTH  + BORDER_WIDTH
        rect_y = rect_y * CELL_HEIGHT + BORDER_WIDTH
        self.rect = pygame.Rect(rect_x, rect_y, rect_width, rect_height)

    def draw(self):
        pygame.draw.rect(screen, CELL_COLOR, self.rect)


class Sprite:
    """ position: np.array(x:int, y:int) """
    def __init__(self, sprite, position, direction = RIGHT):
        self.position = position
        self.original_sprite = sprite
        self.sprite = None
        self.face(direction)

    def face(self, direction):
        if (direction == RIGHT).all():
            self.sprite = np.array(self.original_sprite)
        elif (direction == UP).all():
            self.sprite = np.rot90(self.original_sprite)
        elif (direction == LEFT).all():
            self.sprite = np.rot90(self.original_sprite,2)
        elif (direction == DOWN).all():
            self.sprite = np.rot90(self.original_sprite,3)

    def flip_h(self):
        self.sprite = np.fliplr(self.sprite)

    def flip_v(self):
        self.sprite = np.flipud(self.sprite)

    def draw(self, hud = False):
        cell_positions = [
            np.array((i, j)) for j, col in enumerate(self.sprite) for i, xy in enumerate(col) if xy
        ]
        sprite_x = self.position[0] * (HUD_SPRITE_W if hud else SPRITE_SIZE)
        sprite_y = self.position[1] * (HUD_SPRITE_H if hud else SPRITE_SIZE)
        for cell_x, cell_y in cell_positions:
            cell_x += sprite_x + SCREEN_BORDER + (-2 if hud else 0)
            cell_y += sprite_y + SCREEN_BORDER + (-2 if hud else HUD_BAR)
            Cell(cell_x, cell_y).draw()


class Food:
    def __init__(self):
        self.position = None
        self.move()

    def move(self):
    # pylint:disable=invalid-name  # doesn't like single letter x, y
        x = random.randint(0, GRID_WIDTH - 1)
        y = random.randint(0, GRID_HEIGHT - 1)
        self.position = np.array((x, y))

    def draw(self):
        Sprite(sprites.food, self.position).draw()


class Snake:
    def __init__(self):
        start_position = np.array((START_X, START_Y))
        positions = [start_position - START_DIRECTION * i for i in np.arange(START_LENGTH)]
        directions = [START_DIRECTION,] * START_LENGTH
        full = [False,] * START_LENGTH
        self.sections = [
            {"position": p, "direction": d, "full": f}
            for p, d, f in zip(positions, directions, full)
            ]
        self.direction = START_DIRECTION
        self.mouth_open = False

    def move(self):
        if self.sections[-1]["full"]:
            self.sections[-1]["full"] = False
        else:
            self.sections.pop(-1)

        self.sections[0]["direction"] = self.direction
        new_section = {"position": self.sections[0]["position"] + self.direction,
                       "direction": self.direction,
                       "full": False}
        self.sections.insert(0, new_section)

    def eat(self):
        self.sections[0]["full"] = True

    def open_mouth(self):
        self.mouth_open = True

    def close_mouth(self):
        self.mouth_open = False

    def draw(self):
        for sprite in self._get_sprites():
            sprite.draw()

    def _get_head_sprite(self):
        sprite = sprites.snake_mouth if self.mouth_open else sprites.snake_head
        head_sprite = Sprite(sprite, self.sections[0]["position"], self.sections[0]["direction"])
        if (self.sections[0]["direction"] == LEFT).all():
            head_sprite.flip_v()
        if (self.sections[0]["direction"] == DOWN).all():
            head_sprite.flip_h()
        return [head_sprite,]

    def _get_tail_sprite(self):
        sprite = sprites.snake_full if self.sections[-1]["full"] else sprites.snake_tail
        tail_sprite = Sprite(sprite, self.sections[-1]["position"], self.sections[-1]["direction"])
        if (self.sections[-1]["direction"] == LEFT).all():
            tail_sprite.flip_v()
        if (self.sections[-1]["direction"] == DOWN).all():
            tail_sprite.flip_h()
        return [tail_sprite,]

    def _get_body_sprites(self):
        body_sprites = []
        for i, section in enumerate(self.sections[1:-1]):
            section_dir  = section["direction"]
            previous_dir = self.sections[i+2]["direction"]
            if (section_dir == previous_dir).all() or section["full"]:
                sprite = sprites.snake_full if section["full"] else sprites.snake_body
                body_sprite = Sprite(sprite, section["position"], section_dir)
                if (section_dir == LEFT).all():
                    body_sprite.flip_v()
                if (section_dir == DOWN).all():
                    body_sprite.flip_h()
                body_sprites += [body_sprite,]
            else:
                rotate_left=np.array(((0, -1), (1, 0)))
                if (previous_dir.dot(rotate_left) == section_dir).all():
                    section_dir = section_dir.dot(rotate_left)
                body_sprites += [Sprite(sprites.snake_turn, section["position"], section_dir),]
        return body_sprites

    def _get_sprites(self):
        head = self._get_head_sprite()
        body = self._get_body_sprites()
        tail = self._get_tail_sprite()
        return head + body + tail


class Game:
    def __init__(self):
        self.pause = True
        self.direction_buffer = []
        self.score = 0
        self.hud = Hud()
        self.food = Food()
        self.snake = Snake()
        self.place_food()

    def handle_input_key(self, key):
        match key:
            case pygame.K_UP   : self.direction_buffer += [UP,]
            case pygame.K_DOWN : self.direction_buffer += [DOWN,]
            case pygame.K_LEFT : self.direction_buffer += [LEFT,]
            case pygame.K_RIGHT: self.direction_buffer += [RIGHT,]
            case pygame.K_SPACE: self.pause = not self.pause
        if len(self.direction_buffer) > 0:
            self.pause = False

    def place_food(self):
        self.food.move()
        for section in self.snake.sections:
            if (self.food.position == section["position"]).all():
                self.place_food()

    def change_direction(self):
        if len(self.direction_buffer) == 0:
            return
        if len(self.direction_buffer) > 2:
            self.direction_buffer = self.direction_buffer[-2:]
        direction = self.direction_buffer.pop(0)
        # This does'n work because you could change directions two times before it moves:
        # if (self.snake.direction + direction == 0).all():
        if (self.snake.sections[0]["position"] + direction == self.snake.sections[1]["position"]).all():
            return
        self.snake.direction = direction

    def check_collisions(self):
        head_position = self.snake.sections[0]["position"]
        # Collision with wall:
        if not 0 <= head_position[0] < GRID_WIDTH or not 0 <= head_position[1] < GRID_HEIGHT:
            self.game_over()
        # Collision with body:
        for section in self.snake.sections[1:]:
            if (head_position == section["position"]).all():
                self.game_over()
        # Collision with food:
        if (head_position == self.food.position).all():
            self.snake.open_mouth()
            self.snake.eat()
            self.place_food()
            self.score += 1
        # Food in front:
        front_position = head_position + self.snake.direction
        if (front_position == self.food.position).all():
            self.snake.open_mouth()

    def update(self):
        if self.pause:
            return
        self.snake.close_mouth()
        self.change_direction()
        self.snake.move()
        self.check_collisions()

    def draw(self):
        self.hud.draw_borders()
        self.hud.draw_score(self.score)
        self.food.draw()
        self.snake.draw()

    def game_over(self):
        self.pause = True
        self.score = 0
        self.snake = Snake()
        self.place_food()


class Hud:
    def draw_borders(self):
    # pylint:disable=invalid-name  # doesn't like lower case variables
        for x in np.arange(SCREEN_BORDER - 2, LEVEL_WIDTH + SCREEN_BORDER + 2):
            Cell(x, SCREEN_BORDER + HUD_BAR - 4).draw()
            Cell(x, SCREEN_BORDER + HUD_BAR - 2).draw()
            Cell(x, SCREEN_BORDER + HUD_BAR + LEVEL_HEIGHT + 1).draw()
        for y in np.arange(SCREEN_BORDER + HUD_BAR - 1, SCREEN_BORDER + HUD_BAR + LEVEL_HEIGHT + 1):
            Cell(SCREEN_BORDER - 2, y).draw()
            Cell(LEVEL_WIDTH + SCREEN_BORDER + 1, y).draw()

    def draw_score(self, score):
        numbers_sprites = []
        for digit in str(score).zfill(4)[-4:]:
            match int(digit):
                case 1: numbers_sprites += [sprites.one,]
                case 2: numbers_sprites += [sprites.two,]
                case 3: numbers_sprites += [sprites.three,]
                case 4: numbers_sprites += [sprites.four,]
                case 5: numbers_sprites += [sprites.five,]
                case 6: numbers_sprites += [sprites.six,]
                case 7: numbers_sprites += [sprites.seven,]
                case 8: numbers_sprites += [sprites.eight,]
                case 9: numbers_sprites += [sprites.nine,]
                case 0: numbers_sprites += [sprites.zero,]

        for i, sprite in enumerate(numbers_sprites):
            position = np.array((i, 0))
            Sprite(sprite, position).draw(hud = True)


if __name__ == "__main__":
    # pylint:disable=invalid-name  # doesn't like lower case variables
    check_sprites_size(sprites.game_sprites, SPRITE_SIZE, SPRITE_SIZE)
    check_sprites_size(sprites.number_sprites, HUD_SPRITE_H, HUD_SPRITE_W)

    pygame.init()
    screen_width  = CELL_WIDTH  * (LEVEL_WIDTH  + 2*SCREEN_BORDER)
    screen_height = CELL_HEIGHT * (LEVEL_HEIGHT + 2*SCREEN_BORDER + HUD_BAR)
    screen = pygame.display.set_mode((screen_width, screen_height))

    clock  = pygame.time.Clock()
    game   = Game()
    timer  = pygame.USEREVENT
    pygame.time.set_timer(timer, GAME_SPEED)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                game.handle_input_key(event.key)
            if event.type == timer:
                game.update()

        screen.fill(BG_COLOR)
        game.draw()
        pygame.display.update()
        clock.tick(60)
