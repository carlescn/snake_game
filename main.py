""" An implementation of the Snake game using Pygame and NumPy arrays """
import asyncio
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
BONUS_TIMER = 20     # Turns until the bonus disappears
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
    def __init__(self, sprite, position, direction = RIGHT):
        self.position = position     # type : np.array(x:int, y:int)
        self.original_sprite = sprite
        self.sprite = None
        self.face(direction)

    def face(self, direction):
        """ Rotate the sprite to face some direction. """
        if (direction == RIGHT).all():
            self.sprite = np.array(self.original_sprite)
        elif (direction == UP).all():
            self.sprite = np.rot90(self.original_sprite)
        elif (direction == LEFT).all():
            self.sprite = np.rot90(self.original_sprite,2)
        elif (direction == DOWN).all():
            self.sprite = np.rot90(self.original_sprite,3)

    def flip_h(self):
        """ Flip the sprite horizontally (left to right). """
        self.sprite = np.fliplr(self.sprite)

    def flip_v(self):
        """ Flip the sprite vertically (up to down). """
        self.sprite = np.flipud(self.sprite)

    def draw(self, hud = False, offset = (0, 0)):
        """ Convert the sprite to Cells and draw them on the screen.
        hud = True: draw the sprites on the top bar
        hud = False: draw the sprites on the main level
        offset (x, y): offset the drawing position by x and y. """
        cell_positions = [
            np.array((i, j)) for j, col in enumerate(self.sprite) for i, xy in enumerate(col) if xy
        ]
        sprite_x = self.position[0] * (HUD_SPRITE_W if hud else SPRITE_SIZE)
        sprite_y = self.position[1] * (HUD_SPRITE_H if hud else SPRITE_SIZE)
        for cell_x, cell_y in cell_positions:
            cell_x += sprite_x + SCREEN_BORDER + offset[0] + (-2 if hud else 0)
            cell_y += sprite_y + SCREEN_BORDER + offset[1] + (-2 if hud else HUD_BAR)
            Cell(cell_x, cell_y).draw()


class Food:
    def __init__(self):
        self.position = None
        self.place()

    def place(self):
    # pylint:disable=invalid-name  # doesn't like single letter x, y
        x = np.random.randint(0, GRID_WIDTH  - 1)
        y = np.random.randint(0, GRID_HEIGHT - 1)
        self.position = np.array((x, y))

    def overlaps(self, position):
        """Return True if position coincides with self.position"""
        return (position == self.position).all()

    def draw(self):
        Sprite(sprites.food, self.position).draw()


class Bonus:
    def __init__(self):
        self.timer = BONUS_TIMER
        self.position = None
        self.place()
        index = np.random.randint(0, len(sprites.bonus_sprites))         # index is an int:
        self.sprite = sprites.bonus_sprites[index]  # pylint:disable=invalid-sequence-index

    def place(self):
    # pylint:disable=invalid-name  # doesn't like single letter x, y
        x = random.randint(0, GRID_WIDTH - 2)
        y = random.randint(0, GRID_HEIGHT - 1)
        self.position = np.array((x, y))

    def overlaps(self, position):
        """Return True if position coincides with self.position (or right sprite)"""
        return (position == self.position).all() or (position == self.position + RIGHT).all()

    def draw(self):
        Sprite(self.sprite, self.position).draw()


