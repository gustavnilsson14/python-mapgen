#!/usr/bin/python

import os
import sys
import math
from random import randint, choice
import json
import shutil
from os import listdir
from os.path import isfile, join
import time

start_seconds = int(round(time.time()))

if len( sys.argv ) < 3 :
    print "Usage:"
    print "mapgen.py <sizeX> <sizeY>"
    print "Optionally:"
    print "mapgen.py <sizeX> <sizeY> <mode> <outdir>"
    exit( 1 )

sizeX = int( sys.argv[ 1 ] )
sizeY = int( sys.argv[ 2 ] )
mode = "default"
output_dir = ""
if len( sys.argv ) >= 4 :
    mode = sys.argv[ 3 ]
if len( sys.argv ) >= 5 :
    output_dir = sys.argv[ 4 ]

TILE_TYPE_BASE = 0
TILE_TYPE_EDGE = 1
TILE_TYPE_FLOOR = 2
TILE_TYPE_CORRIDOOR = 3
TILE_TYPE_CORRIDOOR_START = 4
TILE_TYPE_WALL = 5
TILE_TYPE_WALL_CORRIDOOR = 6
TILE_TYPE_HAZARD = 7
TILE_DEBUG_LIST = [
    '.',
    '0',
    '_',
    '-',
    '|',
    '#',
    '#',
    '!',
]
TILE_LEGEND_LIST = [
    'TILE_TYPE_BASE',
    'TILE_TYPE_EDGE',
    'TILE_TYPE_FLOOR',
    'TILE_TYPE_CORRIDOOR',
    'TILE_TYPE_WALL',
    'TILE_TYPE_WALL_HARD',
    'TILE_TYPE_HAZARD',
]
CONTENT_TYPE_NONE = 0
CONTENT_TYPE_TRAP = 1
CONTENT_TYPE_TRAP_DANGEROUS = 2
CONTENT_TYPE_MONSTER = 3
CONTENT_TYPE_MONSTER_GROUP = 4
CONTENT_TYPE_MONSTER_DANGEROUS = 5
CONTENT_TYPE_MONSTER_GROUP_DANGEROUS = 6
CONTENT_TYPE_BOON = 7
CONTENT_TYPE_BOON_GREATER = 8
CONTENT_TYPE_FURNITURE = 9
CONTENT_TYPE_PROP = 10
CONTENT_TYPE_EXIT = 11
CONTENT_TRAP_LIST = [1,2]
CONTENT_MONSTER_LIST = [3,4,5,6]
CONTENT_BOON_LIST = [7,8]
CONTENT_OTHER_LIST = [9,10]

CONTENT_DEBUG_LIST = [
    '',
    '"',
    '!',
    'm',
    'M',
    'd',
    'D',
    '?',
    '$',
    '|',
    '^',
    '<'
]
CONTENT_LEGEND_LIST = [
    'CONTENT_TYPE_NONE',
    'CONTENT_TYPE_TRAP',
    'CONTENT_TYPE_TRAP_DANGEROUS',
    'CONTENT_TYPE_MONSTER',
    'CONTENT_TYPE_MONSTER_GROUP',
    'CONTENT_TYPE_MONSTER_DANGEROUS',
    'CONTENT_TYPE_MONSTER_GROUP_DANGEROUS',
    'CONTENT_TYPE_BOON',
    'CONTENT_TYPE_BOON_GREATER',
    'CONTENT_TYPE_FURNITURE',
    'CONTENT_TYPE_PROP',
    'CONTENT_TYPE_EXIT',
]

