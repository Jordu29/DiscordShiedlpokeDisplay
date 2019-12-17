import codecs
import csv
import json
import os
import sys
import urllib.parse as urlParse
import urllib.request as urlRequest
import math
import discord
import time
from datetime import datetime
import asyncio
from graphqlclient import GraphQLClient

discordTokenPath = os.path.join(os.getcwd(),"discord_token")
discordToken = ''
with open(discordTokenPath, 'r') as discordFile:
    discordToken = discordFile.readline()

apiVersion = 'alpha'
authTokenPath = os.path.join(os.getcwd(),"auth_token")
smashGGClient = GraphQLClient('https://api.smash.gg/gql/' + apiVersion)
with open(authTokenPath, 'r') as authFile:
    smashGGClient.inject_token('Bearer ' + authFile.readline())        

thresholdPath = os.path.join(os.getcwd(),"thresholds")
defaultAnnouncesThresholds = []
with open(thresholdPath, 'r') as thresholdFile:
    defaultAnnouncesThresholds = [float(stringThreshold) for stringThreshold in thresholdFile.readline().split()]

client = discord.Client()

async def annoucement(retrieveTimer=10):
    entrantsAnnouncesThresholds = set(defaultAnnouncesThresholds)
    previousNbEntrants = 0
    current_shieldpoke = retrieve_correct_shortlink()
    while True:
        if(current_shieldpoke != retrieve_correct_shortlink):
            entrantsAnnouncesThresholds = set(defaultAnnouncesThresholds)
            current_shieldpoke = retrieve_correct_shortlink()
            previousNbEntrants = 0
        entrantsAndEventSize = smashGGClient.execute('''query EntrantsAndEventSize($slug: String!) {
            tournament(slug: $slug){
                    name,
                    events{
                        numEntrants
                        startAt
                        phases{
                            name
                        }
                    },
                    
                }
            }''',{
        "slug":current_shieldpoke
        })
        parsedData = json.loads(entrantsAndEventSize)
        tournamentName = parsedData['data']['tournament']['name']
        nbEntrants = int(parsedData['data']['tournament']['events'][0]['numEntrants'])
        maxEntrants = max([int(phase['name'].split()[1]) for phase in parsedData['data']['tournament']['events'][0]['phases']])
        remainingEntrants = maxEntrants-nbEntrants
        entrantsRate = remainingEntrants/maxEntrants
        if previousNbEntrants != remainingEntrants and entrantsRate <= max(entrantsAnnouncesThresholds):
            sentence = 'Plus que '+str(remainingEntrants)+ (' places ' if remainingEntrants > 1 else ' place ') + 'pour le '+tournamentName+' !\r\n:pushpin: http://smash.gg/'+current_shieldpoke
            previousNbEntrants = remainingEntrants
            channel = client.get_channel(653622127815294986)
            await channel.send(sentence)
            entrantsAnnouncesThresholds = remove_thresholds_reached(entrantsAnnouncesThresholds,entrantsRate)
        time.sleep(retrieveTimer)

def retrieve_correct_shortlink():    
    mrs_request = smashGGClient.execute('''query EntrantsAndEventSize($slug: String!) {
        tournament(slug: $slug){
                name,
                events{
                    startAt
                },
                
            }
        }''',{
    "slug":'shieldpoke-mrs'
    })
    mrs_data = json.loads(mrs_request)
    aix_request = smashGGClient.execute('''query EntrantsAndEventSize($slug: String!) {
        tournament(slug: $slug){
                name,
                events{
                    startAt
                },
                
            }
        }''',{
    "slug":'shieldpoke-aix'
    })
    aix_data = json.loads(aix_request)
    return 'shieldpoke-aix' if datetime.fromtimestamp(aix_data['data']['tournament']['events'][0]['startAt']) > datetime.fromtimestamp(mrs_data['data']['tournament']['events'][0]['startAt']) else 'shieldpoke-mrs' 

def remove_thresholds_reached(thresholds, current_rate):
    while max(thresholds) >= current_rate:
        thresholds.remove(max(thresholds))
    return thresholds

def second_max(list_arg):
    new_list = set(list_arg)
    new_list.remove(max(new_list))
    return max(new_list)

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('!planning'):
        await message.channel.send(':flag_fr: Planning Smash Ultimate FR :flag_fr:\r\n:pushpin: https://smashultimate.fr/planning')

@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')    
    await annoucement()

    
def main():
    client.run(discordToken)

if __name__ == "__main__":
    main()