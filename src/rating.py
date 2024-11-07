from dbcredentials import username,password,dbName
import json
from decimal import Decimal
from sshtunnel import SSHTunnelForwarder
import psycopg2

with open("games200.json", "r") as games200:
    gameslist = json.load(games200)

with open("genre_and_score.json", "r") as genreandscore:
    gamegenrelist = json.load(genreandscore)

try:
    with SSHTunnelForwarder(('starbug.cs.rit.edu', 22),
                            ssh_username=username,
                            ssh_password=password,
                            remote_bind_address=('127.0.0.1', 5432)) as server:
        server.start()
        print("SSH tunnel established")
        params = {
            'database': dbName,
            'user': username,
            'password': password,
            'host': 'localhost',
            'port': server.local_bind_port
        }


        conn = psycopg2.connect(**params)
        curs = conn.cursor()
        print("Database connection established")

        for i, gametext in enumerate(gameslist):
            gamedict = json.loads(gametext)
            if (gametext != 'null' and (gamedict[list(gamedict.keys())[0]]['success'] == True)):
                name = gamedict[list(gamedict.keys())[0]]['data']['name']
                ggljson = json.loads(gamegenrelist[i])

                selectgame_id = """SELECT game_id FROM game where title = %s"""
                curs.execute(selectgame_id, (name,))
                game_id = curs.fetchone()[0]
                print(game_id)
                positivescore = ggljson['positive']
                negativescore = ggljson['negative']
                scorefloat = 0 if positivescore == 0 and negativescore == 0 else Decimal(positivescore)/(Decimal(negativescore)+Decimal(positivescore))
                print(scorefloat)

                setrating = """UPDATE game
                            SET aggregaterating = %s
                            WHERE game_id = %s"""
                curs.execute(setrating, (scorefloat, game_id))
                

        print("success")
        conn.commit()
        conn.close()

except:
    print("Connection failed")