class Level :
    
    def __init__( self, sizeX, sizeY, mode = "default" ) :
        self.sizeX = sizeX
        self.sizeY = sizeY
        self.volume = sizeY * sizeY
        self.padding = 1
        self.mode = mode
        self.rooms = []
        self.corridoors = []
        self.content = []
        self.danger_level = 0
        self.boon_level = 0
        self.main_room = 0
        self.main_chunk = []
        self.grid = []
        for y in range( 0, sizeY ) :
            row = []
            for x in range( 0, sizeX ) :
                if x == 0 or y == 0 or x == sizeX - 1 or y == sizeY - 1 :
                    row.append( Tile( self, x, y, TILE_TYPE_EDGE ) )
                    continue
                row.append( Tile( self, x, y, TILE_TYPE_BASE ) )
            self.grid.append( row )
        if mode == "default" :
            self.generate_default()
        self.debug_print()
            
    def debug_print( self ) :
        for row in self.grid :
            row_string = ""
            for tile in row :
                if tile.content != 0 :
                    row_string += str(CONTENT_DEBUG_LIST[tile.content])
                    continue
                row_string += str(TILE_DEBUG_LIST[tile.type])
            print row_string
            
    def get_tile_at( self, x, y ) :
        if self.point_in_grid( (x, y) ) == 1 :
            return self.grid[y][x]
        return 0
    
    def get_unoccupied_tile( self ) :
        maxIterations = 100
        while maxIterations != 0 :
            maxIterations -= 1
            x = randint( 1 + self.padding, sizeX - (self.padding + 1) )
            y = randint( 1 + self.padding, sizeY - (self.padding + 1) )
            tile = self.get_tile_at(x,y)
            if tile.occupied == 0 :
                return tile
        return 0
        
    def point_in_grid( self, point ) :
        if point[0] > 0 and point[0] < self.sizeX -1 and point[1] > 0 and point[1] < self.sizeY -1 :
            return 1
        return 0
    
    def generate_default( self ) :
        self.create_rooms( 10, 2, 3 )
        self.main_room = choice( self.rooms )
        self.main_chunk += [self.main_room]
        self.create_corridoors( 10 )
        self.create_content( 10 )
        
    def create_rooms( self, amount, minDimensions, maxDimensions ) :
        maxTries = 100
        while len( self.rooms ) != amount and maxTries != 0:
            origin = self.get_unoccupied_tile()
            if origin == 0 :
                maxTries -= 1
                continue
            rangeX = randint( minDimensions, maxDimensions )
            rangeY = randint( minDimensions, maxDimensions )
            room = Room( self, origin, rangeX, rangeY, self.padding )
            if room.active == 0 :
                maxTries -= 1
                continue
            self.rooms += [ room ]
        
    def create_corridoors( self, amount, maxLength = -1 ) :
        maxTries = 100
        room = self.main_room
        while len( self.corridoors ) != amount and maxTries != 0 :
            start = room.get_corridoor_start()
            end = self.get_room( room ).get_corridoor_start()
            corridoor = Corridoor( self, start, end )
            room.corridoors += [corridoor]
            self.corridoors += [corridoor]
            room = choice( self.rooms )
            maxTries -= 1
        for corridoor in self.corridoors :
            corridoor.finish()
            
    def create_content( self, amount ) :
        maxTries = 100
        while self.danger_level < amount and maxTries != 0 :
            index = randint( 0, len( CONTENT_MONSTER_LIST ) - 1 )
            monster = CONTENT_MONSTER_LIST[index]
            self.danger_level += index
            room = self.get_room()
            room.insert_content_on_floor( monster )
            maxTries -= 1
        maxTries = 100
        while self.danger_level < amount * 2 and maxTries != 0 :
            index = randint( 0, len( CONTENT_TRAP_LIST ) - 1 )
            trap = CONTENT_TRAP_LIST[index]
            self.danger_level += index * 2
            room = self.get_room()
            room.insert_content_by_wall( trap )
            maxTries -= 1
        maxTries = 100
        while self.boon_level < amount and maxTries != 0 :
            index = randint( 0, len( CONTENT_BOON_LIST ) - 1 )
            boon = CONTENT_BOON_LIST[index]
            self.boon_level += ( index * 3 ) + 1
            room = self.get_room()
            room.insert_content_by_wall( boon )
            maxTries -= 1
    
    def get_room( self, excluded_room = 0 ) :
        max_iterations = 100
        room = choice( self.rooms )
        while max_iterations != 0 and room == excluded_room :
            max_iterations -= 1
            if max_iterations == 0 :
                return 0
            room = choice( self.rooms )
        return room
        
    def grid_to_list( self ) :
        grid_list = []
        for row in self.grid :
            list_row = []
            for tile in row :
                list_row += [{
                    'type': tile.type,
                    'content': tile.content
                }]
            grid_list.append( list_row )
        return grid_list
    
