from copy import deepcopy
from heapq import heappush, heappop
import time
import argparse
import sys
import pdb

#====================================================================================

char_goal = '1'
char_single = '2'

class Piece:
    """
    This represents a piece on the Hua Rong Dao puzzle.
    """

    def __init__(self, is_goal, is_single, is_empty, coord_x, coord_y, orientation):
        """
        :param is_goal: True if the piece is the goal piece and False otherwise.
        :type is_goal: bool
        :param is_single: True if this piece is a 1x1 piece and False otherwise.
        :type is_single: bool
        :param coord_x: The x coordinate of the top left corner of the piece.
        :type coord_x: int
        :param coord_y: The y coordinate of the top left corner of the piece.
        :type coord_y: int
        :param orientation: The orientation of the piece (one of 'h' or 'v') 
            if the piece is a 1x2 piece. Otherwise, this is None
        :type orientation: str
        """

        self.is_goal = is_goal
        self.is_single = is_single
        self.is_empty = is_empty
        self.coord_x = coord_x
        self.coord_y = coord_y
        self.orientation = orientation

    def __repr__(self):
        return '{} {} {} {} {}'.format(self.is_goal, self.is_single, self.is_empty, \
            self.coord_x, self.coord_y, self.orientation)

    def __eq__(self, another):
        return self.is_goal == another.is_goal and self.is_single == another.is_single \
                and self.is_empty == another.is_empty and self.coord_x == another.coord_x \
                and self.coord_y == another.coord_y and self.orientation == another.orientation
    

class Board:
    """
    Board class for setting up the playing board.
    """

    def __init__(self, pieces):
        """
        :param pieces: The list of Pieces
        :type pieces: List[Piece]
        """

        self.width = 4
        self.height = 5

        self.pieces = pieces

        # self.grid is a 2-d (size * size) array automatically generated
        # using the information on the pieces when a board is being created.
        # A grid contains the symbol for representing the pieces on the board.
        self.grid = []
        self.__construct_grid() 

    def __hash__(self):
        return hash(self.grid.__repr__())
    


    def __construct_grid(self):
        """
        Called in __init__ to set up a 2-d grid based on the piece location information.

        """

        for i in range(self.height):
            line = []
            for j in range(self.width):
                line.append('.') # every slots are empty
            self.grid.append(line)

        for piece in self.pieces:
            if piece.is_goal:
                self.grid[piece.coord_y][piece.coord_x] = char_goal
                self.grid[piece.coord_y][piece.coord_x + 1] = char_goal
                self.grid[piece.coord_y + 1][piece.coord_x] = char_goal
                self.grid[piece.coord_y + 1][piece.coord_x + 1] = char_goal
            elif piece.is_single:
                self.grid[piece.coord_y][piece.coord_x] = char_single
            else:
                if piece.orientation == 'h':
                    self.grid[piece.coord_y][piece.coord_x] = '<'
                    self.grid[piece.coord_y][piece.coord_x + 1] = '>'
                elif piece.orientation == 'v':
                    self.grid[piece.coord_y][piece.coord_x] = '^'
                    self.grid[piece.coord_y + 1][piece.coord_x] = 'v'


    def display(self):
        """
        Print out the current board.

        """
        for i, line in enumerate(self.grid):
            for ch in line:
                print(ch, end='')
            print() # endl
    
    def string_display(self):
        result = ""
        for i, line in enumerate(self.grid):
            for ch in line:
                result += ch
            result += '\n'
        result += '\n'
        return result
        

class State:
    """
    State class wrapping a Board with some extra current state information.
    Note that State and Board are different. Board has the locations of the pieces. 
    State has a Board and some extra information that is relevant to the search: 
    heuristic function, f value, current depth and parent.
    """

    def __init__(self, board, f, depth, parent=None):
        """
        :param board: The board of the state.
        :type board: Board
        :param f: The f value of current state.
        :type f: int
        :param depth: The depth of current state in the search tree.
        :type depth: int
        :param parent: The parent of current state.
        :type parent: Optional[State]
        """
        self.board = board
        self.f = f
        self.depth = depth
        self.parent = parent
        self.empty = self.get_empty()
        self.goal = self.get_goal()
        self.id = hash(board)  # The id for breaking ties.

    def get_empty(self):
        empty_slots = []
        for piece in self.board.pieces:
            if(piece.is_empty):
                empty_slots.append(piece)
        return empty_slots
    
    def get_goal(self):
        for piece in self.board.pieces:
            if(piece.is_goal):
                return piece
    
    def __lt__(self, another):
        return self.f < another.f


