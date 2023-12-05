CONE_ANGLE = 15 # degrees
MAX_DISTANCE = 5 # feet
BLOCKING_RADIUS = 1 # feet

# row = [o, dir, adjustedX, adjustedY, oDefender, dirDefender, adjustedXDefender, adjustedYDefender]
def looking_to_block_or_blocking_df_fn(row) -> int:
    blocking_status = 0
    player1 = row[0:4]
    player2 = row[4:]

    if is_in_vision_cone(player1, player2):
        blocking_status = 1

    if is_blocking(player1, player2):
        blocking_status = 2

    return blocking_status
    

def looking_to_block_or_blocking(player1: tuple, player2: tuple) -> int:
    if is_in_vision_cone(player1, player2):
        if is_blocking(player1, player2):
            return 2
            
        return 1

    return 0

def is_in_vision_cone(player1: tuple, player2: tuple) -> bool:
    return (is_in_angle(player1, player2) and is_in_distance(player1, player2))

def is_in_angle(player1: tuple, player2: tuple) -> bool:
    half_cone_angle = CONE_ANGLE / 2

    y_dist = player2[3] - player1[3]
    x_dist = player2[2] - player1[2]
    player1_orientation = float(player1[0]) if type(player1[0]) == str else player1[0]

    angle = math.degrees(math.atan2(y_dist, x_dist))

    if player1_orientation - half_cone_angle <= angle <= player1_orientation + half_cone_angle:
        return True
    
    return False

def is_in_distance(player1: tuple, player2: tuple) -> bool:
    distance_between_players = calculate_distance(player1, player2)
    if distance_between_players <= MAX_DISTANCE:
        return True
    
    return False

def is_blocking(player1: tuple, player2: tuple) -> bool:
    distance_between_players = calculate_distance(player1, player2)
    if distance_between_players <= BLOCKING_RADIUS:
        return True

    return False


def calculate_distance(player1: tuple, player2: tuple) -> float:
    y_dist = abs(player1[3] - player2[3])
    x_dist = abs(player1[2] - player2[2])

    return math.sqrt(x_dist**2 + y_dist**2)