class Room :
    
    def __init__( self, level, origin, rangeX, rangeY, padding ) :
        self.level = level
        self.active = 1
        self.origin = origin
        self.rangeX = rangeX
        self.rangeY = rangeY
        self.floors = []
        self.walls = []
        self.corridoors = []
        for x in range( origin.x - rangeX - padding, origin.x + rangeX + padding ) :
            for y in range( origin.y - rangeY - padding, origin.y + rangeY + padding ) :
                if self.level.point_in_grid( (x,y) ) == 0 :
                    continue
                tile = self.level.get_tile_at( x, y )
                if tile.occupied == 1 :
                    continue
                tile.room = self
                if x < origin.x - rangeX or y < origin.y - rangeY or x >= origin.x + rangeX or y >= origin.y + rangeY :
                    self.walls += [tile]
                    continue
                self.floors += [tile]
        if len( self.floors ) < ( ( self.rangeX * 2 ) * ( self.rangeY * 2 ) ) * 0.6 :
            self.active = 0
            return
        self.create_walls()
        self.create_floors()
    
    def create_walls( self ) :
        for tile in self.walls :
            tile.occupied = 1
            tile.type = TILE_TYPE_WALL
        
    def create_floors( self ) :
        for tile in self.floors :
            tile.occupied = 1
            tile.type = TILE_TYPE_FLOOR
    
    def get_corridoor_start( self ) :
        max_tries = 100
        start = 0
        while max_tries > 0 :
            max_tries -= 1
            tile = choice( self.walls )
            if self.tile_is_suitable_for_corridoor( tile ) == 0 :
                continue
            return tile
        for tile in self.walls :
            if self.tile_is_suitable_for_corridoor( tile ) == 0 :
                continue
            return tile
        return 0
        
    def tile_is_suitable_for_corridoor( self, tile ) :
        if tile.is_corridoor_candidate( self.floors ) == 0 :
            return 0
        neighbors = tile.get_neighbors_of_type( [TILE_TYPE_BASE] )
        if len( neighbors ) != 1 :
            return 0
        neighbors = tile.get_neighbors_of_type( [TILE_TYPE_WALL] )
        if len( neighbors ) < 2 :
            return 0
        neighbors = tile.get_neighbors_of_type( [TILE_TYPE_FLOOR] )
        for neighbor in neighbors :
            if neighbor in self.floors :
                return 1
        return 0
        
    def insert_content_on_floor( self, content ) :
        tile = choice(self.floors)
        max_tries = 100
        while tile.content != 0 and max_tries != 0 :
            max_tries -= 1
            tile = choice(self.floors)
        if max_tries == 0 :
            return
        tile.content = content
        
    def insert_content_by_wall( self, content ) :
        tile = choice(self.floors)
        max_tries = 100
        while ( tile.content != 0 or len( tile.get_neighbors_of_type( [TILE_TYPE_WALL] ) ) == 0 ) and max_tries != 0 :
            max_tries -= 1
            tile = choice(self.floors)
        if max_tries == 0 :
            return
        tile.content = content
        
    def insert_content_not_by_wall( self, content ) :
        tile = choice(self.floors)
        max_tries = 100
        while ( tile.content != 0 and len( tile.get_neighbors_of_type( [TILE_TYPE_WALL] ) ) != 0 ) and max_tries != 0 :
            max_tries -= 1
            tile = choice(self.floors)
        if max_tries == 0 :
            return
        tile.content = content
        
    def intersects_room( self, room ) :
        return 0
        
    def blob_find( self ) :
        return
    
