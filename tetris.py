import pygame
import random 
from sys import exit

pygame.init()

SCREEN_WIDTH, SCREEN_HEIGHT = 800, 900
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption('Tetris')
clock = pygame.time.Clock()

BLACK = (0,0,0)
WHITE = (255,255,255)
GREY = (20,20,20)
RED = (255,0,0)
GREEN = (0,255,0)
BLUE = (0,0,255)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
PURPLE = (90, 60, 200)
CYAN = (0, 255, 255)

large_font = pygame.font.SysFont('consolas', 50)
small_font = pygame.font.SysFont('consolas', 20)

title_text = large_font.render('T E T R I S', 1, WHITE)
game_over_text = small_font.render('GAME OVER', 1, WHITE)
restart_prompt = small_font.render('Press [space] to restart', 1, WHITE)

# Dimensions of main box (where gameplay takes place) 
# Each block is made up 4 unit_positions
cell_size = 40
num_cols, num_rows = 10, 18
border_width = 5
box_width, box_height = num_cols * cell_size + 2 * border_width, num_rows * cell_size + 2 * border_width
hor_margin = (SCREEN_WIDTH - box_width)//2
ver_margin = (SCREEN_HEIGHT - box_height)//2

hold_box_width = 4 * cell_size + 2 * border_width
hold_box_margin = hor_margin//2 - hold_box_width//2

box = pygame.Rect(hor_margin, ver_margin, box_width, box_height)
hold_box = pygame.Rect(hold_box_margin, ver_margin, hold_box_width, hold_box_width)

# Data grid represents which spaces in the box are filled by blocks and which are not
# 0: empty; 1: filled
def create_data_grid():
    data_grid = []
    for row_num in range(num_rows):
        row = [0 for col_num in range(num_cols)]
        data_grid.append(row)
    return data_grid


class Block():
    colors = [PURPLE, GREEN, RED, BLUE, ORANGE, YELLOW, CYAN]

    # Each block is made up of 4 unit_positions, each of which has a specific pos in the grid
    def __init__(self):
        self.unit_positions = self.get_unit_positions(self.rotation_state)

    # Determine position of each of the block's 4 units in the grid
    def get_unit_positions(self, rotation_state):
        x, y = self.x, self.y
        # Each block has a bounding box within which they can rotate
        # cell_positions is a matrix representing position of each cell in the bounding box, 
        # regardless of whether the cell is occupied in the currrent rotation state
        cell_positions = [[(y + row, x + col) for col in range(len(rotation_state[0]))] for row in range(len(rotation_state))]

        unit_positions = []
        for row in range(len(rotation_state)):
            for col in range(len(rotation_state[0])):
                if rotation_state[row][col] != 0:
                    unit_positions.append(cell_positions[row][col])
        return unit_positions
    
    def rotate(self, grid):
        target_rotation_state = []
        for col in range(len(self.rotation_state[0])):
            new_row = [self.rotation_state[row][col] for row in range(len(self.rotation_state)-1, -1, -1)]
            target_rotation_state.append(new_row)
        
        # Check if it is possible to change the current rotation state to the target rotation state
        # Target positions: new positions of each of the block's units if the rotation is successfully performed
        # Check if all target positions are available i.e. all positions are within boundaries of grid and 
        # all corresponding grid cells are empty
        target_positions = self.get_unit_positions(target_rotation_state)

        can_rotate = all(0 <= pos[1] < num_cols for pos in target_positions) and all(grid[pos[0]][pos[1]] == 0 for pos in target_positions)
   
        if can_rotate:
            self.rotation_state = target_rotation_state
            self.unit_positions = target_positions
        # If cannot perform normal in-place rotation, try wall kick, 
        # if also cannot perform wall kick, then don't rotate
        else:
            can_move_left = self.can_move_left(target_positions, grid)
            can_move_right = self.can_move_right(target_positions, grid)

            # Kick left
            if can_move_left:
                self.rotation_state = target_rotation_state
                self.unit_positions = target_positions
                self.move_left()

            # Kick right
            elif can_move_right:
                self.rotation_state = target_rotation_state
                self.unit_positions = target_positions
                self.move_right()

    def can_move_left(self, unit_positions, grid):
        for unit_pos in unit_positions: # Check that all 4 unit_positions in the block can move left
            # Already at leftmost column; cannot move further
            # Or destination position is occupied
            if unit_pos[1] <= 0 or grid[unit_pos[0]][unit_pos[1] - 1] != 0: 
                return False
        return True
    
    def move_left(self):    
        # Move block to the left, unit by unit
        for i, unit_pos in enumerate(self.unit_positions):
            new_unit_pos = (unit_pos[0], unit_pos[1] - 1)
            self.unit_positions[i] = new_unit_pos
        self.x -= 1

    def can_move_right(self, unit_positions, grid):
        for unit_pos in unit_positions: # Check that all 4 unit_positions in the block can move right
            # Already at rightmost column; cannot move further
            # Or destination position is occupied
            if unit_pos[1] >= num_cols - 1 or grid[unit_pos[0]][unit_pos[1] + 1] != 0: 
                return False
        return True
    
    def move_right(self):
        # Move block to the right, unit by unit
        for i, unit_pos in enumerate(self.unit_positions):
            new_unit_pos = (unit_pos[0], unit_pos[1] + 1)
            self.unit_positions[i] = new_unit_pos
        self.x += 1

    def can_descend(self, grid):
        for unit_pos in self.unit_positions: # Reached bottom or destination position is occupied
            if unit_pos[0] >= num_rows - 1: 
                return False
            elif grid[unit_pos[0] + 1][unit_pos[1]] != 0:
                return False
        return True

    # If can descend, then descend
    def soft_drop(self):
        for i, unit_pos in enumerate(self.unit_positions):
            new_unit_pos = (unit_pos[0] + 1, unit_pos[1])
            self.unit_positions[i] = new_unit_pos
        self.y += 1

    # Block will keep moving down until it hits an obstacle i.e. the bottom or another block
    def hard_drop(self, grid):
        while self.can_descend(grid): 
            for i, unit_pos in enumerate(self.unit_positions):
                new_unit_pos = (unit_pos[0] + 1, unit_pos[1])
                self.unit_positions[i] = new_unit_pos
            self.y += 1

    # Lock the block in the grid; it can no longer be controlled by the player
    def lock(self, grid):
        for unit_pos in self.unit_positions:
            grid[unit_pos[0]][unit_pos[1]] = self.id # Update current position of block in the grid