def read_from_file(filename):
    """
    Load initial board from a given file.

    :param filename: The name of the given file.
    :type filename: str
    :return: A loaded board
    :rtype: Board
    """

    puzzle_file = open(filename, "r")

    line_index = 0
    pieces = []
    g_found = False

    for line in puzzle_file:

        for x, ch in enumerate(line):

            if ch == '^': # found vertical piece
                pieces.append(Piece(False, False, False, x, line_index, 'v'))
            elif ch == '<': # found horizontal piece
                pieces.append(Piece(False, False, False, x, line_index, 'h'))
            elif ch == '.':
                pieces.append(Piece(False, False, True, x, line_index, None))
            elif ch == char_single:
                pieces.append(Piece(False, True, False, x, line_index, None))
            elif ch == char_goal:
                if g_found == False:
                    pieces.append(Piece(True, False, False, x, line_index, None))
                    g_found = True
        line_index += 1

    puzzle_file.close()

    board = Board(pieces)
    
    return board

def goal_test(state):
    for piece in state.board.pieces:
        if (piece.is_goal and piece.coord_x == 1 and piece.coord_y == 3):
            return True
    return False

def get_solution(state):
    result = ""
    allStates = list()
    solution_depth = state.depth
    while (state.parent):
        allStates.append(state)
        state = state.parent
    
    allStates.append(state)
    for i in reversed(allStates):
        result += i.board.string_display()
    return result