class Snake:
    def __init__(self):
        self.mouth_open = False
        self.direction = START_DIRECTION
        start_position = np.array((START_X, START_Y))
        positions  = [start_position - START_DIRECTION * i for i in np.arange(START_LENGTH)]
        directions = [START_DIRECTION,] * START_LENGTH
        are_full   = [False,] * START_LENGTH
        self.sections = [
            {"position": p, "direction": d, "is_full": f}
            for p, d, f in zip(positions, directions, are_full)
            ]

    def move(self):
        """ Move the snake body one step. Grow its tail if last section is full. """
        if self.sections[-1]["is_full"]:
            self.sections[-1]["is_full"] = False
        else:
            self.sections.pop(-1)

        new_position = self.sections[0]["position"] + self.direction
        if WRAP_AROUND:
            new_position[0] = new_position[0] % GRID_WIDTH
            new_position[1] = new_position[1] % GRID_HEIGHT
        new_section = {"position": new_position,
                       "direction": self.direction,
                       "is_full": False}
        self.sections.insert(0, new_section)
        self.sections[1]["direction"] = self.direction

    def overlaps(self, position, check_itself = False):
        """Return True if position coincides with any section of the snake"""
        sections = self.sections[1:] if check_itself else self.sections
        for section in sections:
            if (position == section["position"]).all():
                return True
        return False

    def eat(self):
        self.open_mouth()
        self.sections[0]["is_full"] = True

    def open_mouth(self):
        self.mouth_open = True

    def close_mouth(self):
        self.mouth_open = False

    def draw(self):
        for sprite in self._get_sprites():
            sprite.draw()

    def _get_sprites(self):
        """ Return a list of all the snake Sprite objects """
        head = self._get_head_sprite()
        body = self._get_body_sprites()
        tail = self._get_tail_sprite()
        return head + body + tail

    def _flip_sprite_if_left_or_down(self, sprite, direction):
        """ Flips the sprite orientation to imitate the Nokia Snake II game """
        if (direction == LEFT).all():
            sprite.flip_v()
        elif (direction == DOWN).all():
            sprite.flip_h()

    def _get_head_sprite(self):
        """ Check the head direction and if the mouth is open,
        return the adequate Sprite object (in a list of length 1)."""
        head = self.sections[0]
        sprite = sprites.snake_mouth if self.mouth_open else sprites.snake_head
        head_sprite = Sprite(sprite, head["position"], head["direction"])
        self._flip_sprite_if_left_or_down(head_sprite, head["direction"])
        return [head_sprite,]

    def _get_tail_sprite(self):
        """ Check the tail direction and if it is full,
        return the adequate Sprite object (in a list of length 1)."""
        tail = self.sections[-1]
        sprite = sprites.snake_full if tail["is_full"] else sprites.snake_tail
        tail_sprite = Sprite(sprite, tail["position"], tail["direction"])
        self._flip_sprite_if_left_or_down(tail_sprite, tail["direction"])
        return [tail_sprite,]

    def _get_body_sprites(self):
        """ For every body section, check its direction, if it's turning and if it's full,
        return a list with the adequate Sprite objects."""
        body_sprites = []
        for i, section in enumerate(self.sections[1:-1]):
            section_dir  = section["direction"]
            previous_dir = self.sections[i+2]["direction"]
            if (section_dir == previous_dir).all() or section["is_full"]:
                sprite = sprites.snake_full if section["is_full"] else sprites.snake_body
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
# pylint:disable=too-many-instance-attributes
    def __init__(self):
        self.pause = True
        self.score = 0
        self.hud   = Hud()
        self.snake = Snake()
        self.food  = Food()
        self.bonus = Bonus()
        self.direction_buffer = []
        self.next_bonus_timer  = 0
        self.game_over()

    def handle_movement(self, direction):
        """ Add last input to the direction buffer. Unpause the game."""
        self.direction_buffer += [direction,]
        if len(self.direction_buffer) > 0:
            self.pause = False

    def handle_input_key(self, key):
        """ Change directions with arrow keys. Pause / unpause the game with space bar. """
        match key:
            case pygame.K_UP   : self.handle_movement(UP)
            case pygame.K_DOWN : self.handle_movement(DOWN)
            case pygame.K_LEFT : self.handle_movement(LEFT)
            case pygame.K_RIGHT: self.handle_movement(RIGHT)
            case pygame.K_SPACE: self.pause = not self.pause

    def handle_input_mouse_button(self, button):
        """ Change directions by clicking / tapping on the edge of the screen. """
        if button == pygame.BUTTON_LEFT:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            if mouse_x < SCREEN_WIDTH / 3:
                self.handle_movement(LEFT)
            elif mouse_x > SCREEN_WIDTH * 3 / 4:
                self.handle_movement(RIGHT)
            elif mouse_y < SCREEN_HEIGHT / 3:
                self.handle_movement(UP)
            elif mouse_y > SCREEN_HEIGHT * 2 / 3:
                self.handle_movement(DOWN)

    def place_food(self):
        """ Place food on the screen. Make sure it doesn't overlap any existing sprite. """
        self.food.place()
        if self.bonus is not None and self.bonus.overlaps(self.food.position):
            self.place_food()
        if self.snake.overlaps(self.food.position):
            self.place_food()

    def place_bonus(self):
        """ Place bonus on the screen. Make sure it doesn't overlap any existing sprite. """
        self.bonus.place()
        if self.bonus.overlaps(self.food.position) \
        or self.snake.overlaps(self.bonus.position) \
        or self.snake.overlaps(self.bonus.position + RIGHT):
            self.place_bonus()

    def reset_next_bonus_timer(self):
        # TODO: study actual frequency
        self.next_bonus_timer = int(np.random.normal(5.5, 0.5))

    def handle_bonus_timers(self):
        """ Handle bonus timers and create / remove instances. """
        if self.bonus is None:
            if self.next_bonus_timer == 0 and self.score > 0:
                self.bonus = Bonus()
                self.place_bonus()
        else:
            if self.bonus.timer == 0:
                self.bonus = None
                self.reset_next_bonus_timer()
            else:
                self.bonus.timer -= 1

    def change_direction(self):
        """ Change snake direction using the two last inputs on the direction buffer. """
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
        """ Check collisions with wall / body / food / bonus. """
        head_position = self.snake.sections[0]["position"]
        # Collision with wall:
        if not 0 <= head_position[0] < GRID_WIDTH or not 0 <= head_position[1] < GRID_HEIGHT:
            self.game_over()
        # Collision with body:
        if self.snake.overlaps(head_position, check_itself=True):
            self.game_over()
        # Collision with food:
        if self.food.overlaps(head_position):
            self.snake.eat()
            BEEP.play(maxtime=10)
            self.score += POINTS
            self.place_food()
            self.next_bonus_timer -= 1
        # Collision with bonus:
        if self.bonus is not None and self.bonus.overlaps(head_position):
            self.snake.eat()
            BEEP.play(maxtime=10)
            self.score += POINTS * self.bonus.timer
            self.bonus = None
            self.reset_next_bonus_timer()
        # Food or bonus in front:
        front_position = head_position + self.snake.direction
        if self.food.overlaps(front_position):
            self.snake.open_mouth()
        if self.bonus is not None and self.bonus.overlaps(front_position):
            self.snake.open_mouth()

    def update(self):
        if self.pause:
            return
        self.snake.close_mouth()
        self.change_direction()
        self.snake.move()
        self.check_collisions()
        self.handle_bonus_timers()

    def game_over(self):
        """ Reset game to initial state. """
        self.pause = True
        self.score = 0
        self.bonus = None
        self.reset_next_bonus_timer()
        self.snake = Snake()
        self.place_food()

    def draw(self):
        """ Draw the HUD and all the game sprites. """
        self.hud.draw_borders()
        self.hud.draw_score(self.score)
        self.food.draw()
        self.snake.draw()
        if self.bonus is not None:
            self.bonus.draw()
            self.hud.draw_bonus(self.bonus)


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
        score_sprites = self._get_number_sprites(score, 4)
        for i, sprite in enumerate(score_sprites):
            Sprite(sprite, (i, 0)).draw(hud = True)

    def draw_bonus(self, bonus):
        Sprite(bonus.sprite, (GRID_WIDTH - 4, 0)).draw(hud = True, offset = (2, 1))
        score_sprites = self._get_number_sprites(bonus.timer, 2)
        for i, sprite in enumerate(score_sprites):
            Sprite(sprite, (GRID_WIDTH - 2 + i, 0)).draw(hud = True, offset = (2, 0))

    def _get_number_sprites(self, number, digits):
        """ Return a list of number Sprite objects for the last n digits of number"""
        numbers_sprites = []
        for digit in str(number).zfill(digits)[-digits:]:
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
        return numbers_sprites


