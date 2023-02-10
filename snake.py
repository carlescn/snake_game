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
SCREEN_BORDER =  3    # Size of borders at the edge of the screen, in cells
CELL_COLOR    = pygame.Color(( 35,  43, 1))    # Color of the "fake pixels" (RGB)
BG_MAIN_COLOR = pygame.Color((175, 215, 5))    # Main color of the background (RGB)
BG_EDGE_COLOR = pygame.Color((155, 175, 2))    # Dark color for the background gradient (RGB)

## Starting position
START_X         = GRID_WIDTH//2     # Starting X position
START_Y         = GRID_HEIGHT//2    # Starting Y position
START_LENGTH    = 7                 # Starting size
START_DIRECTION = RIGHT             # Starting direction

## Difficulty
GAME_SPEED  = 200    # Milliseconds between game cycles
WRAP_AROUND = True   # Behavior when touching the edge of the screen. True: wrap around. False: die.
# END Customize

POINTS = GAME_SPEED // 100  # TODO: study the actual scoring system

# BETTER DON'T TOUCH THIS!! (it *should* work with different sized sprites in sprites.py)
SPRITE_SIZE  =  4    # Hight and width of the game sprites, in cells (see above)
HUD_SPRITE_W =  4    # Width  of the HUD numbers sprites, in cells (see above)
HUD_SPRITE_H =  5    # Height of the HUD numbers sprites, in cells (see above)
HUD_BAR      =  3 + HUD_SPRITE_H    # Height of the HUD top bar, in cells (see above)


LEVEL_WIDTH  = GRID_WIDTH  * SPRITE_SIZE
LEVEL_HEIGHT = GRID_HEIGHT * SPRITE_SIZE


class Cell:
# pylint:disable=too-few-public-methods
    def __init__(self, rect_x, rect_y):
        rect_width  = CELL_WIDTH  - BORDER_WIDTH
        rect_height = CELL_HEIGHT - BORDER_WIDTH
        rect_x = rect_x * CELL_WIDTH  + BORDER_WIDTH
        rect_y = rect_y * CELL_HEIGHT + BORDER_WIDTH
        self.rect = pygame.Rect(rect_x, rect_y, rect_width, rect_height)

    def draw(self):
        pygame.draw.rect(SCREEN, CELL_COLOR, self.rect)


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

        new_position = self.sections[0]["position"] + self.direction
        if WRAP_AROUND:
            new_position[0] = new_position[0] % GRID_WIDTH
            new_position[1] = new_position[1] % GRID_HEIGHT
        new_section = {"position": new_position,
                       "direction": self.direction,
                       "full": False}
        self.sections.insert(0, new_section)
        self.sections[1]["direction"] = self.direction

    def eat(self):
        self.sections[0]["full"] = True

    def open_mouth(self):
        self.mouth_open = True

    def close_mouth(self):
        self.mouth_open = False

    def draw(self):
        for sprite in self._get_sprites():
            sprite.draw()

    def _get_sprites(self):
        head = self._get_head_sprite()
        body = self._get_body_sprites()
        tail = self._get_tail_sprite()
        return head + body + tail

    def _flip_sprite_if_left_or_down(self, sprite, direction):
        """ This is only to imitate the Nokia game sprite orientation """
        if (direction == LEFT).all():
            sprite.flip_v()
        elif (direction == DOWN).all():
            sprite.flip_h()

    def _get_head_sprite(self):
        head = self.sections[0]
        sprite = sprites.snake_mouth if self.mouth_open else sprites.snake_head
        head_sprite = Sprite(sprite, head["position"], head["direction"])
        self._flip_sprite_if_left_or_down(head_sprite, head["direction"])
        return [head_sprite,]

    def _get_tail_sprite(self):
        tail = self.sections[-1]
        sprite = sprites.snake_full if tail["full"] else sprites.snake_tail
        tail_sprite = Sprite(sprite, tail["position"], tail["direction"])
        self._flip_sprite_if_left_or_down(tail_sprite, tail["direction"])
        return [tail_sprite,]

    def _get_body_sprites(self):
        body_sprites = []
        for i, section in enumerate(self.sections[1:-1]):
            section_dir  = section["direction"]
            previous_dir = self.sections[i+2]["direction"]
            if (section_dir == previous_dir).all() or section["full"]:
                sprite = sprites.snake_full if section["full"] else sprites.snake_body
                body_sprite = Sprite(sprite, section["position"], section_dir)
                self._flip_sprite_if_left_or_down(body_sprite, section_dir)
                body_sprites += [body_sprite,]
            else:
                rotate_left=np.array(((0, -1), (1, 0)))
                if (previous_dir.dot(rotate_left) == section_dir).all():
                    section_dir = section_dir.dot(rotate_left)
                body_sprites += [Sprite(sprites.snake_turn, section["position"], section_dir),]
        return body_sprites


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
        if (self.snake.sections[0]["position"] + direction
                == self.snake.sections[1]["position"]).all():
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
            BEEP.play(maxtime=10)
            self.place_food()
            self.score += POINTS
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


def _check_sprites_size(sprites_list, height, width):
    for sprite in sprites_list:
        assert np.array(sprite).shape[0] == height
        assert np.array(sprite).shape[1] == width

def _draw_background():
    """ Draws a rectangle the size of the screen with a gradient at the edges """
    size = SCREEN.get_width() / 32
    surface = pygame.Surface((size, size))
    pygame.draw.rect(surface, BG_EDGE_COLOR, pygame.Rect(0, 0, size, size))
    pygame.draw.rect(surface, BG_MAIN_COLOR, pygame.Rect(1, 1, size - 2, size - 2))
    surface = pygame.transform.smoothscale(surface, (SCREEN.get_width(), SCREEN.get_height()))
    SCREEN.blit(surface, pygame.Rect(0, 0, SCREEN.get_width(), SCREEN.get_height()))


if __name__ == "__main__":
    # pylint:disable=invalid-name  # doesn't like lower case variables
    _check_sprites_size(sprites.game_sprites, SPRITE_SIZE, SPRITE_SIZE)
    _check_sprites_size(sprites.number_sprites, HUD_SPRITE_H, HUD_SPRITE_W)

    pygame.init()
    pygame.display.set_caption("Snake")
    icon = pygame.image.load("icon.png")
    pygame.display.set_icon(icon)

    screen_width  = CELL_WIDTH  * (LEVEL_WIDTH  + 2*SCREEN_BORDER)
    screen_height = CELL_HEIGHT * (LEVEL_HEIGHT + 2*SCREEN_BORDER + HUD_BAR)
    SCREEN = pygame.display.set_mode((screen_width, screen_height))

    pygame.mixer.init()
    buffer = np.sin(2 * np.pi * np.arange(44100) * 1760 / 44100).astype(np.float32)
    BEEP = pygame.mixer.Sound(buffer)

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

        _draw_background()
        game.draw()
        pygame.display.update()
        clock.tick(60)