def gen_successors(state):
    new_states = []
    for piece in state.board.pieces:
        if piece.is_single:
            if (Piece(False, False, True, piece.coord_x, piece.coord_y - 1, None) in state.empty):
                copy_pieces = deepcopy(state.board.pieces)
                copy_pieces.remove(piece)
                copy_pieces.remove(Piece(False, False, True, piece.coord_x, piece.coord_y - 1, None))

                copy_pieces.append(Piece(False, True, False, piece.coord_x, piece.coord_y - 1, None))
                copy_pieces.append(Piece(False, False, True, piece.coord_x, piece.coord_y, None))
                new_board = Board(copy_pieces)
                new_state = State(new_board, 0, state.depth + 1, state)
                new_state.f = manhattan(new_state) + state.depth + 1
                new_states.append(new_state)
            
            if (Piece(False, False, True, piece.coord_x, piece.coord_y + 1, None) in state.empty):
                copy_pieces = deepcopy(state.board.pieces)
                copy_pieces.remove(piece)
                copy_pieces.remove(Piece(False, False, True, piece.coord_x, piece.coord_y + 1, None))

                copy_pieces.append(Piece(False, True, False, piece.coord_x, piece.coord_y + 1, None))
                copy_pieces.append(Piece(False, False, True, piece.coord_x, piece.coord_y, None))
                new_board = Board(copy_pieces)
                new_state = State(new_board, 0, state.depth + 1, state)
                new_state.f = manhattan(new_state) + state.depth + 1                
                new_states.append(new_state)
            
            if (Piece(False, False, True, piece.coord_x - 1, piece.coord_y, None) in state.empty):
                copy_pieces = deepcopy(state.board.pieces)
                copy_pieces.remove(piece)
                copy_pieces.remove(Piece(False, False, True, piece.coord_x - 1, piece.coord_y, None))

                copy_pieces.append(Piece(False, True, False, piece.coord_x - 1, piece.coord_y, None))
                copy_pieces.append(Piece(False, False, True, piece.coord_x, piece.coord_y, None))
                new_board = Board(copy_pieces)
                new_state = State(new_board, 0, state.depth + 1, state)
                new_state.f = manhattan(new_state) + state.depth + 1                
                new_states.append(new_state)
            
            if (Piece(False, False, True, piece.coord_x + 1, piece.coord_y, None) in state.empty):
                # pdb.set_trace()
                copy_pieces = deepcopy(state.board.pieces)
                copy_pieces.remove(piece)
                copy_pieces.remove(Piece(False, False, True, piece.coord_x + 1, piece.coord_y, None))

                copy_pieces.append(Piece(False, True, False, piece.coord_x + 1, piece.coord_y, None))
                copy_pieces.append(Piece(False, False, True, piece.coord_x, piece.coord_y, None))
                new_board = Board(copy_pieces)
                new_state = State(new_board, 0, state.depth + 1, state)
                new_state.f = manhattan(new_state) + state.depth + 1                
                new_states.append(new_state)


    
        elif piece.is_goal:
            if (Piece(False, False, True, piece.coord_x, piece.coord_y - 1, None) in state.empty 
                    and Piece(False, False, True, piece.coord_x + 1, piece.coord_y - 1, None) in state.empty):
                copy_pieces = deepcopy(state.board.pieces)
                copy_pieces.remove(piece)
                copy_pieces.remove(Piece(False, False, True, piece.coord_x, piece.coord_y - 1, None))
                copy_pieces.remove(Piece(False, False, True, piece.coord_x + 1, piece.coord_y - 1, None))

                copy_pieces.append(Piece(True, False, False, piece.coord_x, piece.coord_y - 1, None))
                copy_pieces.append(Piece(False, False, True, piece.coord_x, piece.coord_y + 1, None))
                copy_pieces.append(Piece(False, False, True, piece.coord_x + 1, piece.coord_y + 1, None))

                new_board = Board(copy_pieces)
                new_state = State(new_board, 0, state.depth + 1, state)
                new_state.f = manhattan(new_state) + state.depth + 1                
                new_states.append(new_state)
            
            if (Piece(False, False, True, piece.coord_x, piece.coord_y + 2, None) in state.empty
                    and Piece(False, False, True, piece.coord_x + 1, piece.coord_y + 2, None) in state.empty):
                copy_pieces = deepcopy(state.board.pieces)
                copy_pieces.remove(piece)
                copy_pieces.remove(Piece(False, False, True, piece.coord_x, piece.coord_y + 2, None))
                copy_pieces.remove(Piece(False, False, True, piece.coord_x + 1, piece.coord_y + 2, None))

                copy_pieces.append(Piece(True, False, False, piece.coord_x, piece.coord_y + 1, None))
                copy_pieces.append(Piece(False, False, True, piece.coord_x, piece.coord_y, None))
                copy_pieces.append(Piece(False, False, True, piece.coord_x + 1, piece.coord_y, None))

                new_board = Board(copy_pieces)
                new_state = State(new_board, 0, state.depth + 1, state)
                new_state.f = manhattan(new_state) + state.depth + 1                
                new_states.append(new_state)
            
            if (Piece(False, False, True, piece.coord_x - 1, piece.coord_y, None) in state.empty
                    and Piece(False, False, True, piece.coord_x - 1, piece.coord_y + 1, None) in state.empty):
                copy_pieces = deepcopy(state.board.pieces)
                copy_pieces.remove(piece)
                copy_pieces.remove(Piece(False, False, True, piece.coord_x - 1, piece.coord_y, None))
                copy_pieces.remove(Piece(False, False, True, piece.coord_x - 1, piece.coord_y + 1, None))

                copy_pieces.append(Piece(True, False, False, piece.coord_x - 1, piece.coord_y, None))
                copy_pieces.append(Piece(False, False, True, piece.coord_x + 1, piece.coord_y, None))
                copy_pieces.append(Piece(False, False, True, piece.coord_x + 1, piece.coord_y + 1, None))

                new_board = Board(copy_pieces)
                new_state = State(new_board, 0, state.depth + 1, state)
                new_state.f = manhattan(new_state) + state.depth + 1                
                new_states.append(new_state)
            
            if (Piece(False, False, True, piece.coord_x + 2, piece.coord_y, None) in state.empty
                    and Piece(False, False, True, piece.coord_x + 2, piece.coord_y + 1, None) in state.empty):
                
                copy_pieces = deepcopy(state.board.pieces)
                copy_pieces.remove(piece)
                copy_pieces.remove(Piece(False, False, True, piece.coord_x + 2, piece.coord_y, None))
                copy_pieces.remove(Piece(False, False, True, piece.coord_x + 2, piece.coord_y + 1, None))

                copy_pieces.append(Piece(True, False, False, piece.coord_x + 1, piece.coord_y, None))
                copy_pieces.append(Piece(False, False, True, piece.coord_x, piece.coord_y, None))
                copy_pieces.append(Piece(False, False, True, piece.coord_x, piece.coord_y + 1, None))

                new_board = Board(copy_pieces)
                new_state = State(new_board, 0, state.depth + 1, state)
                new_state.f = manhattan(new_state) + state.depth + 1                
                new_states.append(new_state)

        
        elif piece.orientation == 'h':
            if (Piece(False, False, True, piece.coord_x, piece.coord_y - 1, None) in state.empty 
                    and Piece(False, False, True, piece.coord_x + 1, piece.coord_y - 1, None) in state.empty):
                # pdb.set_trace()
                copy_pieces = deepcopy(state.board.pieces)
                copy_pieces.remove(piece)
                copy_pieces.remove(Piece(False, False, True, piece.coord_x, piece.coord_y - 1, None))
                copy_pieces.remove(Piece(False, False, True, piece.coord_x + 1, piece.coord_y - 1, None))

                copy_pieces.append(Piece(False, False, False, piece.coord_x, piece.coord_y - 1, 'h'))
                copy_pieces.append(Piece(False, False, True, piece.coord_x, piece.coord_y, None))
                copy_pieces.append(Piece(False, False, True, piece.coord_x + 1, piece.coord_y, None))

                new_board = Board(copy_pieces)
                new_state = State(new_board, 0, state.depth + 1, state)
                new_state.f = manhattan(new_state) + state.depth + 1                
                new_states.append(new_state)
            
            if (Piece(False, False, True, piece.coord_x, piece.coord_y + 1, None) in state.empty
                    and Piece(False, False, True, piece.coord_x + 1, piece.coord_y + 1, None) in state.empty):
                copy_pieces = deepcopy(state.board.pieces)
                copy_pieces.remove(piece)
                copy_pieces.remove(Piece(False, False, True, piece.coord_x, piece.coord_y + 1, None))
                copy_pieces.remove(Piece(False, False, True, piece.coord_x + 1, piece.coord_y + 1, None))

                copy_pieces.append(Piece(False, False, False, piece.coord_x, piece.coord_y + 1, 'h'))
                copy_pieces.append(Piece(False, False, True, piece.coord_x, piece.coord_y, None))
                copy_pieces.append(Piece(False, False, True, piece.coord_x + 1, piece.coord_y, None))

                new_board = Board(copy_pieces)
                new_state = State(new_board, 0, state.depth + 1, state)
                new_state.f = manhattan(new_state) + state.depth + 1                
                new_states.append(new_state)
            
            if (Piece(False, False, True, piece.coord_x - 1, piece.coord_y, None) in state.empty):
                copy_pieces = deepcopy(state.board.pieces)
                copy_pieces.remove(piece)
                copy_pieces.remove(Piece(False, False, True, piece.coord_x - 1, piece.coord_y, None))

                copy_pieces.append(Piece(False, False, False, piece.coord_x - 1, piece.coord_y, 'h'))
                copy_pieces.append(Piece(False, False, True, piece.coord_x + 1, piece.coord_y, None))

                new_board = Board(copy_pieces)
                new_state = State(new_board, 0, state.depth + 1, state)
                new_state.f = manhattan(new_state) + state.depth + 1                
                new_states.append(new_state)
            
            if (Piece(False, False, True, piece.coord_x + 2, piece.coord_y, None) in state.empty):
                copy_pieces = deepcopy(state.board.pieces)
                copy_pieces.remove(piece)
                copy_pieces.remove(Piece(False, False, True, piece.coord_x + 2, piece.coord_y, None))

                copy_pieces.append(Piece(False, False, False, piece.coord_x + 1, piece.coord_y, 'h'))
                copy_pieces.append(Piece(False, False, True, piece.coord_x, piece.coord_y, None))

                new_board = Board(copy_pieces)
                new_state = State(new_board, 0, state.depth + 1, state)
                new_state.f = manhattan(new_state) + state.depth + 1                
                new_states.append(new_state)
        

        



        elif piece.orientation == 'v':
            if (Piece(False, False, True, piece.coord_x, piece.coord_y - 1, None) in state.empty):
                copy_pieces = deepcopy(state.board.pieces)
                copy_pieces.remove(piece)
                copy_pieces.remove(Piece(False, False, True, piece.coord_x, piece.coord_y - 1, None))

                copy_pieces.append(Piece(False, False, False, piece.coord_x, piece.coord_y - 1, 'v'))
                copy_pieces.append(Piece(False, False, True, piece.coord_x, piece.coord_y + 1, None))

                new_board = Board(copy_pieces)
                new_state = State(new_board, 0, state.depth + 1, state)
                new_state.f = manhattan(new_state) + state.depth + 1                
                new_states.append(new_state)
            
            if (Piece(False, False, True, piece.coord_x, piece.coord_y + 2, None) in state.empty):
                copy_pieces = deepcopy(state.board.pieces)
                copy_pieces.remove(piece)
                copy_pieces.remove(Piece(False, False, True, piece.coord_x, piece.coord_y + 2, None))

                copy_pieces.append(Piece(False, False, False, piece.coord_x, piece.coord_y + 1, 'v'))
                copy_pieces.append(Piece(False, False, True, piece.coord_x, piece.coord_y, None))

                new_board = Board(copy_pieces)
                new_state = State(new_board, 0, state.depth + 1, state)
                new_state.f = manhattan(new_state) + state.depth + 1                
                new_states.append(new_state)
            
            if (Piece(False, False, True, piece.coord_x - 1, piece.coord_y, None) in state.empty
                    and Piece(False, False, True, piece.coord_x - 1, piece.coord_y + 1, None) in state.empty):
                copy_pieces = deepcopy(state.board.pieces)
                copy_pieces.remove(piece)
                copy_pieces.remove(Piece(False, False, True, piece.coord_x - 1, piece.coord_y, None))
                copy_pieces.remove(Piece(False, False, True, piece.coord_x - 1, piece.coord_y + 1, None))


                copy_pieces.append(Piece(False, False, False, piece.coord_x - 1, piece.coord_y, 'v'))
                copy_pieces.append(Piece(False, False, True, piece.coord_x, piece.coord_y, None))
                copy_pieces.append(Piece(False, False, True, piece.coord_x, piece.coord_y + 1, None))

                new_board = Board(copy_pieces)
                new_state = State(new_board, 0, state.depth + 1, state)
                new_state.f = manhattan(new_state) + state.depth + 1                
                new_states.append(new_state)
            
            if (Piece(False, False, True, piece.coord_x + 1, piece.coord_y, None) in state.empty
                    and Piece(False, False, True, piece.coord_x + 1, piece.coord_y + 1, None) in state.empty):
                copy_pieces = deepcopy(state.board.pieces)
                copy_pieces.remove(piece)
                copy_pieces.remove(Piece(False, False, True, piece.coord_x + 1, piece.coord_y, None))
                copy_pieces.remove(Piece(False, False, True, piece.coord_x + 1, piece.coord_y + 1, None))


                copy_pieces.append(Piece(False, False, False, piece.coord_x + 1, piece.coord_y, 'v'))
                copy_pieces.append(Piece(False, False, True, piece.coord_x, piece.coord_y, None))
                copy_pieces.append(Piece(False, False, True, piece.coord_x, piece.coord_y + 1, None))

                new_board = Board(copy_pieces)
                new_state = State(new_board, 0, state.depth + 1, state)
                new_state.f = manhattan(new_state) + state.depth + 1                
                new_states.append(new_state)
    return new_states
            
            

