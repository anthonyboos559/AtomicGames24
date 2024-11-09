#!/usr/bin/python

import sys
import json
import random

if (sys.version_info > (3, 0)):
    print("Python 3.X detected")
    import socketserver as ss
else:
    print("Python 2.X detected")
    import SocketServer as ss


class NetworkHandler(ss.StreamRequestHandler):
    def handle(self):
        game = Game()

        while True:
            data = self.rfile.readline().decode() # reads until '\n' encountered
            json_data = json.loads(str(data))
            # uncomment the following line to see pretty-printed data
            # print(json.dumps(json_data, indent=4, sort_keys=True))
            # response = game.get_random_move(json_data).encode()
            response = game.get_moves(json_data).encode()
            self.wfile.write(response)

class Unit:
    def __init__(self, config: dict) -> None:
        self.id = config['id']
        self.x = config['x']
        self.y = config['y']
        self.type = config['type']
        self.status = config['status']
        self.hp = config['health']
        self.resource = config.get("resource", None)
        self.attack = config.get("can_attack", None)

class Tile:
    def __init__(self, config: dict) -> None:
        self.visible = config.get('visible', False)
        self.x = config['x']
        self.y = config['y']
        self.blocked = config.get('blocked', False)
        if config.get('resources', None):
            self.resources = Resource(config['resources'])
        else:
            self.resources = None
        self.units = []
        if config.get('units', []):
            for unit in config['units']:
                self.units.append(Unit(unit))

    def update(self, config:dict):
        self.visible = config['visible']
        self.blocked = config.get('blocked', False)
        if config.get('resources', None):
            self.resources = Resource(config['resources'])
        else:
            self.resources = None
        self.units = []
        if config.get('units', []):
            for unit in config['units']:
                self.units.append(Unit(unit))

class Resource:
    def __init__(self, config: dict) -> None:
        self.id = config['id']
        self.type = config['type']
        self.total = config['total']
        self.value = config['value']

class Game:
    def __init__(self):
        self.units = set() # set of unique unit ids
        self.directions = ['N', 'S', 'E', 'W']
        self.tiles = []

    def get_moves(self, json_data):
        game_info = json_data.get("game_info", {})
        if game_info:
            self.tiles = []
            for i in range(((2 * game_info["map_height"]) + 1)):
                row = [None] * ((2 * game_info["map_width"]) + 1)
                for j in range(((2 * game_info["map_width"]) + 1)):
                    row[j] = Tile({'x': j, 'y': i})
                self.tiles.append(row)
            
        for tile in json_data['tile_updates']:
            self.tiles[tile['x']][tile['y']].update(tile)
        
        units = set([unit['id'] for unit in json_data['unit_updates'] if unit['type'] != 'base'])
        self.units |= units # add any additional ids we encounter
        unit = random.choice(tuple(self.units))
        direction = random.choice(self.directions)
        move = 'MOVE'
        command = {"commands": [{"command": move, "unit": unit, "dir": direction}]}
        response = json.dumps(command, separators=(',',':')) + '\n'
        return response



    def get_random_move(self, json_data):
        units = set([unit['id'] for unit in json_data['unit_updates'] if unit['type'] != 'base'])
        self.units |= units # add any additional ids we encounter
        unit = random.choice(tuple(self.units))
        direction = random.choice(self.directions)
        move = 'MOVE'
        command = {"commands": [{"command": move, "unit": unit, "dir": direction}]}
        response = json.dumps(command, separators=(',',':')) + '\n'
        return response

if __name__ == "__main__":
    port = int(sys.argv[1]) if (len(sys.argv) > 1 and sys.argv[1]) else 9090
    host = '0.0.0.0'

    server = ss.TCPServer((host, port), NetworkHandler)
    print("listening on {}:{}".format(host, port))
    server.serve_forever()
