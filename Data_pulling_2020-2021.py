import sys
from urllib.request import urlopen
from bs4 import BeautifulSoup
import requests
import pandas as pd
import sqlite3

league_id = '15562579'
year = '2020'
espn = "AEBVC6YS%2FWaC1olembgTCqlTjvQKjLNaDnYzmKySMO%2BW8QudENps9MFirTsg%2BndeJsDoQJg29ha6LWK2JBqRVnZ%2FqG0xfJ1u9QoWhL05cPbx3WjhAGEG3kqhkRJhz1ZrIxt4c1qrSgvaqWQaD32Z1yJI0CwNAekIyRozoj8WaohT12qKNGut%2FAeRmEieIkawzE5OMg3NellVNtlWw7BIgr84ZqDBB1sE4dULPHELMjoAr19tXNN3yfCTsADcrS%2FRyPJEtWV7MJj70x2X35HH7aThdLyZ3lJRElxIZi%2BR0c%2FOIQ%3D%3D"

swid = "{95664A0A-21A8-45EC-A64A-0A21A815ECC1}"

def get_weekly_lineup(league_id, year, swid, espn):
    slotcodes = {
        0 : 'QB', 2 : 'RB', 4 : 'WR',
        6 : 'TE', 16: 'Def', 17: 'K',
        20: 'Bench', 21: 'IR', 23: 'Flex'
    }

    url = 'https://fantasy.espn.com/apis/v3/games/ffl/seasons/' + \
        str(year) + '/segments/0/leagues/' + str(league_id) + \
        '?view=mMatchup&view=mMatchupScore'

    data = []
    for week in range(1, 17):

        r = requests.get(url,
                        params={'scoringPeriodId': week},
                        cookies={"SWID": swid, "espn_s2": espn})
        d = r.json()
        for tm in d['teams']:
            tmid = tm['id']
            for p in tm['roster']['entries']:
                name = p['playerPoolEntry']['player']['fullName']
                slot = p['lineupSlotId']
                pos  = slotcodes[slot]

                # injured status (need try/exc bc of D/ST)
                inj = 'NA'
                try:
                    inj = p['playerPoolEntry']['player']['injuryStatus']
                except:
                    pass

                # projected/actual points
                proj, act = None, None
                for stat in p['playerPoolEntry']['player']['stats']:
                    if stat['scoringPeriodId'] != week:
                        continue
                    if stat['statSourceId'] == 0:
                        act = stat['appliedTotal']
                    elif stat['statSourceId'] == 1:
                        proj = stat['appliedTotal']

                data.append([
                    week, tmid, name, slot, pos, inj, proj, act
                ])


    df = pd.DataFrame(data, 
                        columns=['Week', 'Team', 'Player', 'Slot', 
                                'Pos', 'Status', 'Proj', 'Actual'])
    path = 'data/weekly_lineup_' + year + ".csv"
    df.to_csv(path)
    return data

def get_schedule(url, swid, espn, year):
    r = requests.get(url,
                        params={},
                        cookies={"SWID": swid, "espn_s2": espn})
    d = r.json()
    df = [[
            game['matchupPeriodId'],
            game['home']['teamId'], game['home']['totalPoints'],
            game['away']['teamId'], game['away']['totalPoints']
        ] for game in d['schedule']]
    df = pd.DataFrame(df, columns=['Week', 'Team1', 'Score1', 'Team2', 'Score2'])
    df['Type'] = ['Regular' if w<=14 else 'Playoff' for w in df['Week']]
    
    path = 'data/schedule_' + year + ".csv"
    df.to_csv(path)
    return df



url = "https://fantasy.espn.com/apis/v3/games/ffl/leagueHistory/" + \
        str(league_id) + "?seasonId=" + str(year)
def get_teams(url, year):
    r = requests.get(url, params={"view": "mTeam"})
    d = r.json()[0]
    teams = [[
        info['abbrev'],
        info['name'],
        info['nickname'],
        info['id'],
        info['playoffSeed'],
        info['rankCalculatedFinal'],
        info['points'],
        info['record']['overall']['wins'],
        info['record']['overall']['losses'],
        info['record']['overall']['wins'],
        info['record']['overall']['percentage'],
        info['record']['overall']['pointsAgainst'],
        info['record']['overall']['streakLength'],
        info['record']['overall']['streakType'],
        info['transactionCounter']['acquisitions'],
        info['transactionCounter']['moveToActive'],
        info['transactionCounter']['trades'],
        info['transactionCounter']['moveToIR'],
        info['valuesByStat']
    ] for info in d['teams']] 
    columns_teams = [ 'abbrev', 'name' ,
        'nickname' ,
        'id',
        'playoffSeed' ,
        'rankCalculatedFinal' ,
        'points' ,
        'wins' ,
        'losses' ,
        'wins' ,
        'percentage' ,
        'pointsAgainst' ,
        'streakLength' ,
        'streakType' ,
        'acquisitions' ,
        'moveToActive' ,
        'trades' ,
        'moveToIR' ,
        'valuesByStat']

    df_teams = pd.DataFrame(teams, columns=columns_teams)
    path = 'data/teams_' + year + ".csv"
    df_teams.to_csv(path)
    return df_teams

print("Got Data for: ")
for i in ['2020' ,'2021']:
    get_weekly_lineup(league_id, i, swid, espn)
    print("weekly lineup " + i)
    url = 'https://fantasy.espn.com/apis/v3/games/ffl/seasons/' + \
        str(i) + '/segments/0/leagues/' + str(league_id) + \
        '?view=mMatchup&view=mMatchupScore'
    get_schedule(url, swid, espn, i)
    print("schedule " + i)
    url = "https://fantasy.espn.com/apis/v3/games/ffl/leagueHistory/" + \
            str(league_id) + "?seasonId=" + str(i)
    get_teams(url, i)
    print("teams " + i)