def dfs(initial_state, gen_successors, goal_test):
    frontier = [initial_state]
    explored = []
    states = 0
    while (len(frontier) > 0):
        states += 1
        curr = frontier.pop()
        if (curr.id not in explored):
            explored.append(curr.id)
            if (goal_test(curr)):
                print(states + len(frontier))
                return curr
            new_state = gen_successors(curr)
            for i in range(len(new_state)):
                frontier.append(new_state[i])
    return None

def manhattan(state):
    return abs(state.goal.coord_x - 1) + abs(state.goal.coord_y - 3)


def advanced(state):
    top_left = state.board.grid[3][1]
    top_right = state.board.grid[3][2]
    bot_left = state.board.grid[4][1]
    bot_right = state.board.grid[4][2]
    if (top_left != char_goal and top_left != '.' or
        top_right != char_goal and top_right != '.' or
        bot_left != char_goal and bot_left != '.' or
        bot_right != char_goal and bot_right != '.'):
        
        return manhattan(state) + 1
    else:
        return manhattan(state)
        


    

def astar(initial_state, gen_successors, goal_test):
    frontier = [initial_state]
    explored = []
    states = 0
    while(len(frontier) > 0):
        states += 1
        curr = heappop(frontier)
        if (curr.id not in explored):
            explored.append(curr.id)
            if(goal_test(curr)):
                print(states + len(frontier))
                return curr
            new_states = gen_successors(curr)
            for i in range(len(new_states)):
                heappush(frontier, new_states[i])
    return None
        

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--inputfile",
        type=str,
        required=True,
        help="The input file that contains the puzzle."
    )
    parser.add_argument(
        "--outputfile",
        type=str,
        required=False,
        help="The output file that contains the solution."
    )
    parser.add_argument(
        "--algo",
        type=str,
        required=True,
        choices=['astar', 'dfs'],
        help="The searching algorithm."
    )
    args = parser.parse_args()
    # read the board from the file
    board = read_from_file(args.inputfile)
    f = open(args.outputfile, "w")

    algoSearch = args.algo
    initial_state = State(board, 0, 0, [])
    initial_state.f = manhattan(initial_state) + initial_state.depth
    if (algoSearch == 'dfs'):
        result = dfs(initial_state, gen_successors, goal_test)
        if (result != None):
            f.write(get_solution(result))
        else:
            f.write("No solution found!")
    elif (algoSearch == 'astar'):
        result = astar(initial_state, gen_successors, goal_test)
        if (result != None):
            f.write(get_solution(result))
        else:
            f.write("No solution found!")
    f.close()
    


