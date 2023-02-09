""" Sprites for the Snake game """

food =         ((0, 1, 0, 0),
                (1, 0, 1, 0),
                (0, 1, 0, 0),
                (0, 0, 0, 0))

snake_head =   ((1, 0, 0, 0),
                (0, 1, 1, 0),
                (1, 1, 1, 0),
                (0, 0, 0, 0))

snake_mouth =  ((1, 0, 1, 0),
                (0, 1, 0, 0),
                (1, 1, 0, 0),
                (0, 0, 1, 0))

snake_body =   ((0, 0, 0, 0),
                (1, 1, 0, 1),
                (1, 0, 1, 1),
                (0, 0, 0, 0))

snake_full =   ((0, 1, 1, 0),
                (1, 1, 0, 1),
                (1, 0, 1, 1),
                (0, 1, 1, 0))

snake_turn =   ((0, 0, 0, 0),
                (0, 0, 1, 1),
                (0, 1, 0, 1),
                (0, 1, 1, 0))

snake_tail =   ((0, 0, 0, 0),
                (0, 0, 0, 1),
                (0, 1, 1, 1),
                (0, 0, 0, 0))

sprites_list = [food, snake_head, snake_mouth, snake_body, snake_full, snake_turn, snake_tail]
