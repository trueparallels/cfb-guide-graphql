from graphene import ObjectType, String, Schema, Int, Decimal, Field, List
import decimal
import boto3
from boto3.dynamodb.conditions import Attr, Key

class Conference(ObjectType):
    id = Decimal()
    name = String()
    parent_id = Decimal()

class TeamsQuery(ObjectType):
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

class GamesQuery(ObjectType):
    pass

class Game(ObjectType):
    gameId = String()
    gameWeekYear = String()
    date = String()
    homeAbbreviation = String()
    visitorAbbreviation = String()


class AllQuery(TeamsQuery, GamesQuery, ObjectType):
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
                )
            )

        return games

schema = Schema(query=AllQuery)