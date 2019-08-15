from graphene import ObjectType, String, Schema, Int, Decimal, Field, List, Boolean
import decimal
import boto3
from boto3.dynamodb.conditions import Attr, Key

conferences_cache = {}

class Conference(ObjectType):
    id = Decimal()
    name = String()
    parent_id = Decimal()

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
    home = String()
    visitor = String()
    homeAbbreviation = String()
    visitorAbbreviation = String()
    isNeutralSite = Boolean()

class GamesQuery(ObjectType):
    byWeek = List(Game, week=String(default_value="2019-1"))

    def resolve_byWeek(parent, info, **kwargs):
        week = kwargs.get('week')
        games = []

        db = boto3.resource('dynamodb')
        gamesTable = db.Table('cfb-guide-prod-games')

        response = gamesTable.query(
            Select='ALL_ATTRIBUTES',
            KeyConditionExpression=Key('game_week_year').eq(week)
        )

        for item in response['Items']:
            games.append(
                Game(
                    gameId=item['game_id'],
                    gameWeekYear=item['game_week_year'],
                    date=item['date'],
                    homeAbbreviation=item['home_abbr'],
                    visitorAbbreviation=item['visitor_abbr'],
                    home=item['home'],
                    visitor=item['visitor'],
                    isNeutralSite=item['neutral_site']
                )
            )

        return games

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
            print('int parent conf')
            print(int(parent.conference))
            return conferences_cache[int(parent.conference)]

        db = boto3.resource('dynamodb')
        leaguesTable = db.Table('cfb-guide-prod-leagues')

        response = leaguesTable.scan(
            Select='ALL_ATTRIBUTES'
        )

        for item in response['Items']:
            conf_id = int(item['id'])
            print('conf_id')
            print(conf_id)
            conferences_cache[conf_id] = item

        return conferences_cache[int(parent.conference)]

class TeamsQuery(ObjectType):
    teams = List(Team)

    def resolve_teams(parent, info, **kwargs):
        teams = []

        db = boto3.resource('dynamodb')
        teamsTable = db.Table('cfb-guide-prod-teams')

        response = teamsTable.scan(
            Select='ALL_ATTRIBUTES'
        )

        for item in response['Items']:
            teams.append(
                Team(
                    id=item['id'],
                    abbreviation=item['abbreviation'],
                    alternateColor=item['alternate_color'],
                    color=item['color'],
                    conference=item['conference'],
                    displayName=item['display_name'],
                    location=item['location'],
                    name=item['name']
                )
            )

        return teams

class AllQuery(ConferenceQuery, GamesQuery, TeamsQuery, ObjectType):
    pass

schema = Schema(query=AllQuery)