def _check_sprites_size(sprites_list, width, height):
    """ Check that all the sprites conform to their expected size. """
    for sprite in sprites_list:
        assert np.array(sprite).shape[0] == height
        assert np.array(sprite).shape[1] == width

def _draw_background():
    """ Draw a rectangle the size of the screen with a gradient at the edges. """
    size = SCREEN.get_width() / 32
    surface = pygame.Surface((size, size))
    pygame.draw.rect(surface, BG_EDGE_COLOR, pygame.Rect(0, 0, size, size))
    pygame.draw.rect(surface, BG_MAIN_COLOR, pygame.Rect(1, 1, size - 2, size - 2))
    surface = pygame.transform.smoothscale(surface, (SCREEN.get_width(), SCREEN.get_height()))
    SCREEN.blit(surface, pygame.Rect(0, 0, SCREEN.get_width(), SCREEN.get_height()))

async def main():
    """ Handle the game loop. """
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
            if event.type == pygame.KEYDOWN:
                game.handle_input_key(event.key)
            if event.type == pygame.MOUSEBUTTONDOWN:
                game.handle_input_mouse_button(event.button)
            if event.type == TIMER:
                game.update()

        _draw_background()
        game.draw()
        pygame.display.update()
        await asyncio.sleep(0)

if __name__=="__main__":
    _check_sprites_size(sprites.main_sprites, SPRITE_SIZE, SPRITE_SIZE)
    _check_sprites_size(sprites.bonus_sprites, 2*SPRITE_SIZE, SPRITE_SIZE)
    _check_sprites_size(sprites.number_sprites, HUD_SPRITE_W, HUD_SPRITE_H)

    pygame.init()
    pygame.mixer.init()

    pygame.display.set_caption("Snake")
    pygame.display.set_icon(pygame.image.load("icon.png"))

    SCREEN_WIDTH  = CELL_WIDTH  * (LEVEL_WIDTH  + 2*SCREEN_BORDER)
    SCREEN_HEIGHT = CELL_HEIGHT * (LEVEL_HEIGHT + 2*SCREEN_BORDER + HUD_BAR)
    SCREEN = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

    buffer = np.sin(2 * np.pi * np.arange(44100) * 1760 / 44100).astype(np.float32)
    BEEP = pygame.mixer.Sound(buffer)

    TIMER = pygame.USEREVENT
    pygame.time.set_timer(TIMER, GAME_SPEED)

    game = Game()

    asyncio.run(main())
    