class T_Block(Block):
    def __init__(self):
        self.id = 1
        self.x, self.y = 3, 0 # (x,y) : position of top_left unit in rotation_state
        self.rotation_state = [[0,1,0],
                               [1,1,1],
                               [0,0,0]]
        super().__init__()

class S_Block(Block):
   def __init__(self):
        self.id = 2
        self.x, self.y = 3, 0
        self.rotation_state = [[0,1,1],
                               [1,1,0],
                               [0,0,0]]
        super().__init__()

class Z_Block(Block):
    def __init__(self):
        self.id = 3
        self.x, self.y = 3, 0
        self.rotation_state = [[1,1,0],
                               [0,1,1],
                               [0,0,0]]
        super().__init__()

class J_Block(Block):
    def __init__(self):
        self.id = 4
        self.x, self.y = 3, 0
        self.rotation_state = [[1,0,0],
                               [1,1,1],
                               [0,0,0]]
        super().__init__()

class L_Block(Block):
    def __init__(self):
        self.id = 5
        self.x, self.y = 3, 0
        self.rotation_state = [[0,0,1],
                               [1,1,1],
                               [0,0,0]]
        super().__init__()

class O_Block(Block):
    def __init__(self):
        self.id = 6
        self.x, self.y = 4, 0
        self.rotation_state = [[1,1],
                               [1,1]]
        super().__init__()

class I_Block(Block):
    def __init__(self):
        self.id = 7
        self.x, self.y = 3, 0
        self.rotation_state = [[0,0,0,0],
                               [1,1,1,1],
                               [0,0,0,0],
                               [0,0,0,0]]
        super().__init__()


def clear_lines(grid):
    new_grid = [row for row in grid if not all(row)] # If line is not completely filled, insert it to new grid
    lines_cleared = num_rows - len(new_grid)
    empty_line = [0 for _ in range(num_cols)]
    for _ in range(lines_cleared):
        new_grid.insert(0, empty_line)
    return (new_grid, lines_cleared) 


def draw_grid(grid):
    # Draw row by row starting from top row
    for row in range(num_rows):
        for col in range(num_cols):
            cell = pygame.Rect(box.x + border_width + col * cell_size, box.y + border_width + row * cell_size, cell_size, cell_size) 
            
            if grid[row][col] != 0: # Occupied
                pygame.draw.rect(screen, Block.colors[grid[row][col] - 1], cell)
            
            pygame.draw.rect(screen, GREY, cell, 1)
                

def draw_active_block(block):
    for unit_pos in block.unit_positions:
        unit = pygame.Rect(box.x + border_width + unit_pos[1] * cell_size, box.y + border_width + unit_pos[0] * cell_size, cell_size, cell_size) 
        pygame.draw.rect(screen, Block.colors[block.id - 1], unit)
        pygame.draw.rect(screen, GREY, unit, 1)


