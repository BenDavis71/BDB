import pandas as pd
import numpy as np
import polars as pl
import coneAnalysis as cone_analysis
from constants import *


def main():
    # read data
    players = pl.read_csv('nfl-big-data-bowl-2024/players.csv')
    plays = pl.read_csv('nfl-big-data-bowl-2024/plays.csv',infer_schema_length=100000)
    games = pl.read_csv('nfl-big-data-bowl-2024/games.csv',infer_schema_length=10000)
    tracking = pl.read_csv('nfl-big-data-bowl-2024/tracking_week*.csv',infer_schema_length=10000)

    # normalize data
    players = players.with_columns([pl.col('nflId').cast(str)])
    plays = plays.join(games,on='gameId')
    plays = plays.with_columns([
        (pl.col('gameId').cast(str) + '-'
        + pl.col('playId').cast(str)).alias('uniquePlayId')
    ])

    tracking = tracking.with_columns(
        (pl.col('gameId').cast(str) + '-'
        + pl.col('playId').cast(str)).alias('uniquePlayId'),
        (pl.col('gameId').cast(str) + '-'
        + pl.col('playId').cast(str) + '-'
        + pl.col('nflId').cast(str)).alias('uniquePlayerId'),
    )

    # normalize position
    tracking=tracking.with_columns([
        pl.when(pl.col('playDirection')=='right').then(53.3-pl.col('y')).otherwise(pl.col('y')).alias('adjustedX'),
        pl.when(pl.col('playDirection')=='right').then(pl.col('x')).otherwise(120-pl.col('x')).alias('adjustedY')
    ])

    tracking=tracking.with_columns([
        pl.when(pl.col('event')=='ball_snap').then(pl.col('frameId')).otherwise(-1).alias('startingFrameId'),
    ])
    tracking=tracking.with_columns([
        pl.col('startingFrameId').max().over(pl.col('uniquePlayId')),
    ])
    tracking=tracking.with_columns([
        (pl.col('frameId') - pl.col('startingFrameId')).alias('framesSinceSnap'),
    ])

    # normalize orientation 'o' and direction 'dir'
    # convert 'NA' to 0
    replacement_values = {'NA': '0'}
    tracking = tracking.with_columns(
        pl.col('o').apply(lambda x: replacement_values.get(x, x)),
        pl.col('dir').apply(lambda x: replacement_values.get(x, x)),
    )

    tracking=tracking.with_columns([
        pl.when(pl.col('playDirection')=='right').then(pl.col('dir').cast(pl.Float64)).otherwise(180-pl.col('dir').cast(pl.Float64)).alias('adjustedDir'),
        pl.when(pl.col('playDirection')=='right').then(pl.col('o').cast(pl.Float64)).otherwise(180-pl.col('o').cast(pl.Float64)).alias('adjustedO'),
    ])

    tracking=tracking.with_columns([
        pl.when(pl.col('event')=='ball_snap').then(pl.col('frameId')).otherwise(-1).alias('startingFrameId'),
    ])
    tracking=tracking.with_columns([
        pl.col('startingFrameId').max().over(pl.col('uniquePlayId')),
    ])
    tracking=tracking.with_columns([
        (pl.col('frameId') - pl.col('startingFrameId')).alias('framesSinceSnap'),
    ])

    tracking = tracking.filter(pl.col('startingFrameId')!=-1)
    tracking = tracking.filter(pl.col('club')!='football')

    labeled = tracking.filter(pl.col('gameId')==2022091104)

    players = tracking.join(players,on='nflId',how='left')
    players = players.join(games.select(['gameId','homeTeamAbbr','visitorTeamAbbr']),on='gameId')
    players = players.with_columns([
        pl.when(pl.col('club')==pl.col('homeTeamAbbr'))
        .then(pl.col('visitorTeamAbbr'))
        .otherwise(pl.col('homeTeamAbbr'))
        .alias('opponentClub')
    ])

    print(players.schema)

    # TODO: fix
    # players = players.select(
    #     ['gameId','playId','nflId','displayName','jerseyNumber','frameId','club','opponentClub',
    #         's','a','dis','o','dir','adjustedX','adjustedY','adjustedO','adjustedDir','framesSinceSnap','startingX','startingY',
    #         'relativeX','relativeY','position']
    # )

    players = players.join(
        players,
        left_on=['gameId','playId','frameId','club'],
        right_on=['gameId','playId','frameId','opponentClub'],
        suffix='Defender'
    )

    blocking_df = players.select(
        'o', 'dir', 'adjustedX', 'adjustedY', 'oDefender', 'dirDefender', 'adjustedXDefender', 'adjustedYDefender'
    ).apply(looking_to_block_or_blocking_df_fn)

    players.with_column(pl.column(blocking_df))

main()