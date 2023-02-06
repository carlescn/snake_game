""" Snake game """
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
CELL   =  8                 # Size of one "fake pixel", in actual pixels
BORDER =  1                 # Size of empty space between cells, in actual pixels
SPRITE =  4 #(LEAVE AT 4!!) # Size of the sprites, in cells
GRID_W = 20                 # Width of the screen, in sprites
GRID_H = 20                 # Height of the screen, in sprites

GAME_SPEED = 120            # Time between updates in milliseconds

START_X         = GRID_W//3 # Starting X position
START_Y         = GRID_H//2 # Starting Y position
START_LENGTH    = 3         # Starting size
START_DIRECTION = RIGHT     # Starting direction

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

class Cell:
    def __init__(self, x = 0, y = 0):
    # pylint:disable=invalid-name  # doesn't like single letter x, y
        self.color = CELL_COLOR
        rect_size = CELL - BORDER
        self.rect = pygame.Rect(0, 0, rect_size, rect_size)
        self.place(x, y)

    def place(self, x, y):
    # pylint:disable=invalid-name  # doesn't like single letter x, y
        self.rect.x = x * CELL + BORDER
        self.rect.y = y * CELL + BORDER

    def draw(self):
        pygame.draw.rect(screen, self.color, self.rect)


class Sprite:
    """
    sprite:
    position: np.array(x:int, y:int)
    """
    def __init__(self, sprite, position, direction = RIGHT, flip = False):
    # pylint:disable=invalid-name  # doesn't like single letter x, y
        self._check_sprite_size(sprite)
        self.sprite = self._rotate_sprite(sprite, direction, flip)
        self.position = position
        self.cell_positions = self._get_cell_positions()
        self.cells = [Cell(x, y) for x, y in self.cell_positions]

    def _check_sprite_size(self, sprite):
        assert len(sprite) == SPRITE  # Check number of cols
        for col in sprite:
            assert len(col) == SPRITE # Check number of rows

    def _get_cell_positions(self):
        cell_positions = []
        for j, col in enumerate(self.sprite):
            for i, pos in enumerate(col):
                if pos:
                    cell_positions.append(np.array((i, j)))
        return cell_positions

    def draw(self):
    # pylint:disable=invalid-name  # doesn't like single letter x, y
        x, y = self.position
        for cell, (i, j) in zip(self.cells, self.cell_positions):
            cell.place(x * SPRITE + i, y * SPRITE + j)
            cell.draw()

    def _rotate_sprite(self, sprite, direction, flip):
        if (direction == UP).all():
            sprite = np.rot90(sprite)
        elif (direction == DOWN).all():
            sprite = np.rot90(sprite,3)
        elif (direction == LEFT).all():
            sprite = np.fliplr(sprite)
        elif (direction == RIGHT).all():
            sprite = np.array(sprite)
        if flip:
            sprite = np.fliplr(sprite)
        return sprite


class Food:
    def __init__(self):
        self.position = None
        self.move()

    def move(self):
    # pylint:disable=invalid-name  # doesn't like single letter x, y
        x = random.randint(0, GRID_W -1)
        y = random.randint(0, GRID_H -1)
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
        self.moving = False

    def move(self):
    # pylint:disable=invalid-name  # doesn't like single letter x, y
        if not self.moving:
            return
        if not self.growing:
            self._directions.pop(-1)
            self.positions.pop(-1)
        self._directions[0] = self.direction
        self._directions.insert(0, self.direction)
        self.positions.insert(0, self.positions[0] + self.direction)
        self.growing = False

    # TODO: add buffer
    def change_direction(self, new_direction):
        # if (self._directions[0] + new_direction == 0).all():
        # does'n work: you can change directions two times it moves
        new_position = self.positions[0] + new_direction
        if (new_position == self.positions[1]).all():
            return
        self.direction = new_direction
        self.moving = True

    def grow(self):
        self.growing = True

    def stop(self):
        self.moving = False

    def get_sprites(self):
        head = [Sprite(SNAKE_HEAD, self.positions[0], self._directions[0]),]
        tail = [Sprite(SNAKE_TAIL, self.positions[-1], self._directions[-1]),]
        body = []
        for i, position in enumerate(self.positions[1:-1]):
            new_dir  = self._directions[i+1]
            old_dir = self._directions[i+2]
            if (new_dir == old_dir).all():
                body += [Sprite(SNAKE_BODY, position, new_dir),]
            else:
                # TODO: Make this simpler?
                flip = False
                if (old_dir == UP).all() and (new_dir == RIGHT).all():
                    direction = RIGHT
                elif (old_dir == LEFT).all() and (new_dir == DOWN).all():
                    direction = RIGHT
                elif (old_dir == UP).all() and (new_dir == LEFT).all():
                    direction = LEFT
                elif (old_dir == RIGHT).all() and (new_dir == DOWN).all():
                    direction = LEFT
                elif (old_dir == DOWN).all() and (new_dir == RIGHT).all():
                    direction = UP
                elif (old_dir == LEFT).all() and (new_dir == UP).all():
                    direction = UP
                elif (old_dir == DOWN).all() and (new_dir == LEFT).all():
                    direction = UP
                    flip = True
                elif (old_dir == RIGHT).all() and (new_dir == UP).all():
                    direction = UP
                    flip = True
                body += [Sprite(SNAKE_TURN, position, direction, flip),]
        return head + body + tail

    def draw(self):
        for sprite in self.get_sprites():
            sprite.draw()


class Game:
    def __init__(self):
        self.high_score = 0
        self.food  = Food()
        self.snake = Snake()
        self.place_food()

    def handle_input_key(self, key):
        match key:
            case pygame.K_UP   : self.snake.change_direction(UP)
            case pygame.K_DOWN : self.snake.change_direction(DOWN)
            case pygame.K_LEFT : self.snake.change_direction(LEFT)
            case pygame.K_RIGHT: self.snake.change_direction(RIGHT)
            case pygame.K_SPACE: self.snake.stop()

    def check_collisions(self):
        new_position = self.snake.positions[0] + self.snake.direction
        # Collision with wall
        if not 0 <= new_position[0] < GRID_W or not 0 <= new_position[1] < GRID_H:
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
        if self.snake.moving:
            self.check_collisions()
        self.snake.move()
        self.show_score()

    def game_over(self):
        self.snake.restart()
        self.place_food()

    def draw(self):
        self.food.draw()
        self.snake.draw()


pygame.init()
screen = pygame.display.set_mode((GRID_W * CELL * SPRITE, GRID_H * CELL * SPRITE))
clock  = pygame.time.Clock()
game   = Game()

timer  = pygame.USEREVENT  # pylint:disable=invalid-name  # lower case
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
