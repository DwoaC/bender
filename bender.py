'''
Solution to Bender puzzle on CodinGame.com

The [Bender](https://www.codingame.com/training/medium/bender-episode-1)
puzzle Futurama's Bender wanders around a 2D board from a goal to
a target.  Various obstacles force Bender to move in certain ways or
restrict your options for a move.

Your goal is to write a program that directs Bender to the goal.

Your input is the board state in a list of lists (l and c in the code.

The output should be a list of moves that gets Bender to the goal
without breaking any of the rules.

The solution here is very straight forward evaluation of Benders
constraints, current state, and the best possible move.

Forgive the print statements, the site insists you use them rather
than logging.
'''

import sys
from collections import namedtuple

Direction = namedtuple('Direction', ['x', 'y'])

priorities = ['s', 'e', 'n', 'w']
directions = {'w': Direction(0, -1),
              'n': Direction(-1, 0),
              'e': Direction(0, 1),
              's': Direction(1, 0),
              }
BENDER_CHAR = '@'
BOOTH_CHAR = '$'
INVERTER_CHAR = 'I'
BEER_CHAR = 'B'
OBSTACLE_BREAKABLE = 'X'
OBSTACLE_UNBREAKABLE = '#'
TELEPORT_CHAR = 'T'
TIMEOUT = 8000

DIRECTION_LONG_NAMES = {
    'n': 'NORTH',
    's': 'SOUTH',
    'e': 'EAST',
    'w': 'WEST'
}


class BenderException(Exception):
    pass


class BenderObstacle(BenderException):
    pass

class BenderTrapped(BenderException):
    pass

