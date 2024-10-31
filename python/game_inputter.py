from dbcredentials import username,password,dbName # file containing login info
import psycopg2
from psycopg2 import Error
import json
from sshtunnel import SSHTunnelForwarder
from decimal import Decimal


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

        with open("games200.json", "r") as games200: # from steam storefront api
            gameslist = json.load(games200)

        with open("genre_and_score.json", "r") as genreandscore: # from steamspy api
            gamegenrelist = json.load(genreandscore)

        try:
            for i, gametext in enumerate(gameslist):
                gamedict = json.loads(gametext)
                if (gametext != 'null' and (gamedict[list(gamedict.keys())[0]]['success'] == True)):
                    insertgame = "insert into game (title, esrb) values (%s, %s)"
                    name = gamedict[list(gamedict.keys())[0]]['data']['name']
                    required_age = gamedict[list(gamedict.keys())[0]]['data']['required_age']
                    print(name)
                    curs.execute(insertgame, (name, required_age))
                    ggl = json.loads(gamegenrelist[i])
                    genrelist = list(ggl['tags'].keys())
                    insertgenre = """INSERT INTO genre (name)
                                        VALUES (%s)
                                        ON CONFLICT (name) DO NOTHING"""
                    insertgamegenre = """INSERT INTO game_genre (game_id, genre_id)
                                        VALUES (%s, %s)"""
                    try: # for entering in genre and game_genre
                        for genre in genrelist:
                            curs.execute(insertgenre, (genre,))
                            curs.execute("select genre_id from genre where name = %s", (genre,))
                            gen_id = curs.fetchone()[0]
                            curs.execute("select game_id from game where title = %s", (name,))
                            gam_id = curs.fetchone()[0]
                            curs.execute(insertgamegenre, (gam_id, gen_id))
                            curs.execute("select * from game_genre where game_id = %s", (gam_id,))
                    except Exception as e:
                        print(e)
                    
                    dev_list = gamedict[list(gamedict.keys())[0]]['data'].get('developers', ())
                    insert_dev = """INSERT INTO developer (name)
                                        VALUES (%s)
                                        ON CONFLICT (name) DO NOTHING"""
                    insert_developing = """INSERT INTO developing (game_id, developer_id)
                                        VALUES (%s, %s)"""
                    try: # for entering in developer and developing
                        for dev in dev_list:
                            curs.execute(insert_dev, (dev,))
                            curs.execute("select developer_id from developer where name = %s", (dev,))
                            gen_id = curs.fetchone()[0]
                            curs.execute("select game_id from game where title = %s", (name,))
                            gam_id = curs.fetchone()[0]
                            curs.execute(insert_developing, (gam_id, gen_id))
                    except Exception as e:
                        print(e)

                    pub_list = gamedict[list(gamedict.keys())[0]]['data'].get('publishers', ())
                    insert_pub = """INSERT INTO publisher (name)
                                        VALUES (%s)
                                        ON CONFLICT (name) DO NOTHING"""
                    insert_publishing = """INSERT INTO publishing (game_id, publisher_id)
                                        VALUES (%s, %s)"""
                    try: # for entering in publisher and publishing
                        for pub in pub_list:
                            curs.execute(insert_pub, (pub,))
                            curs.execute("select publisher_id from publisher where name = %s", (pub,))
                            gen_id = curs.fetchone()[0]
                            curs.execute("select game_id from game where title = %s", (name,))
                            gam_id = curs.fetchone()[0]
                            curs.execute(insert_publishing, (gam_id, gen_id))
                    except Exception as e:
                        print(e)
                    
                    insert_release = """INSERT INTO release (platform_id, game_id, price, release_date) 
                                        VALUES (%s, %s, %s, %s)"""
                    try: # for entering in release (all prices/dates across 3 platforms are the same)
                        cents = gamedict[list(gamedict.keys())[0]]['data'].get("price_overview", {"final":0})['final']
                        price = Decimal(cents)/Decimal(100)
                        release_date = gamedict[list(gamedict.keys())[0]]['data']['release_date']['date']
                        curs.execute("select game_id from game where title = %s", (name,))
                        game_id = curs.fetchone()[0]

                        curs.execute(insert_release, (1, game_id, price, release_date)) # windows
                        curs.execute(insert_release, (2, game_id, price, release_date)) # mac
                        curs.execute(insert_release, (3, game_id, price, release_date)) # linux
                        
                    except Exception as e:
                        print(e)


                    

            conn.commit()
            print("success")

        except Exception as e:
            print(e)
            conn.rollback()  # Rollback the transaction


        # conn.commit()
        conn.close()
except:
    print("Connection failed")