class Corridoor :
    
    def __init__( self, level, start = (0,0), end = (0,0) ) :
        self.level = level
        self.start = start
        self.end = end
        self.path = 0
        if self.end != 0 and self.start != 0 :
            self.generate_route()
        
    def generate_route( self ) :
        types_dict = {
            TILE_TYPE_BASE: 1,
            TILE_TYPE_CORRIDOOR: 0,
            TILE_TYPE_WALL_CORRIDOOR: 50,
            TILE_TYPE_CORRIDOOR_START: 0
        }
        
        self.start.type = TILE_TYPE_CORRIDOOR_START
        self.end.type = TILE_TYPE_CORRIDOOR_START
        
        self.path = Path( self.level, types_dict, self.start, self.end )
        
        for tile in self.path.path :
            tile.type = TILE_TYPE_CORRIDOOR
            neighbors = tile.get_neighbors_of_type( [ TILE_TYPE_BASE ], 0 )
            for neighbor in neighbors :
                neighbor.type = TILE_TYPE_WALL_CORRIDOOR
        self.start.type = TILE_TYPE_CORRIDOOR_START
        self.end.type = TILE_TYPE_CORRIDOOR_START

    def finish( self ) :
        if self.path == 0 :
            return
        elif len(self.path.path) == 0 :
            self.start.type = TILE_TYPE_WALL
            self.end.type = TILE_TYPE_WALL
                        
class Tile :
    
    def __init__( self, level, x, y, type ) :
        self.level = level
        self.x = x
        self.y = y
        self.type = type
        self.content = 0
        self.occupied = 0
        self.room = 0
        self.h = 0
        self.d = 0
        self.p = 0
        
    def is_corridoor_candidate( self, floor_tiles = 0 ) :
        x = self.x
        y = self.y
        for x in range( x-1,x+2 ) :
            for y in range( y-1,y+2 ) :
                tile = self.level.get_tile_at( x,y )
                if tile == 0 :
                    continue
                if tile == self :
                    continue
                if tile.occupied == 1 :
                    continue
                if tile.type == TILE_TYPE_EDGE :
                    continue
                return self
        return 0
        
    def get_neighbors_of_type( self, types, no_diagonals = 1 ) :
        neighbors = []
        for x in range( -1, 2 ) :
            for y in range( -1, 2 ) :
                if no_diagonals == 1 :
                    if x != 0 and y != 0 :
                        continue
                tile = self.level.get_tile_at(self.x+x,self.y+y)
                if tile == self :
                    continue
                if tile == 0 :
                    continue
                if tile.type in types :
                    neighbors += [tile]
        return neighbors
        
class Path :
    
    def __init__( self, level, types_dict, start, end ) :
        self.level = level
        self.start = start
        self.end = end
        self.path = []
        
        current = self.start
        open_list = []
        closed_list = [ start ]
        max_iterations = 3000
        while current != end and max_iterations != 0 :
            neighbors = current.get_neighbors_of_type( types_dict.keys() )
            for tile in neighbors :
                if tile in open_list :
                    continue
                if tile in closed_list :
                    continue
                tile.h = self.xydiff( ( tile.x,tile.y ),( self.end.x,self.end.y ) )
                tile.d = current.d + types_dict.get( tile.type )
                tile.p = current
                open_list += [tile]
            next = 0
            for tile in open_list :
                if next == 0 :
                    next = tile
                    continue
                if tile == self.end :
                    next = tile
                    continue
                if next == self.end :
                    continue
                if tile.d + tile.h < next.d + next.h :
                    next = tile
            if next == 0 :
                return
            open_list.remove(next)
            closed_list += [next]
            current = next
            temp_type = current.type
            max_iterations -= 1
            
        if current != end :
            return
        max_iterations = 100
        while current != start and max_iterations != 0 :
            self.path += [current]
            current = current.p
        self.path += [current]
        
    def xydiff( self, point1, point2 ) :
        diff = 0
        diff += abs(point1[0] - point2[0])
        diff += abs(point1[1] - point2[1])
        return diff
        
level = Level( sizeX, sizeY, mode )
level.debug_print()
data = {
    "type_legend": TILE_LEGEND_LIST,
    "content_legend": CONTENT_LEGEND_LIST,
    "grid": level.grid_to_list(),
}
string_grid_json = json.dumps( data, sort_keys=True,indent=4, separators=(',', ': '))
print string_grid_json