#!/usr/bin/python  # Specifies the interpreter to execute the script

import sys  # Imports sys module for system-related functionalities
import json  # Imports json module to work with JSON data
import random  # Imports random module for random selections

import math
import heapq

class Cell:
    def __init__(self):
      # Parent cell's row index
        self.parent_i = 0
    # Parent cell's column index
        self.parent_j = 0
 # Total cost of the cell (g + h)
        self.f = float('inf')
    # Cost from start to this cell
        self.g = float('inf')
    # Heuristic cost from this cell to destination
        self.h = 0

# Checks Python version; imports appropriate socket server module based on version
if (sys.version_info > (3, 0)):
    print("Python 3.X detected")  # Indicates Python 3.X is in use
    import socketserver as ss  # Imports socketserver as ss for Python 3.X
else:
    print("Python 2.X detected")  # Indicates Python 2.X is in use
    import SocketServer as ss  # Imports SocketServer as ss for Python 2.X


class NetworkHandler(ss.StreamRequestHandler):  # Defines a network request handler
    def handle(self):  # Handles incoming client requests
        game = Game()  # Initializes a new game instance

        while True:  # Loop to continuously process client requests
            data = self.rfile.readline().decode()  # Reads data until newline character, then decodes
            json_data = json.loads(str(data))  # Parses the data into a JSON object
            # uncomment the following line to see pretty-printed data
            # print(json.dumps(json_data, indent=4, sort_keys=True))
            # response = game.get_random_move(json_data).encode()
            response = game.get_moves(json_data).encode()  # Gets moves based on JSON data, encodes as bytes
            self.wfile.write(response)  # Sends the response back to the client


class Unit:  # Class to represent individual units
    def __init__(self, config: dict) -> None:  # Constructor initializes unit properties
        self.id = config['id']  # Unit ID
        self.x = config['x']  # Unit x-coordinate
        self.y = config['y']  # Unit y-coordinate
        self.type = config['type']  # Type of the unit
        self.status = config['status']  # Status of the unit
        self.hp = config['health']  # Health points of the unit
        self.resource = config.get("resource", None)  # Optional resource attribute
        self.attack = config.get("can_attack", None)  # Optional attack capability


class Tile:  # Class to represent tiles in the game map
    def __init__(self, config: dict) -> None:  # Constructor initializes tile properties
        self.visible = config.get('visible', False)  # Tile visibility status
        self.x = config['x']  # Tile x-coordinate
        self.y = config['y']  # Tile y-coordinate
        self.blocked = config.get('blocked', False)  # Tile blockage status
        if config.get('resources', None):  # Checks if resources are present
            self.resources = Resource(config['resources'])  # Assigns resources if available
        else:
            self.resources = None  # Sets resources to None if absent
        self.units = []  # Initializes unit list on the tile
        if config.get('units', []):  # Checks if units are on the tile
            for unit in config['units']:  # Adds each unit to the tile's unit list
                self.units.append(Unit(unit))

    def update(self, config: dict):  # Updates tile properties with new data
        self.visible = config['visible']  # Updates visibility
        self.blocked = config.get('blocked', False)  # Updates blockage status
        if config.get('resources', None):  # Checks if resources are present
            self.resources = Resource(config['resources'])  # Updates resources if available
        else:
            self.resources = None  # Sets resources to None if absent
        self.units = []  # Clears existing units list
        if config.get('units', []):  # Checks if units are on the tile
            for unit in config['units']:  # Adds each unit to the tile's unit list
                self.units.append(Unit(unit))


class Resource:  # Class to represent resources on a tile
    def __init__(self, config: dict) -> None:  # Constructor initializes resource properties
        self.id = config['id']  # Resource ID
        self.type = config['type']  # Resource type
        self.total = config['total']  # Total quantity of the resource
        self.value = config['value']  # Value of the resource


