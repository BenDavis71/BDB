import polars as pl
import math as math

from constants import CONE_ANGLE, MAX_DISTANCE

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
def is_in_vision_cone(player1: pl.DataFrame, player2: pl.DataFrame) -> bool:
    return (is_in_angle(player2, player2) and is_in_distance(player2, player2))

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
    y_dist = abs(player1.select(pl.col('adjustedY')).item() - player2.select(pl.col('adjustedY')).item())
    x_dist = abs(player1.select(pl.col('adjustedX')).item() - player2.select(pl.col('adjustedX')).item())

    distance_between_players = math.sqrt(x_dist**2 + y_dist**2)

    if distance_between_players <= max_distance:
        return True
    
    return False