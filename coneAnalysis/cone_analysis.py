import polars as pl
import math as math

from constants import CONE_ANGLE, MAX_DISTANCE

def is_in_vision_cone(player1_row, player2_row) -> bool:
    return (is_in_angle(player1_row, player2_row) and is_in_distance(player1_row, player2_row))

def is_in_angle(player1, player2) -> bool:
    half_cone_angle = CONE_ANGLE / 2

    y_dist = abs(player1.select(pl.col('adjustedY')).item() - player2.select(pl.col('adjustedY')).item())
    x_dist = abs(player1.select(pl.col('adjustedX')).item() - player2.select(pl.col('adjustedX')).item())
    player1_orientation = player1.select(pl.col('adjustedO')).item()

    angle = math.degrees(math.atan2(y_dist, x_dist))

    if player1_orientation - half_cone_angle <= angle + player1_orientation <= player1_orientation + angle:
        return True
    
    return False

def is_in_distance(player1_index, player2_index) -> bool:
    y_dist = abs(player1.select(pl.col('adjustedY')).item() - player2.select(pl.col('adjustedY')).item())
    x_dist = abs(player1.select(pl.col('adjustedX')).item() - player2.select(pl.col('adjustedX')).item())

    distance_between_players = math.sqrt(x_dist**2 + y_dist**2)

    if distance_between_players <= MAX_DISTANCE:
        return True
    
    return False