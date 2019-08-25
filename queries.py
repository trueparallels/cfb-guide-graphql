import boto3
from boto3.dynamodb.conditions import Attr, Key
import schema

def get_teams():
    teams = []
    db = boto3.resource('dynamodb')
    teamsTable = db.Table('cfb-guide-prod-teams')

    response = teamsTable.scan(
        Select='ALL_ATTRIBUTES'
    )

    for item in response['Items']:
        team = schema.Team(
                id=item['id'],
                abbreviation=item['abbreviation'],
                alternateColor=item['alternate_color'],
                color=item['color'],
                conference=item['conference'],
                displayName=item['display_name'],
                location=item['location'],
                name=item['name']
            )
        teams.append(team)

    return teams

def get_networks():
    networks = {}

    db = boto3.resource('dynamodb')
    gamesTable = db.Table('cfb-guide-prod-games')

    response = gamesTable.scan(
        Select='SPECIFIC_ATTRIBUTES',
        AttributesToGet=['network']
    )

    print(response['Items'])

    for item in response['Items']:
        network = schema.Network(
            name=item['network']
        )
        print(network.name)
        networks[network.name] = network

    return networks.values()