class Bender:
    def __init__(self, rows):
        '''
        Represents Bender on the board.

        >>> board = [['#', '#', '#', '#', '#'],
        >>>          ['#', '@', ' ', ' ', '#'],
        >>>          ['#', ' ', ' ', ' ', '#'],
        >>>          ['#', ' ', ' ', '$', '#'],
        >>>          ['#', '#', '#', '#', '#']]
        >>> bender = Bender(board)
        >>> bender
        <bender.Bender object at 0x10f72c9e8>

        >>> bender.go()
        Getting cell " " @ 2, 1 in direction s
        Checking for obstacle. Direction: s, Cell: " ", obstacles: #X
        Moving in direction: s
            New location is 2, 1

        >>> bender.finished
        False

        >>> while not bender.finished:
        >>>     bender.go()
        Getting cell " " @ 3, 1 in direction s
        Checking for obstacle. Direction: s, Cell: " ", obstacles: #X
        Moving in direction: s
            New location is 3, 1
        Getting cell "#" @ 4, 1 in direction s
        Checking for obstacle. Direction: s, Cell: "#", obstacles: #X
        Moving in direction s failed.  Trying priorities.
        Getting cell "#" @ 4, 1 in direction s
        Checking for obstacle. Direction: s, Cell: "#", obstacles: #X
        Getting cell " " @ 3, 2 in direction e
        Checking for obstacle. Direction: e, Cell: " ", obstacles: #X
        Moving in direction: e
            New location is 3, 2
        Getting cell "$" @ 3, 3 in direction e
        Checking for obstacle. Direction: e, Cell: "$", obstacles: #X
        Moving in direction: e
            New location is 3, 3

        >>> bender.finished
        True

        Bender has a few internal states that will change over the course
        of the game.
        1. Priorities - various obstacles change which direction Bender
        prefers to move in.
        2. Beer - when Bender picks up a beer he can ignore certain
        obstacles and even remove them from the Board.
        3. Board - the board can change in the course of the game.  Obstacles
        can be removed and forced directions can be changed.

        :param rows: (list of str) initial state of the board
        '''
        self.rows = rows
        self.x, self.y = self.get_initial_cell(rows)
        self.teleport = self.get_teleporters(rows)
        self.history = []
        self.current_direction = 's'
        self.priorities = priorities
        self.in_beer_state = False

    def get_teleporters(self, rows):
        '''
        Find all teleporters on the board.

        Teleporters appear in pairs on the board.  Moving on to one of the pair
        teleports you to the other cell in the pair.

        This builds a dict of the teleporters on the board.
        '''
        teleport_locations = []
        for row_index, row in enumerate(rows):
            for col_index, col in enumerate(row):
                if col == TELEPORT_CHAR:
                    teleport_locations.append((row_index, col_index))
        print('Teleporters: {}'.format(teleport_locations), file=sys.stderr)
        try:
            teleport_dict = dict((
                (teleport_locations[0], teleport_locations[1]),
                (teleport_locations[1], teleport_locations[0])))
        except:
            teleport_dict = None

        if teleport_dict is not None:
            print('Found a teleporter from {} to {}'.format(
                teleport_locations[0],
                teleport_locations[1]
            ), file=sys.stderr)

        return teleport_dict

    @property
    def obstacles(self):
        '''Get all possible obstacles.

        When in a bear state Bender can pass X obstacles.
        '''
        if self.in_beer_state:
            return '#'
        else:
            return '#X'

    def get_initial_cell(self, rows):
        for row_index, row in enumerate(rows):
            for col_index, col in enumerate(row):
                if BENDER_CHAR in col:
                    return row_index, col_index

    def go(self):
        '''
        Check current cell, benders state and move bender.
        '''
        self.check_current_cell()

        if self.on_forced_direction:
            self.move_in_forced_direction()
        elif not self.check_for_obstacle(self.current_direction):
            self.move(self.current_direction)
        else:
            print('Moving in direction {direction} failed.  Trying priorities.'.format(
                direction=self.current_direction),
                file=sys.stderr)
            self.move_via_priorities()

    def check_current_cell(self):
        self.check_beer()
        self.check_inverter()
        self.check_teleport()
        self.check_destroy_obstacle()

    def check_destroy_obstacle(self):
        if self.current_cell == OBSTACLE_BREAKABLE and self.in_beer_state:
            print('Destroying obstacle @ {}, {}'.format(self.x, self.y), file=sys.stderr)
            self.rows[self.x][self.y] = ' '

    def check_teleport(self):
        if self.current_cell == TELEPORT_CHAR:
            print('Teleporting from {} to {}'.format(
                (self.x, self.y),
                self.teleport[(self.x, self.y)]),
                file=sys.stderr)
            self.x, self.y = self.teleport[(self.x, self.y)]

    def check_beer(self):
        if self.current_cell == BEER_CHAR:
            self.in_beer_state = not self.in_beer_state

    def check_inverter(self):
        if self.current_cell == INVERTER_CHAR:
            print('Reversing priorities {} to {}'.format(
                self.priorities,
                list(reversed(self.priorities))),
                file=sys.stderr)
            self.priorities = list(reversed(self.priorities))

    @property
    def on_forced_direction(self):
        return self.current_cell.lower() in directions

    def move_in_forced_direction(self):
        self.move(self.current_cell.lower())

    def move_via_priorities(self):
        '''
        Decide the direction for Bender to move.

        Considers that Bender has a list of priorities for moving and picks
        the first valid direction to move in.
        '''
        for direction in self.priorities:
            if not self.check_for_obstacle(direction):
                return self.move(direction)
        raise BenderTrapped("Bender can't find a direction to move.")

    def move(self, compass):
        print('Moving in direction: {}'.format(compass), file=sys.stderr)

        x, y = directions[compass]
        self.x += x
        self.y += y
        self.history.append(DIRECTION_LONG_NAMES[compass])
        self.current_direction = compass
        print('\tNew location is {}, {}'.format(self.x, self.y), file=sys.stderr)

    @property
    def finished(self):
        if self.current_cell == BOOTH_CHAR:
            return True
        else:
            return len(self.history) > TIMEOUT

    def check_for_obstacle(self, compass):
        '''
        Returns True if an obstacle that can stop Bender is in the given direction.

        :param compass: (str) one of n, s, e, w
        :return: (bool) Can Bender move onto the cell
        '''
        cell = self.get_cell(compass)
        print(
            'Checking for obstacle. Direction: {direction}, Cell: "{cell}", obstacles: {obstacles}'.format(
                direction=compass,
                cell=cell,
                obstacles=self.obstacles),
            file=sys.stderr)
        return cell in self.obstacles

    def get_cell(self, compass):
        x, y = directions[compass]
        cell = self.rows[self.x + x][self.y + y]
        print('Getting cell "{cell}" @ {x}, {y} in direction {direction}'.format(
            x=self.x + x,
            y=self.y + y,
            direction=compass,
            cell=cell),
            file=sys.stderr)
        return cell

    @property
    def current_cell(self):
        return self.rows[self.x][self.y]

if __name__=='__main__':
    l, c = [int(i) for i in input().split()]
    rows = []
    for i in range(l):
        rows.append(list(input()))
        print(rows[-1], file=sys.stderr)
    print('', file=sys.stderr)

    bender = Bender(rows)
    # TODO: Bender should be a generator and use a for loop to move bender
    while not bender.finished:
        bender.go()
    if len(bender.history) >= TIMEOUT:
        print('LOOP')
    else:
        for h in bender.history:
            print(h)