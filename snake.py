""" Snake game """
import sys
import random
import pygame
import numpy as np

GAME_SPEED = 100 # Time between updates in milliseconds
CELL   = 20      # Size of one square in pixels
GRID_W = 20      # Width of the screen in cells
GRID_H = 20      # Height of the screen in cells

UP    = np.array(( 0, -1))
DOWN  = np.array(( 0,  1))
LEFT  = np.array((-1,  0))
RIGHT = np.array(( 1,  0))

# Starting position, size and direction of the snake
START_X         = GRID_W//3
START_Y         = GRID_H//2
START_LENGTH    = 3
START_DIRECTION = RIGHT

BACKGROUND_COLOR = pygame.Color('moccasin')
FOOD_COLOR       = pygame.Color('red')
SNAKE_HEAD_COLOR = pygame.Color('green4')
SNAKE_BODY_COLOR = pygame.Color('green3')

class Block:
    def __init__(self, x, y, color, circle=False):
    # pylint:disable=invalid-name  # doesn't like single letter x, y
        self.position = np.array((x, y))
        self.rect = pygame.rect.Rect(x * CELL, y * CELL, CELL, CELL)
        self.color = color
        self.circle = circle

    def move(self, x, y):
    # pylint:disable=invalid-name  # doesn't like single letter x, y
        self.position = (x, y)
        self.rect.x = x * CELL
        self.rect.y = y * CELL

    def draw(self):
        if self.circle:
            pygame.draw.ellipse(screen, self.color, self.rect)
        else:
            pygame.draw.rect(screen, self.color, self.rect)

class Food:
    def __init__(self):
        self.block = Block(0, 0, FOOD_COLOR, circle = True)

    def move(self):
    # pylint:disable=invalid-name  # doesn't like single letter x, y
        x = random.randint(0, GRID_W -1)
        y = random.randint(0, GRID_H -1)
        self.block.move(x, y)

    def draw(self):
        self.block.draw()

class Snake:
    def __init__(self):
        self.blocks = None
        self.direction = None
        self.growing = None
        self.moving = None
        self.restart()

    def move(self):
    # pylint:disable=invalid-name  # doesn't like single letter x, y
        if not self.moving:
            return
        if not self.growing:
            self.blocks.pop(-1)
        self.blocks[0].color = SNAKE_BODY_COLOR
        x, y = self.blocks[0].position + self.direction
        self.blocks.insert(0, Block(x, y, SNAKE_HEAD_COLOR))
        self.growing = False

    def change_direction(self, new_direction):
        # if (self.direction + new_direction == 0).all():
        # does'n work: you can change directions two times it moves
        new_position = self.blocks[0].position + new_direction
        if (new_position == self.blocks[1].position).all():
            return
        self.direction = new_direction
        self.moving = True

    def grow(self):
        self.growing = True

    def stop(self):
        self.moving = False

    def restart(self):
        start_xys = np.array((START_X, START_Y))
        start_xys = [start_xys - START_DIRECTION * i for i in np.arange(START_LENGTH)]
        self.blocks = [Block(x, y, SNAKE_BODY_COLOR) for x, y in start_xys]
        self.blocks[0].color = SNAKE_HEAD_COLOR
        self.direction = START_DIRECTION
        self.growing = False
        self.moving = False

    def draw(self):
        for block in self.blocks:
            block.draw()

class Game:
    def __init__(self):
        self.food  = Food()
        self.snake = Snake()
        self.move_food()
        self.high_score = 0

    def handle_input_key(self, key):
        match key:
            case pygame.K_UP   : self.snake.change_direction(UP)
            case pygame.K_DOWN : self.snake.change_direction(DOWN)
            case pygame.K_LEFT : self.snake.change_direction(LEFT)
            case pygame.K_RIGHT: self.snake.change_direction(RIGHT)
            case pygame.K_SPACE: self.snake.stop()

    def check_collisions(self):
        new_position = self.snake.blocks[0].position + self.snake.direction
        # Collision with wall
        if not 0 <= new_position[0] < GRID_W or not 0 <= new_position[1] < GRID_H:
            self.game_over()
        # Collision with body
        for block in self.snake.blocks[1:]:
            if (new_position == block.position).all():
                self.game_over()
        # Collision with food
        if (new_position == self.food.block.position).all():
            self.move_food()
            self.snake.grow()

    def move_food(self):
        self.food.move()
        for block in self.snake.blocks:
            if (self.food.block.position == block.position).all():
                self.move_food()

    def show_score(self):
        score = len(self.snake.blocks) - START_LENGTH
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
        self.move_food()

    def draw(self):
        self.food.draw()
        self.snake.draw()

pygame.init()
screen = pygame.display.set_mode((GRID_W * CELL, GRID_H * CELL))
clock  = pygame.time.Clock()
timer  = pygame.USEREVENT  # pylint:disable=invalid-name  # lower case
pygame.time.set_timer(timer, GAME_SPEED)
game   = Game()
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.KEYDOWN:
            game.handle_input_key(event.key)
        if event.type == timer:
            game.update()
    screen.fill(BACKGROUND_COLOR)
    game.draw()
    pygame.display.update()
    clock.tick(60)
