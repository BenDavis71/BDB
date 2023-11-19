import polars as pl
import math as math

# find a better way to import?
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from constants import *

'''
Used to determine if player1 can 'see' player2

Example:
data = {
    'adjustedX': [50.00, 50.00],
    'adjustedY': [45.00, 46.00],
    'adjustedO': [90.00, 270.00]
}

test_df = pl.DataFrame(data)
is_in_vision_cone(test_df[0], test_df[1])
'''

# This fn should be called and determines if
# 1: A player can see another player
# 2: A player is blocking another player
# 0: Neither - they're blind?
def looking_to_block_or_blocking(player1: pl.DataFrame, player2: pl.DataFrame) -> int:
    if is_blocking(player1, player2):
        return 2

    if is_in_vision_cone(player1, player2):
        return 1

    return 0

def is_in_vision_cone(player1: pl.DataFrame, player2: pl.DataFrame) -> bool:
    return (is_in_angle(player1, player2) and is_in_distance(player1, player2))

def is_in_angle(player1: pl.DataFrame, player2: pl.DataFrame) -> bool:
    half_cone_angle = CONE_ANGLE / 2

    y_dist = player2.select(pl.col('adjustedY')).item() - player1.select(pl.col('adjustedY')).item()
    x_dist = player2.select(pl.col('adjustedX')).item() - player1.select(pl.col('adjustedX')).item()

    player1_orientation = player1.select(pl.col('adjustedO')).item()

    angle = math.degrees(math.atan2(y_dist, x_dist))

    if player1_orientation - half_cone_angle <= angle <= player1_orientation + half_cone_angle:
        return True
    
    return False

def is_in_distance(player1: pl.DataFrame, player2: pl.DataFrame) -> bool:
    distance_between_players = calculate_distance(player1, player2)
    if distance_between_players <= MAX_DISTANCE:
        return True
    
    return False

def is_blocking(player1: pl.DataFrame, player2: pl.DataFrame) -> bool:
    distance_between_players = calculate_distance(player1, player2)
    if distance_between_players <= BLOCKING_RADIUS:
        return True

    return False


def calculate_distance(player1: pl.DataFrame, player2: pl.DataFrame) -> float:
    y_dist = abs(player1.select(pl.col('adjustedY')).item() - player2.select(pl.col('adjustedY')).item())
    x_dist = abs(player1.select(pl.col('adjustedX')).item() - player2.select(pl.col('adjustedX')).item())

    return math.sqrt(x_dist**2 + y_dist**2)