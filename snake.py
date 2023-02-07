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
GRID_WIDTH   = 20                 # Width of the screen, in sprites
GRID_HEIGHT  = 20                 # Height of the screen, in sprites

GAME_SPEED   = 120                # Time between updates in milliseconds

START_X         = GRID_WIDTH//3   # Starting X position
START_Y         = GRID_HEIGHT//2  # Starting Y position
START_LENGTH    = 3               # Starting size
START_DIRECTION = RIGHT           # Starting direction

FOOD_SPRITE = ((0, 1, 0, 0),
               (1, 0, 1, 0),
               (0, 1, 0, 0),
               (0, 0, 0, 0))

SNAKE_HEAD  = ((0, 1, 0, 0),
               (1, 0, 1, 1),
               (1, 1, 1, 1),
               (0, 0, 0, 0))

SNAKE_BODY  = ((0, 0, 0, 0),
               (1, 1, 0, 1),
               (1, 0, 1, 1),
               (0, 0, 0, 0))

SNAKE_TAIL  = ((0, 0, 0, 0),
               (0, 0, 1, 1),
               (1, 1, 1, 1),
               (0, 0, 0, 0))

SNAKE_TURN  = ((0, 0, 0, 0),
               (0, 0, 1, 1),
               (0, 1, 0, 1),
               (0, 1, 1, 0))

def _check_sprites_size():
    for sprite in (FOOD_SPRITE, SNAKE_HEAD, SNAKE_BODY, SNAKE_TAIL):
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
    """
    position: np.array(x:int, y:int)
    """
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
        self._directions = None
        self.positions = None
        self.direction = None
        self.growing = None
        self.moving = None
        self.restart()

    def restart(self):
        start_xys = np.array((START_X, START_Y))
        self.positions = [start_xys - START_DIRECTION * i for i in np.arange(START_LENGTH)]
        self.direction = START_DIRECTION
        self._directions = [START_DIRECTION,] * START_LENGTH
        self.growing = False

    def move(self):
    # pylint:disable=invalid-name  # doesn't like single letter x, y
        if not self.growing:
            self._directions.pop(-1)
            self.positions.pop(-1)
        self._directions[0] = self.direction
        self._directions.insert(0, self.direction)
        self.positions.insert(0, self.positions[0] + self.direction)
        self.growing = False

    def grow(self):
        self.growing = True

    def _get_sprites(self):
        head = Sprite(SNAKE_HEAD, self.positions[0], self._directions[0])
        if (self._directions[0] == LEFT).all():
            head.flip_v()
        tail = Sprite(SNAKE_TAIL, self.positions[-1], self._directions[-1])
        body = []
        for i, position in enumerate(self.positions[1:-1]):
            sprite_dir   = self._directions[i+1]
            previous_dir = self._directions[i+2]
            if (sprite_dir == previous_dir).all():
                body += [Sprite(SNAKE_BODY, position, sprite_dir),]
            else:
                rotate_left=np.array(((0, -1), (1, 0)))
                if (previous_dir.dot(rotate_left) == sprite_dir).all():
                    sprite_dir = sprite_dir.dot(rotate_left)
                body += [Sprite(SNAKE_TURN, position, sprite_dir),]
        return [head,] + body + [tail,]

    def draw(self):
        for sprite in self._get_sprites():
            sprite.draw()


class Game:
    def __init__(self):
        self.pause = True
        self.high_score = 0
        self.food  = Food()
        self.snake = Snake()
        self.place_food()
        self.direction_buffer = []

    def change_direction(self):
        if len(self.direction_buffer) == 0:
            return
        if len(self.direction_buffer) > 2:
            self.direction_buffer = self.direction_buffer[-2:]
        direction = self.direction_buffer.pop(0)
        # This does'n work because you could change directions two times before it moves:
        # if (self.snake.direction + direction == 0).all():
        if (self.snake.positions[0] + direction == self.snake.positions[1]).all():
            return
        self.snake.direction = direction
        self.pause = False

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
        new_position = self.snake.positions[0] + self.snake.direction
        # Collision with wall
        if not 0 <= new_position[0] < GRID_WIDTH or not 0 <= new_position[1] < GRID_HEIGHT:
            self.game_over()
        # Collision with body
        for position in self.snake.positions[1:]:
            if (new_position == position).all():
                self.game_over()
        # Collision with food
        if (new_position == self.food.position).all():
            self.place_food()
            self.snake.grow()

    def place_food(self):
        self.food.move()
        for position in self.snake.positions:
            if (self.food.position == position).all():
                self.place_food()

    def show_score(self):
        score = len(self.snake.positions) - START_LENGTH
        if score > self.high_score:
            self.high_score = score
        pygame.display.set_caption(
            f'Snake - Score = {score:d} (High score: {self.high_score:d})'
        )

    def update(self):
        if self.pause:
            return
        self.change_direction()
        self.check_collisions()
        self.snake.move()
        self.show_score()

    def game_over(self):
        self.pause = True
        self.snake.restart()
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
