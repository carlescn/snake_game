""" An implementation of the Snake game using pygame and numpy arrays """
import sys
import random
import pygame
import numpy as np

BG_COLOR   = pygame.Color((175, 215, 5))
CELL_COLOR = pygame.Color(( 35,  43, 1))

UP    = np.array(( 0, -1))
DOWN  = np.array(( 0,  1))
LEFT  = np.array((-1,  0))
RIGHT = np.array(( 1,  0))

# Customize the game look and feel:
CELL_SIZE    =  8                 # Size of one "fake pixel", in actual pixels
BORDER_WIDTH =  1                 # Size of empty space between cells, in actual pixels
SPRITE_SIZE  =  4 #(LEAVE AT 4!!) # Size of the sprites, in cells
GRID_WIDTH   = 16                 # Width of the screen, in sprites
GRID_HEIGHT  =  9                 # Height of the screen, in sprites

GAME_SPEED   = 150                # Time between updates in milliseconds

START_X         = GRID_WIDTH//3   # Starting X position
START_Y         = GRID_HEIGHT//2  # Starting Y position
START_LENGTH    = 4               # Starting size
START_DIRECTION = RIGHT           # Starting direction

FOOD_SPRITE  = ((0, 1, 0, 0),
                (1, 0, 1, 0),
                (0, 1, 0, 0),
                (0, 0, 0, 0))

SPRITE_HEAD  = ((1, 0, 0, 0),
                (0, 1, 1, 0),
                (1, 1, 1, 0),
                (0, 0, 0, 0))

SPRITE_MOUTH = ((1, 0, 1, 0),
                (0, 1, 0, 0),
                (1, 1, 0, 0),
                (0, 0, 1, 0))

SPRITE_BODY  = ((0, 0, 0, 0),
                (1, 1, 0, 1),
                (1, 0, 1, 1),
                (0, 0, 0, 0))

SPRITE_FULL  = ((0, 1, 1, 0),
                (1, 1, 0, 1),
                (1, 0, 1, 1),
                (0, 1, 1, 0))

SPRITE_TURN  = ((0, 0, 0, 0),
                (0, 0, 1, 1),
                (0, 1, 0, 1),
                (0, 1, 1, 0))

SPRITE_TAIL  = ((0, 0, 0, 0),
                (0, 0, 0, 1),
                (0, 1, 1, 1),
                (0, 0, 0, 0))

def _check_sprites_size():
    for sprite in (FOOD_SPRITE, SPRITE_HEAD, SPRITE_MOUTH,
                   SPRITE_BODY, SPRITE_FULL, SPRITE_TURN, SPRITE_TAIL):
        assert np.array(sprite).shape[0] == SPRITE_SIZE
        assert np.array(sprite).shape[1] == SPRITE_SIZE


class Cell:
    def __init__(self, x, y):
    # pylint:disable=invalid-name  # doesn't like single letter x, y
        rect_size = CELL_SIZE - BORDER_WIDTH
        x = x * CELL_SIZE + BORDER_WIDTH
        y = y * CELL_SIZE + BORDER_WIDTH
        self.rect = pygame.Rect(x, y, rect_size, rect_size)

    def draw(self):
        pygame.draw.rect(screen, CELL_COLOR, self.rect)


class Sprite:
    """ position: np.array(x:int, y:int) """
    def __init__(self, sprite, position, direction = RIGHT):
    # pylint:disable=invalid-name  # doesn't like single letter x, y
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

    def draw(self):
    # pylint:disable=invalid-name  # doesn't like single letter x, y
        cell_positions = [
            np.array((i, j)) for j, col in enumerate(self.sprite)
            for i, pos in enumerate(col)
            if pos
        ]
        x, y = self.position * SPRITE_SIZE
        for cell in [Cell(x + i, y + j) for i, j in cell_positions]:
            cell.draw()


class Food:
    def __init__(self):
        self.position = None
        self.move()

    def move(self):
    # pylint:disable=invalid-name  # doesn't like single letter x, y
        x = random.randint(0, GRID_WIDTH -1)
        y = random.randint(0, GRID_HEIGHT -1)
        self.position = np.array((x, y))

    def draw(self):
        Sprite(FOOD_SPRITE, self.position).draw()