class Game:  # Main class representing the game logic
    def __init__(self):  # Initializes game properties
        self.units = set()  # Set to store unique unit IDs
        self.directions = ['N', 'S', 'E', 'W']  # Possible movement directions
        self.tiles = []  # List to store game map tiles

    def get_moves(self, json_data):  # Generates moves based on JSON data
        game_info = json_data.get("game_info", {})  # Extracts game information
        if game_info:  # If game information is present
            self.tiles = []  # Resets tiles list
            for i in range(((2 * game_info["map_height"]) + 1)):  # Creates rows of tiles
                row = [None] * ((2 * game_info["map_width"]) + 1)  # Initializes row
                for j in range(((2 * game_info["map_width"]) + 1)):  # Creates columns of tiles
                    row[j] = Tile({'x': j, 'y': i})  # Creates a tile with x, y coordinates
                self.tiles.append(row)  # Adds row to tiles list

        for tile in json_data['tile_updates']:  # Updates each tile with new data
            self.tiles[tile['x']][tile['y']].update(tile)  # Calls update method for the tile

        units = set([unit['id'] for unit in json_data['unit_updates'] if unit['type'] != 'base'])  # Collects unit IDs
        self.units |= units  # Adds new unit IDs to the set
        unit = random.choice(tuple(self.units))  # Chooses a random unit
        direction = random.choice(self.directions)  # Chooses a random direction
        move = 'MOVE'  # Sets the command to 'MOVE'
        command = {
            "commands": [{"command": move, "unit": unit, "dir": direction}]}  # Creates move command in JSON format
        response = json.dumps(command, separators=(',', ':')) + '\n'  # Converts command to JSON and adds newline
        return response  # Returns the move response

    def get_random_move(self, json_data):  # Generates random move commands
        units = set([unit['id'] for unit in json_data['unit_updates'] if unit['type'] != 'base'])  # Collects unit IDs
        self.units |= units  # Adds new unit IDs to the set
        unit = random.choice(tuple(self.units))  # Chooses a random unit
        direction = random.choice(self.directions)  # Chooses a random direction
        move = 'MOVE'  # Sets the command to 'MOVE'
        command = {
            "commands": [{"command": move, "unit": unit, "dir": direction}]}  # Creates move command in JSON format
        response = json.dumps(command, separators=(',', ':')) + '\n'  # Converts command to JSON and adds newline
        return response  # Returns the move response

    def is_valid(self, Currentrow, currentcol, game_info):
        return (Currentrow >= 0) and (Currentrow < game_info["map_height"]) and (currentcol >= 0) and (currentcol < game_info["map_width"])

    # Check if a cell is unblocked

    def is_unblocked(self,tiles, row, col):
        tile = tiles[row][col]
        return tile.blocked

    # Check if a cell is the destination

    def is_destination(self,row, col, dest):
        return row == dest[0] and col == dest[1]

    # Calculate the heuristic value of a cell (Euclidean distance to destination)

    def calculate_h_value(self,row, col, dest):
        return ((row - dest[0]) ** 2 + (col - dest[1]) ** 2) ** 0.5

    # Trace the path from source to destination

    def trace_path(self,cell_details, dest):
        print("The Path is ")
        path = []
        row = dest[0]
        col = dest[1]

        # Trace the path from destination to source using parent cells
        while not (cell_details[row][col].parent_i == row and cell_details[row][col].parent_j == col):
            path.append((row, col))
            temp_row = cell_details[row][col].parent_i
            temp_col = cell_details[row][col].parent_j
            row = temp_row
            col = temp_col

        # Add the source cell to the path
        path.append((row, col))
        # Reverse the path to get the path from source to destination
        path.reverse()

        # Print the path
        # for i in path:
        #     print("->", i, end=" ")
        return path



    # Implement the A* search algorithm

    def a_star_search(self,game_info, src, dest, tiles):
        # Check if the source and destination are valid
        if not self.is_valid(src[0], src[1], game_info) or not self.is_valid(dest[0], dest[1], game_info):
            print("Source or destination is invalid")
            return

        # Check if the source and destination are unblocked
        if not self.is_unblocked(tiles, src[0], src[1]) or not self.is_unblocked(tiles, dest[0], dest[1]):
            print("Source or the destination is blocked")
            return

        # Check if we are already at the destination
        if self.is_destination(src[0], src[1], dest):
            print("We are already at the destination")
            return

        # Initialize the closed list (visited cells)
        closed_list = [[False for _ in range(game_info["map_width"])] for _ in range(game_info["map_height"])]
        # Initialize the details of each cell
        cell_details = [[Cell() for _ in range(game_info["map_width"])] for _ in range(game_info["map_height"])]

        # Initialize the start cell details
        i = src[0]
        j = src[1]
        cell_details[i][j].f = 0
        cell_details[i][j].g = 0
        cell_details[i][j].h = 0
        cell_details[i][j].parent_i = i
        cell_details[i][j].parent_j = j

        # Initialize the open list (cells to be visited) with the start cell
        open_list = []
        heapq.heappush(open_list, (0.0, i, j))

        # Initialize the flag for whether destination is found
        found_dest = False

        # Main loop of A* search algorithm
        while len(open_list) > 0:
            # Pop the cell with the smallest f value from the open list
            p = heapq.heappop(open_list)

            # Mark the cell as visited
            i = p[1]
            j = p[2]
            closed_list[i][j] = True

            # For each direction, check the successors
            directions = [(0, 1), (0, -1), (1, 0), (-1, 0),
                          (1, 1), (1, -1), (-1, 1), (-1, -1)]
            for dir in directions:
                new_i = i + dir[0]
                new_j = j + dir[1]

                # If the successor is valid, unblocked, and not visited
                if self.is_valid(new_i, new_j) and self.is_unblocked(tiles, new_i, new_j) and not closed_list[new_i][new_j]:
                    # If the successor is the destination
                    if self.is_destination(new_i, new_j, dest):
                        # Set the parent of the destination cell
                        cell_details[new_i][new_j].parent_i = i
                        cell_details[new_i][new_j].parent_j = j
                        print("The destination cell is found")
                        # Trace and print the path from source to destination
                        self.trace_path(cell_details, dest)
                        found_dest = True
                        return
                    else:
                        # Calculate the new f, g, and h values
                        g_new = cell_details[i][j].g + 1.0
                        h_new = self.calculate_h_value(new_i, new_j, dest)
                        f_new = g_new + h_new

                        # If the cell is not in the open list or the new f value is smaller
                        if cell_details[new_i][new_j].f == float('inf') or cell_details[new_i][new_j].f > f_new:
                            # Add the cell to the open list
                            heapq.heappush(open_list, (f_new, new_i, new_j))
                            # Update the cell details
                            cell_details[new_i][new_j].f = f_new
                            cell_details[new_i][new_j].g = g_new
                            cell_details[new_i][new_j].h = h_new
                            cell_details[new_i][new_j].parent_i = i
                            cell_details[new_i][new_j].parent_j = j

        # If the destination is not found after visiting all cells
        if not found_dest:
            print("Failed to find the destination cell")

    # Driver Code


# Runs the server if this script is executed directly
if __name__ == "__main__":
    port = int(sys.argv[1]) if (len(sys.argv) > 1 and sys.argv[1]) else 9090  # Sets port from args or defaults to 9090
    host = '0.0.0.0'  # Sets the server to listen on all IP addresses

    server = ss.TCPServer((host, port), NetworkHandler)  # Creates a TCP server with host and port
    print("listening on {}:{}".format(host, port))  # Prints the listening host and port
    server.serve_forever()  # Starts the server to handle requests indefinitely