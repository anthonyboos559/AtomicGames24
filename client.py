#!/usr/bin/python

import sys
import json
import random

from collections import defaultdict

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
        self.player_id = config['player_id']
        self.x = config['x']
        self.y = config['y']
        self.type = config['type']
        self.status = config['status']
        self.hp = config['health']
        self.resource = config.get("resource", None)
        self.attack = config.get("can_attack", None)

    def update(self, config: dict):
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
        self.units = {}
        self.directions = ['N', 'S', 'E', 'W']
        self.tiles = []
        self.enemies = {}
        self.base = None

    def init_board(self, game_info):
        self.tiles = []
        for i in range(((2 * game_info["map_height"]) + 1)):
            row = [None] * ((2 * game_info["map_width"]) + 1)
            for j in range(((2 * game_info["map_width"]) + 1)):
                row[j] = Tile({'x': j, 'y': i})
            self.tiles.append(row)

    def get_moves(self, json_data):
        game_info = json_data.get("game_info", {})
        if game_info:
            self.init_board(game_info)
            
        for tile in json_data['tile_updates']:
            self.tiles[tile['x']][tile['y']].update(tile)
            if tile.get("units", []):
                for enemy in tile["units"]:
                    self.enemies[enemy['id']] = Unit(enemy)

        for unit in json_data['unit_updates']:
            if self.base is None and unit['type'] == 'base':
                self.base = Unit(unit)
            if unit['id'] in self.units.keys():
                self.units[unit['id']].update(unit)
            else:
                self.units[unit['id']] = Unit(unit)

        commands = []
        unit_counts = defaultdict(int)

        for unit in self.units.values():
            unit_counts[unit.type] += 1
            if unit.status == 'idle':
                if unit.type == 'worker':
                    if unit.resources:
                        shortest_path = self.get_shortest_path((unit.x, unit.y), (self.base.x, self.base.y))
                        commands.append({"command": 'MOVE', "unit": unit.id, "dir": self.get_direction(unit, shortest_path[0])})
                    else:
                        destx, desty = self.get_nearest_resource(unit)
                        shortest_path = self.get_shortest_path((unit.x, unit.y), (destx, desty))
                        if len(shortest_path > 1):
                            commands.append({"command": 'MOVE', "unit": unit.id, "dir": self.get_direction(unit, shortest_path[0])})
                        else:
                            commands.append({"command": 'GATHER', 'unit': unit.id, "dir": self.get_direction(unit, shortest_path[0])})
                
        if unit_counts['scout'] <= 3:
            commands.append({"command": "CREATE", "type": "scout"})
        if unit_counts['tank'] <= 1:
            commands.append({"command": "CREATE", "type": "tank"})
        if unit_counts['worker'] <= 5:
            commands.append({"command": "CREATE", "type": "worker"})

        command = {"commands": commands}
        response = json.dumps(command, separators=(',',':')) + '\n'
        return response

    def get_nearset_resource(self, unit):
        start = unit.x, unit.y
        for k in range(1, 31):
            for yoff in range(-k, k+1):
                for xoff in range(-k, k+1):
                    tile = self.tiles[unit.x + xoff][unit.y + yoff]
                    if tile.resources:
                        return tile.x, tile.y


    def get_direction(self, unit, coords):
        if unit.x == coords[0]:
            dir = unit.y - coords[1]
            if dir < 0:
                return 'N'
            else:
                return 'S'
        else:
            dir = unit.x - coords[0]
            if dir < 0:
                return 'W'
            else:
                return 'E'

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