def draw_held_block(held_block):
    if not held_block:
        return
    block = held_block()
    for row in range(len(block.rotation_state)):
        for col in range(len(block.rotation_state[0])):
            if block.rotation_state[row][col] != 0:
                unit = pygame.Rect(hold_box_margin + border_width + col * cell_size, box.y + row * cell_size, cell_size, cell_size)
                pygame.draw.rect(screen, Block.colors[block.id - 1], unit)
                pygame.draw.rect(screen, GREY, unit, 1)


def draw_constants():
    # Draw main box
    pygame.draw.rect(screen, WHITE, box, border_width)
    # Draw hold box
    pygame.draw.rect(screen, WHITE, hold_box, border_width)
    # Draw next box
    # Draw text  
    screen.blit(title_text, (SCREEN_WIDTH//2 - title_text.get_width()//2, ver_margin//2 - title_text.get_height()//2))


def draw_game_over():
    screen.blit(game_over_text, (SCREEN_WIDTH//2 - game_over_text.get_width()//2, SCREEN_HEIGHT//2 - game_over_text.get_height()//2))
    screen.blit(restart_prompt, (SCREEN_WIDTH//2 - restart_prompt.get_width()//2, SCREEN_HEIGHT//2 + game_over_text.get_height()//2))


# Block descends 1 cell every {descent interval} milliseconds
descent_timer = pygame.USEREVENT + 1
descent_interval = 1000
pygame.time.set_timer(descent_timer, descent_interval)

block_types = [T_Block, S_Block, Z_Block, J_Block, L_Block, O_Block, I_Block]
line_clears = ['SINGLE', 'DOUBLE', 'TRIPLE', 'TETRIS']


def main():
    game_state = 1
    grid = create_data_grid()
    active_block_exists = False

    next_bag = []
    current_bag = random.sample(block_types, k = len(block_types))

    held_block = None

    level = 0
    combo = 0
    score = 0

    while True:
        screen.fill(BLACK)
        draw_grid(grid)
        draw_held_block(held_block)
        draw_constants()

        if active_block_exists:
            draw_active_block(block)

        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

        if game_state == 1:
            
            # Block spawning
            if not active_block_exists:
                block_type = current_bag.pop() 
                block = block_type()
                
                # Game over if newly spawned block cannot descend further, 
                # i.e. the top row is occupied
                if not block.can_descend(grid):
                    game_state = 2
                    continue

                active_block_exists = True

                # Each new block can only be swapped once
                # With each new block spawned, the 'swap count' will reset
                swapped = False

                if len(next_bag) == 0:
                    next_bag = random.sample(block_types, k = len(block_types))
                current_bag.insert(0, next_bag.pop())

            for event in events:
                # Passively descend by 1 cell at specified intervals
                if event.type == descent_timer:
                    block.soft_drop()
                
                if event.type == pygame.KEYDOWN:
                    # Move left and right
                    if event.key == pygame.K_LEFT and block.can_move_left(block.unit_positions, grid):
                        block.move_left()
                    if event.key == pygame.K_RIGHT and block.can_move_right(block.unit_positions, grid):
                        block.move_right()
                    
                    # Rotate    
                    if event.key == pygame.K_UP:
                        block.rotate_clockwise(grid)

                    # Soft-drop
                    if event.key == pygame.K_DOWN and block.can_descend(grid):
                        block.soft_drop()

                    # Hard-drop
                    if event.key == pygame.K_SPACE:
                        block.hard_drop(grid)
                    
                    # Hold
                    if event.key == pygame.K_c and not swapped:
                        if held_block: # Swap current block with held block
                            block, held_block = held_block(), block_types[block.id - 1] 
                        
                        else: # If there is nothing being held (only possible at start of game)
                            held_block = block_types[block.id - 1]
                            block_type = current_bag.pop() # class
                            block = block_type() # instance
                            current_bag.insert(0, next_bag.pop())

                        swapped = True
            
            # Current active block has landed and will now be locked
            # Clear any completed lines
            if not block.can_descend(grid):
                block.lock(grid)
                grid, lines_cleared = clear_lines(grid)
                
                del block
                active_block_exists = False
                
                # Scoring
                if lines_cleared > 0:
                    combo += 1
                else:
                    combo = 0


        if game_state == 2:
            draw_game_over()
            for event in events:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    main()
        
        pygame.display.update()
        clock.tick(60)


if __name__ == '__main__':
    main()