class Snake:
    def __init__(self):
        start_xys = np.array((START_X, START_Y))
        positions = [start_xys - START_DIRECTION * i for i in np.arange(START_LENGTH)]
        directions = [START_DIRECTION,] * START_LENGTH
        full = [False,] * START_LENGTH
        self.sections = [
            {"position": p, "direction": d, "full": f}
            for p, d, f in zip(positions, directions, full)
            ]
        self.direction = START_DIRECTION
        self.growing = False
        self.mouth_open = False

    def move(self):
    # pylint:disable=invalid-name  # doesn't like single letter x, y
        if self.sections[-1]["full"]:
            self.sections[-1]["full"] = False
        else:
            self.sections.pop(-1)

        self.sections[0]["direction"] = self.direction
        new_section = {"position": self.sections[0]["position"] + self.direction,
                       "direction": self.direction,
                       "full": False}
        self.sections.insert(0, new_section)

        if self.growing:
            self.sections[0]["full"] = True
            self.growing = False

    def grow(self):
        self.growing = True

    def open_mouth(self):
        self.mouth_open = True

    def close_mouth(self):
        self.mouth_open = False

    def draw(self):
        for sprite in self._get_sprites():
            sprite.draw()

    def _get_head_sprite(self):
        sprite = SPRITE_MOUTH if self.mouth_open else SPRITE_HEAD
        head_sprite = Sprite(sprite, self.sections[0]["position"], self.sections[0]["direction"])
        if (self.sections[0]["direction"] == LEFT).all():
            head_sprite.flip_v()
        if (self.sections[0]["direction"] == DOWN).all():
            head_sprite.flip_h()
        return [head_sprite,]

    def _get_tail_sprite(self):
        sprite = SPRITE_FULL if self.sections[-1]["full"] else SPRITE_TAIL
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
                sprite = SPRITE_FULL if section["full"] else SPRITE_BODY
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
                body_sprites += [Sprite(SPRITE_TURN, section["position"], section_dir),]
        return body_sprites

    def _get_sprites(self):
        head = self._get_head_sprite()
        body = self._get_body_sprites()
        tail = self._get_tail_sprite()
        return head + body + tail


class Game:
    def __init__(self):
        self.pause = True
        self.score = 0
        self.high_score = 0
        self.direction_buffer = []
        self.food  = Food()
        self.snake = Snake()
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

    def handle_input_key(self, key):
        match key:
            case pygame.K_UP   : self.direction_buffer += [UP,]
            case pygame.K_DOWN : self.direction_buffer += [DOWN,]
            case pygame.K_LEFT : self.direction_buffer += [LEFT,]
            case pygame.K_RIGHT: self.direction_buffer += [RIGHT,]
            case pygame.K_SPACE: self.pause = not self.pause
        if len(self.direction_buffer) > 0:
            self.pause = False

    def check_collisions(self):
        new_position = self.snake.sections[0]["position"] + self.snake.direction
        # Collision with wall
        if not 0 <= new_position[0] < GRID_WIDTH or not 0 <= new_position[1] < GRID_HEIGHT:
            self.game_over()
        # Collision with body
        for section in self.snake.sections[1:]:
            if (new_position == section["position"]).all():
                self.game_over()
        # Collision with food
        if (new_position == self.food.position).all():
            self.snake.open_mouth()
            self.snake.grow()
            self.place_food()
            self.score += 1
        # Food in front
        new_position = new_position + self.snake.direction
        if (new_position == self.food.position).all():
            self.snake.open_mouth()

    def place_food(self):
        self.food.move()
        for section in self.snake.sections:
            if (self.food.position == section["position"]).all():
                self.place_food()

    def show_score(self):
        self.high_score = max(self.score, self.high_score)
        pygame.display.set_caption(f'Snake - Score = {self.score:d} (High score: {self.high_score:d})')

    def update(self):
        if self.pause:
            return
        self.snake.close_mouth()
        self.change_direction()
        self.check_collisions()
        self.snake.move()
        self.show_score()

    def game_over(self):
        self.pause = True
        self.score = 0
        self.snake = Snake()
        self.place_food()

    def draw(self):
        self.food.draw()
        self.snake.draw()


# pylint:disable=invalid-name  # doesn't like lower case variables
_check_sprites_size()

pygame.init()
screen_width = GRID_WIDTH * CELL_SIZE * SPRITE_SIZE
screen_height = GRID_HEIGHT * CELL_SIZE * SPRITE_SIZE
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
