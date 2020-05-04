from graphene import ObjectType, String, Schema, Int, Decimal, Field, List, Boolean
import decimal
import boto3
from boto3.dynamodb.conditions import Attr, Key
import queries
import json
import logging

conferences_cache = {}
teams_cache = []
networks_cache = []

def get_final(item, team):
    if 'home_final_score' in item or 'visitor_final_score' in item:
        return decimal.Decimal(item['{}_final_score'.format(team)])

    return None

class Conference(ObjectType):
    id = Decimal()
    name = String()
    parent_id = Decimal()

class Network(ObjectType):
    name = String()

class Team(ObjectType):
    id = Decimal()
    abbreviation = String()
    alternateColor = String()
    color = String()
    conference = Field(Conference)
    displayName = String()
    location = String()
    name = String()

    def resolve_conference(parent, info, **kwargs):
        global conferences_cache

        if len(conferences_cache):
            return conferences_cache[int(parent.conference)]

        db = boto3.resource('dynamodb')
        leaguesTable = db.Table('cfb-guide-prod-leagues')

        response = leaguesTable.scan(
            Select='ALL_ATTRIBUTES'
        )

        for item in response['Items']:
            conf_id = int(item['id'])
            conferences_cache[conf_id] = item

        return conferences_cache[int(parent.conference)]

class ConferenceQuery(ObjectType):
    conference = List(Conference, id=Int(default_value=None))

    def resolve_conference(parent, info, **kwargs):
        teamId = kwargs.get('id')

        db = boto3.resource('dynamodb')
        leaguesTable = db.Table('cfb-guide-prod-leagues')

        if not teamId:
            response = leaguesTable.scan(
                Select='ALL_ATTRIBUTES',
                FilterExpression=Attr('parent_id').eq(80)
            )
        else:
            response = leaguesTable.scan(
                Select='ALL_ATTRIBUTES',
                FilterExpression=Attr('id').eq(teamId)
            )

        response_items = response['Items']
        
        conferences = []

        for item in response_items:
            conferences.append(
                Conference(
                    id=decimal.Decimal(item['id']),
                    name=item['name'],
                    parent_id=decimal.Decimal(item['parent_id'])
                )
            )

        return conferences

class Game(ObjectType):
    gameId = String()
    gameWeekYear = String()
    date = String()
    dateIsValid = Boolean()
    network = String()
    home = String()
    visitor = String()
    homeAbbreviation = String()
    visitorAbbreviation = String()
    isNeutralSite = Boolean()
    homeTeam = Field(Team)
    visitorTeam = Field(Team)
    homeFinalScore = Decimal()
    visitorFinalScore = Decimal()
    headline = String()

class GamesQuery(ObjectType):
    byWeek = List(Game, week=String(default_value="2019-1"))
    allGamesByYear = List(Game, year=String(default_value="2020"))

    def resolve_allGamesByYear(parent, info, **kwargs):
        logging.getLogger('__main__').info("resolving allGamesByYear")
        global teams_cache

        year = kwargs.get('year')
        year_filter = "{}-".format(year)

        if not len(teams_cache):
            teams_cache = queries.get_teams()

        games = []

        db = boto3.resource('dynamodb')
        gamesTable = db.Table('cfb-guide-prod-games')

        response = gamesTable.scan(
            Select='ALL_ATTRIBUTES',
            FilterExpression=Key('game_week_year').begins_with(year_filter)
        )

        for item in response['Items']:
            home_team = [team for team in teams_cache if team.id == item['home_team_id']]
            visitor_team = [team for team in teams_cache if team.id == item['visitor_team_id']]
            # print(json.dumps(item, indent=4, default=str))
            games.append(
                Game(
                    gameId=item['game_id'],
                    gameWeekYear=item['game_week_year'],
                    date=item['date'],
                    dateIsValid=item['date_is_valid'] if 'date_is_valid' in item else None,
                    network=item['network'],
                    headline=item['headline'] if 'headline' in item else None,
                    homeAbbreviation=item['home_abbr'],
                    visitorAbbreviation=item['visitor_abbr'],
                    home=item['home'],
                    visitor=item['visitor'],
                    isNeutralSite=item['neutral_site'],
                    homeTeam=home_team[0] if len(home_team) else None,
                    visitorTeam=visitor_team[0] if len(visitor_team) else None,
                    homeFinalScore=get_final(item, 'home'),
                    visitorFinalScore=get_final(item, 'visitor')
                )
            )

        return games


    def resolve_byWeek(parent, info, **kwargs):
        global teams_cache

        if not len(teams_cache):
            teams_cache = queries.get_teams()

        week = kwargs.get('week')
        games = []

        db = boto3.resource('dynamodb')
        gamesTable = db.Table('cfb-guide-prod-games')

        response = gamesTable.query(
            Select='ALL_ATTRIBUTES',
            KeyConditionExpression=Key('game_week_year').eq(week)
        )

        for item in response['Items']:
            home_team = [team for team in teams_cache if team.id == item['home_team_id']]
            visitor_team = [team for team in teams_cache if team.id == item['visitor_team_id']]
            # print(json.dumps(item, indent=4, default=str))
            games.append(
                Game(
                    gameId=item['game_id'],
                    gameWeekYear=item['game_week_year'],
                    date=item['date'],
                    dateIsValid=item['date_is_valid'] if 'date_is_valid' in item else None,
                    network=item['network'],
                    headline=item['headline'] if 'headline' in item else None,
                    homeAbbreviation=item['home_abbr'],
                    visitorAbbreviation=item['visitor_abbr'],
                    home=item['home'],
                    visitor=item['visitor'],
                    isNeutralSite=item['neutral_site'],
                    homeTeam=home_team[0] if len(home_team) else None,
                    visitorTeam=visitor_team[0] if len(visitor_team) else None,
                    homeFinalScore=get_final(item, 'home'),
                    visitorFinalScore=get_final(item, 'visitor')
                )
            )

        return games

class TeamsQuery(ObjectType):
    teams = List(Team)

    def resolve_teams(parent, info, **kwargs):
        global teams_cache
        
        if not len(teams_cache):
            teams_cache = queries.get_teams()
        
        return teams_cache

class NetworksQuery(ObjectType):
    networks = List(Network)

    def resolve_networks(parent, info, **kwargs):
        global networks_cache
        
        if not len(networks_cache):
            networks_cache = queries.get_networks()
        
        return networks_cache

class AllQuery(ConferenceQuery, GamesQuery, TeamsQuery, NetworksQuery, ObjectType):
    pass

schema = Schema(query=AllQuery)