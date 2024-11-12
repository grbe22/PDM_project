"""
    Team 23 python handler for user commands.
    Takes input commands from the user & converts them to SQL commands.
    Pings the CS server with commands & expects results.
"""
import psycopg2
from sshtunnel import SSHTunnelForwarder
import argparse
from datetime import datetime, timedelta
import numpy as np

user:str = None
userid:int = None
server:SSHTunnelForwarder = None
cursor = None
connection = None

# takes cur, conn, username.
# if user not found, returns none.
# if found, returns the username.
def login(conn, cur, username):
    global user
    global userid
    cur.execute(f"""
        SELECT username, user_id from p320_23.user where username = '{username}';
    """)
    feedback = cur.fetchone()
    if feedback == None:
        print("No user was found with that name.")
        return
    print("User found. Logged in.")
    user = feedback[0]
    userid = feedback[1]

    # updates the user's last-access by updating their last_access_time to datetime.now().
    now = datetime.now()
    cur.execute(f""" 
        update p320_23.user
        set last_access_time = '{now}'
        where user_id = {userid};
    """)
    conn.commit()

    return feedback

# Requires many arguments.
# in order: username, email, password, first_name, last_name, creation_date, and last_accessed_date.
# creation and last_accessed_date can be generated in the method.
def create_account(conn, cur, username, email, password, f_n, l_n):
    cur.execute(f"""
        select * from p320_23.user where username = '{username}'
                """)
    if cur.fetchone() != None:
        print(f"User {username} already exists.")
        return
    now = datetime.now()
    cur.execute(f"""
        insert into p320_23.user(username, email, password, first_name, last_name, creation_date, last_access_time) values
                                ('{username}', '{email}', '{password}', '{f_n}', '{l_n}', '{now}', '{now}')
                """)
    conn.commit()
    login(conn, cur, username)

# signs you out :)
def logout(conn, cur):
    global user
    global userid
    user = None
    userid = None
    print("See you later!")

# Games MUST be a list of game ids.
def create_collection(conn, cur, name, games):
    print(user, userid)
    cur.execute(f"""
        select * from p320_23.collection where name = '{name}' and
        user_id = {userid};
    """)
    if cur.fetchone() != None:
        print(f"Collection named {name} already exists for this user.")
        return
    cur.execute(f"""
        insert into p320_23.collection(name, user_id) values ('{name}',
        {userid});
    """)
    conn.commit()

    # grabs the autogenerated id from this collection.
    cur.execute(f"""
        select collection_id from p320_23.collection where name = '{name}' and user_id = {userid};
    """)
    coll_id = cur.fetchone()[0]
    print(f"Collection {name} created for {user} with new id {coll_id}.")
    conn.commit()
    # adds each game, one by one, to the game_in_collection list.
    for i in games:
        a_update_collection(conn, cur, coll_id, i)
    # returns the collection id
    return coll_id

# gets all collections belonging to the current user.
# todo: add playtime once implementing play sessions.
def get_all_collections(conn, cur):
    cur.execute(f"""
        select name, collection_id from p320_23.collection where user_id = {userid}; 
    """)
    arr = []
    game_ids = []
    for i in cur.fetchall():
        arr.append([i[0], i[1]])
        # this function also requires all of the games in the list, by name
        cur.execute(f"""
            select count(game_id) from p320_23.game_in_collection where collection_id = {i[1]};
        """)
        arr[-1].append(str(cur.fetchone()[0]))
    for i in range(0, len(arr)):
        cur.execute(f"""
select game_id from p320_23.game_in_collection where collection_id = {arr[i][1]}
                    """)
        cur.execute(f"""
            select sum(end_time - start_time) from p320_23.playtime where user_id = {userid} and game_id in
            (select game_id from p320_23.game_in_collection where collection_id = {arr[i][1]});
        """)
        arr[i].pop(1)
        elapsed_time = np.sum(cur.fetchall())
        print("datetime: ", elapsed_time)
        if elapsed_time == None:
            hours, remainder = 0, 0
        else:
            hours, remainder = divmod(elapsed_time.total_seconds(), 3600)
        minutes = remainder // 60
        arr[i].append(str(int(hours)) + ":" + str(int(minutes)))
    # arr should have n elements each with 4 values (todo: 3 currently).
    # in order, for each element, (name, collection_id, game_count, total_playtime)
    return arr

# deletes all dependencies of this collection, then the collection itself.
def delete_collection(conn, cur, collection_name):
    cur.execute(f"""
        select * from p320_23.collection where user_id = {userid} and name = '{collection_name}';
    """)
    if cur.fetchone() == None:
        print("Collection does not exist. No changes were made.")
        return
    # start by deleting the game_in_collection entries with this id
    cur.execute(f"""
        delete from p320_23.game_in_collection where collection_id = (select collection_id from p320_23.collection where user_id = {userid} and name = '{collection_name}');
    """)
    cur.execute(f"""
        delete from p320_23.collection where user_id = {userid} and name = '{collection_name}';
    """)
    conn.commit()
    print(f"Succesfully deleted collection {collection_name}.")

def find_game(conn, cur, args): # boy thats a lot of args
    # args is as follows:
    # 0. <name|platform|release_date|developer|publisher|playtime|ratings> 
    # 1. <VALUE> 
    # OPTIONAL
    # 2/3. sort by 
    # 4. <name|price|genre|release_year>
    # 5. <ascending|descending>
    
    if not(args[0] in ["name", "platform", "release_date", "developer", "publisher", "playtime", "ratings"]):
        print("Please specify properly which method you want to find the game through.")
        return
    
    if len(args) != 2:
        if len(args) != 5:#these args are supposed to be optinal and they currently break when trying to query
            print("improperly formatted argument length. Please make sure all elements are unspaced.")
            return
        if not(args[3] in ["name", "price", "genre", "release_year"]):
            print("Please specify properly the sorting mechanism.")
            return
        if not(args[4] in ["ascending", "descending"]):
            print("Please make sure to specify ascending or descending order.")
            return
    
    games = None
    game_list = None
    if args[0] == "name":
        game_list = f"""
            select game_id from p320_23.game where LOWER(title) like LOWER('%{args[1]}%')
        """

    elif args[0] == "platform":
        if not(args[1].lower() in ["windows", "mac", "linux"]):
            print("Platform not recognized.")
            return
        # grabs the game ids where 
        game_list = f"""
            select game_id from p320_23.release where platform_id =
            (select platform_id from p320_23.platform where LOWER(name) = LOWER('{args[1]}'))
        """
    
    elif args[0] == "release_date":
        game_list = f"""
            select distinct game_id from p320_23.release where cast(release_date as varchar) like '%{args[1]}%'
        """

    elif args[0] == "developer":
        game_list = f"""
            select game_id from p320_23.developing where developer_id =
            (select developer_id from p320_23.developer where LOWER(name) like '%{args[1]}%')
        """

    elif args[0] == "publisher":
        game_list = f"""
            select game_id from p320_23.publishing where publisher_id =
            (select publisher_id from p320_23.publisher where LOWER(name) like '%{args[1]}%')
        """
    
    elif args[0] == "playtime":
        game_list = f"""
            select g.game_id from p320_23.game g 
            join p320_23.playtime p on g.game_id = p.game_id
            where p.user_id = {userid}
            group by g.game_id, g.title
            order by sum(extract(epoch from (p.end_time - p.start_time)) / 3600) desc
            limit 10
        """
    
    elif args[0] == "ratings":
        game_list = f"""
            select game_id from p320_23.rating where user_id = {userid} and rating = cast({args[1]} as int)
        """
    
    kw = "asc"
    if len(args) == 5:
        if args[4] == "descending":
            kw = "desc"
        # name is default, no need to engage
        if args[3] == "price":
            # orders by price.
            cur.execute(f"""
                select title from p320_23.game where game_id in ({game_list}) order by
                (select min(price) from p320_23.release where game_id = game.game_id) {kw}
            """)
            print(cur.fetchall())
            return
        if args[3] == "genre":
            # orders by genre
            funct = ""
            if args[4] == "descending":
                funct = "max"
            else:
                funct = "min"
            cur.execute(f"""
                select title from p320_23.game where game_id in ({game_list}) order by
                (select {funct}(genre_id) from p320_23.game_genre where game_id = game.game_id)) {kw}
            """)
            print(cur.fetchall())
            return
        if args[3] == "release_year":
            # orders by release
            funct = ""
            if args[4] == "descending":
                funct = "max"
            else:
                funct = "min"
            cur.execute(f"""
                select title from p320_23.game where game_id in ({game_list}) order by
                (select {funct}(release_date) from p320_23.release where game_id = game.game_id) {kw}
            """)
            print(cur.fetchall())

    if args[0] == "playtime":
        kw = "desc"
        cur.execute(f"""
            select title from p320_23.game where game_id in ({game_list}) order by title {kw},
            (select min(release_date) from p320_23.release where game_id = game.game_id) {kw};
        """)
        print(cur.fetchall())
        return

    if len(args) == 2 or args[4] == "name":
        cur.execute(f"""
            select title from p320_23.game where game_id in ({game_list}) order by title {kw},
            (select min(release_date) from p320_23.release where game_id = game.game_id) {kw};
        """)
        print(cur.fetchall())
        return



    

# alternate update collection that takes an id instead of a name
def a_update_collection(conn, cur, cid, gname):
    cur.execute(f"""
            select game_id from p320_23.game where title = '{gname}';
        """)
        # validates that game exists
    try:
        game = cur.fetchone()[0]
    except:
        print(f"Game {game} not found.")
        return
    # verifies the intersection
    # throws a warning if user doesn't have the platform the game is on
    cur.execute(f"""
        select platform_id from p320_23.platform_owned_by_user where user_id = {userid}
        intersect
        select platform_id from p320_23.release where game_id = {game};
    """)
    if cur.fetchone() == None:
        if (input(f"You do not own any platforms {gname} is on. type 'y' to add anyway. ") != "y"):
            print(f"Skipping {gname}...")
            return
        print()

    cur.execute(f"""
        select game_id from p320_23.game_in_collection where collection_id = {cid} and game_id = {game};
    """)
    if cur.fetchone() != None:
        print(f"Game with ID {game} already exists in collection with ID {cid}.")
        return
    cur.execute(f"""
        insert into p320_23.game_in_collection (game_id, collection_id) values ({game}, {cid});
    """)
    conn.commit()
    print(f"Game with id {game} successfully inserted into collection with id {cid}")

# isAdd - if True, adds a new game. If False, do not... do that. Remove it.
def update_collection(conn, cur, isAdd, cname, gname):
    # validates that collection exists
    cur.execute(f"""
        select collection_id from p320_23.collection where user_id = {userid} and name = '{cname}';
    """)
    cid = cur.fetchone()

    if cid == None:
        print(f"Collection {cname} not found.")
        return
    cid = cid[0]
    cur.execute(f"""
        select game_id from p320_23.game where title = '{gname}';
    """)
    # validates that game exists
    try:
        game = cur.fetchone()[0]
    except:
        print(f"Game {game} not found.")
        return
    if isAdd:
        # verifies the intersection
        # throws a warning if user doesn't have the platform the game is on
        cur.execute(f"""
            if not exists(
            select platform_id from p320_23.platform_owned_by_user where user_id = {userid}
            intersect
            select platform_id from p320_23.release where game_id = {game};)
            then
            raiseerror('game intersection not found')
        """)
        if cur.fetchone() == None:
            if (input(f"You do not own any platforms {game} is on. type 'y' to ") != "y"):
                print(f"Skipping {game}...")
                return
            print()

        cur.execute(f"""
            select game_id from p320_23.game_in_collection where collection_id = {cid} and game_id = {game};
        """)
        if cur.fetchone() != None:
            print(f"Game with ID {game} already exists in collection with ID {cid}.")
            return
        cur.execute(f"""
            insert into p320_23.game_in_collection (game_id, collection_id) values ({game}, {cid});
        """)
        conn.commit()
        print(f"Game with id {game} successfully inserted into collection with id {cid}")
    else:
        cur.execute(f"""
            select * from p320_23.game_in_collection where collection_id = {cid} and game_id = {game};
        """)
        if cur.fetchone() == None:
            print(f"Game with id {game} does not exist in collection with ID {cid}.")
        else:
            cur.execute(f"""
                delete from p320_23.game_in_collection where collection_id = {cid} and game_id = {game};
            """)
            conn.commit()
            print(f"Successfully removed game {game} from collection {cid}.")

# if a collection exists, rename it.
# otherwise, reject.
def update_collection_name(conn, cur, oldName, newName):
    cur.execute(f"""
        select * from p320_23.collection where name = '{oldName}' and user_id = {userid};
    """)
    if cur.fetchone() == None:
        print("No collection was found with that name.")
        return
    cur.execute(f"""
        select * from p320_23.collection where name = '{newName}' and user_id = {userid};
    """)
    if cur.fetchone() != None:
        print(f"Collection with new name {newName} already exists.")
        return
    cur.execute(f"""
        update p320_23.collection set name = '{newName}';
    """)
    conn.commit()
    print(f"Sucessfully renamed collection {oldName} into {newName}")

# takes the userid, finds the gameid, and posts a rating (if rating in 1, 2, 3, 4, 5).
# updates ratings where they already exist.
def rate(conn, cur, gamename, rating):
    if not(rating in ["1", "2", "3", "4", "5"]):
        print("Invalid rating value.")
        return
    cur.execute(f"""
        select game_id from p320_23.game where title = '{gamename}';
    """)
    g_id = cur.fetchone()[0]
    if g_id == None:
        print("Game not found.")
        return
    cur.execute(f"""
        select * from p320_23.rating where user_id = {userid} and game_id = {g_id};
    """)
    if cur.fetchone() != None:
        cur.execute(f"""
            update p320_23.rating set rating = {rating} where game_id = {g_id} and user_id = {userid};
        """)
        conn.commit()
        print("Updated rating.")
    else:
        cur.execute(f"""
            insert into p320_23.rating(user_id, game_id, rating) values ({userid}, {g_id}, {rating});
        """)
        conn.commit()
        print("New rating created.")

# start and end are datetime objects
# game is assumedly a name
def play(conn, cur, game, start, end):
    cur.execute(f"""
        select game_id from p320_23.game where title = '{game}'
    """)
    g_id = cur.fetchone()[0]
    if g_id == None:
        print("Game not found.")
        return
    
    # adds a playsession to the list.
    cur.execute(f"""
        insert into p320_23.playtime(user_id, game_id, start_time, end_time)
        values ({userid}, {g_id}, '{start}', '{end}');
    """)
    conn.commit()
    print("Logged playtime.")

# calls play with end being now, and the beginning being time minutes away.
def play_with_duration(conn, cur, game, time):
    time = int(time)
    play(conn, cur, game, datetime.now() - timedelta(minutes = time), datetime.now())

# Takes a follower (the logged in user) and a followee.
# creates a connection if none exists.
# prints to console if it was successful or not.
def follow(conn, cur, followee):
    cur.execute(f"""
        SELECT * from following where
        follower_id = {userid} and 
        following_id = (select user_id from p320_23.user where username = '{followee}');
    """)
    if cur.fetchone() != None:
        print(f"You are already following {followee}.")
        return;
    cur.execute(f"""
        INSERT INTO following(follower_id, following_id) VALUES 
            ({userid}, 
            (SELECT user_id FROM p320_23.user WHERE username='{followee}'));
    """)
    conn.commit()
    print(f"Successfully followed {followee}")

# gets users by a partial email. It can contain the partial email anywhere in the email string.
def get_users_by_email(conn, cur, p_email):
    cur.execute(f"""
        select username, email from p320_23.user where LOWER(email) like LOWER('%{p_email}%'); 
    """)
    return cur.fetchall()

# Takes a follower (the logged in user) and a followee.
# deletes a connection if it exists.
# prints to console outcome - successful or not.
def unfollow(conn, cur, followee):
    cur.execute(f"""
        select * from p320_23.following where
        follower_id = {userid} and 
        following_id = (select user_id from p320_23.user where username = '{followee}');
    """)
    if cur.fetchone() == None:
        print(f"No changes were made. You were not already following {followee}.")
        return
    cur.execute(f""" 
        delete from p320_23.following where 
        follower_id = {userid} and
        following_id = (select user_id from p320_23.user where username = '{followee}');
    """)
    conn.commit()
    print(f"Successfully unfollowed {followee}")

# takes a platform name, and adds it to the user's platforms.
# if platform does not exist, return an error message.
def add_platform(conn, cur, platform):
    cur.execute(f"""
        select platform_id from p320_23.platform where name = '{platform}';
    """)
    dbloc = cur.fetchone()[0]
    if dbloc == None:
        print("Platform not found in database.")
        return
    cur.execute(f"""
        select * from p320_23.platform_owned_by_user where user_id = {userid} and platform_id = {dbloc}
    """)
    if cur.fetchone() != None:
        # it already catches duplicats, but I just want to get the user their error message.
        print("Platform already owned by user.")
        return
    
    cur.execute(f"""
        insert into p320_23.platform_owned_by_user (user_id, platform_id) values
                ({userid}, {dbloc})
    """)
    conn.commit()
    print(f"Successfully added {platform} to your platforms.")

# takes a platform name, and removes it to the user's platforms.
# if platform does not exist, or the user does not have that platform, return an error message.
def remove_platform(conn, cur, platform):
    cur.execute(f"""
        select platform_id from p320_23.platform where name = '{platform}';
    """)
    dbloc = cur.fetchone()[0]
    if dbloc == None:
        print("Platform not found in database.")
        return
    
    cur.execute(f"""
        select * from p320_23.platform_owned_by_user where user_id = {userid} and platform_id = {dbloc}
    """)
    if cur.fetchone() == None:
        # it already catches duplicats, but I just want to get the user their error message.
        print("Platform already owned by user.")
        return
    
    cur.execute(f"""
        delete from p320_23.platform_owned_by_user where user_id = {userid} and platform_id = {dbloc}
    """)
    conn.commit()
    print(f"Succesfully removed {platform} from your platforms.")


# prints the number of people you follow
def following_count(conn, cur):
    cur.execute(f"""
        select count(following_id) from p320_23.following where follower_id = {userid}
    """)
    print("You are following", cur.fetchone()[0], "users.")


# print the number of people following you
def follower_count(conn, cur):
    cur.execute(f"""
        select count(follower_id) from p320_23.following where following_id = {userid}
    """)
    print("You have", cur.fetchone()[0], "followers.")


# print the number of collections you have
def collection_count(conn, cur):
    cur.execute(f"""
        select count(name) from p320_23.collection where user_id = {userid}
    """)
    print("You have", cur.fetchone()[0], "collections.")

# get the top games (by rating)
def get_top_games(conn, cur):
    cur.execute(f"""
        select rating, title from p320_23.rating
        inner join
        p320_23.game on p320_23.rating.game_id = p320_23.game.game_id
        where user_id = {userid}
        order by rating desc, title desc
        limit 10;
    """)
    print(cur.fetchall())

# calls some good, healthy functions
def get_profile(conn, cur):
    follower_count(conn, cur)
    following_count(conn, cur)
    collection_count(conn, cur)
    get_top_games(conn, cur)

# generates count random users in the database.
import random
import numpy
def gen_random_users(conn, cur):
    first_names = ["Aurora", "Carlyle", "Franklin", "Helen", "Jeek", "Lois", "Nevada", "Pater", "Rusty", "Thompson", "Vert", "Xander", "Zygote"]
    last_names = ["Batter", "Dorph", "Erickson", "Ganges", "Intract", "Konnors", "Moot", "Olene", "Quart", "Stevens", "Umbridge", "Waylan", "Yelnats"]
    # taken from the most common passwords 2011 - 2024, wikipedia, then split in half
    passwords_part_1 = ["pass", "1234", "qwe", "1q2w", "2pass", "monk", "shad", "mast", "ilove", "mich", "super", "zaq1", "aze"]
    passwords_part_2 = ["word", "5678", "rty", "3e4r", "word2", "eys", "ows", "erful", "you", "ael", "man", "zaq1", "rty2"]
    for i in range(0, len(first_names)):
        for j in range(0, len(last_names)):
            # 75% chance to create a user of this name
            # randint is inclusive of a & b
            if random.randint(0, 3) == 0:
                continue
            fn = first_names[i]
            ln = last_names[j]
            # generates a random password
            pw = passwords_part_1[random.randint(0, len(passwords_part_1) - 1)] + passwords_part_2[random.randint(0, len(passwords_part_2) - 1)]
            # idk why I'm doing this
            if random.randint(0, 6) == 0:
                pw = ln + pw
            elif random.randint(0, 6) == 0:
                pw = pw + ln
            
            # emails
            email = ""
            if random.randint(0, 1) == 0:
                email += fn
                path = random.randint(0, 2)
                if path == 0:
                    email += "_" + ln
                elif path == 1:
                    email += "-" + ln
                else:
                    email += ln
            else:
                email += ln
                path = random.randint(0, 2)
                if path == 0:
                    email += "_" + fn
                elif path == 1:
                    email += "-" + fn
                else:
                    email += fn
                
            if random.randint(0, 1) == 0:
                email += str(random.randint(1, 4000))

            path = random.randint(0, 3)
            # most common email domains
            if path == 0:
                email += "@gmail.com"
            if path == 1:
                email += "@yahoo.net"
            if path == 2:
                email += "@outlook.com"
            if path == 3:
                email += "@hotmail.net"

            username = fn + ln + str(random.randint(100, 999))
            username = username[:16]
            # create account also logs you in so we don't have to deal with that    
            create_account(conn, cur, username, email, pw, fn, ln)
            a = random.randint(0, 2)
            b = random.randint(0, 2)
            consoles = ["windows", "mac", "linux"]
            # has a 33% chance of only having one console assigned to a user
            if a == b:
                add_platform(conn, cur, consoles[a])
            else:
                add_platform(conn, cur, consoles[a])
                add_platform(conn, cur, consoles[b])

def genFollowers(conn, cur):
    cur.execute(f"""
        select username from p320_23.user
    """)
    all_users = cur.fetchall()[10:]
    for i in all_users:
        login(conn, cur, i[0])

        random_count = random.randint(0, 10)
        for j in range(0, random_count):
            k = random.randint(0, len(all_users) - 1)
            follow(conn, cur, all_users[k][0])

def genRatings(conn, cur):
    cur.execute(f"""
        select username from p320_23.user""")
    all_users = cur.fetchall()
    cur.execute(f"""
        select title from p320_23.game""")
    all_games = cur.fetchall()
    for i in all_users:
        login(conn, cur, i[0])
        rating_count = random.randint(0, 6)
        if rating_count > 4:
            rating_count = random.randint(4, 15)
        # some users are more generous than others
        skew = random.randint(0, 2)
        for j in range(0, rating_count):
            k = random.randint(0, len(all_games) - 1)
            ratee = random.randint(1, 3) + skew
            rate(conn, cur, all_games[k][0], str(ratee))

def genPlaytime(conn, cur):
    cur.execute(f"""
        select username from p320_23.user""")
    all_users = cur.fetchall()
    cur.execute(f"""
        select title from p320_23.game""")
    all_games = cur.fetchall()
    for i in all_users:
        cur_game = all_games[random.randint(0, len(all_games) - 1)][0]
        login(conn, cur, i[0])
        play_with_duration(conn, cur, cur_game, random.randint(20, 240))
        

def checkCommandsList(connection, cursor, command):
    
    command = command.split()
    
    if userid == None:
        if command[0] != "login" and command[0] != "help" and (command[0] != "create" and command[1] != "account"):
            print ("You are not signed in. Use login <USERNAME>, create_account <USERNAME>, or help for all commands.")
            return
    else:
        if command[0] == "login" or command[0] == "create_account":
            print("You are already logged in. Logout using command logout.")
            return
    
    match (command[0]):
        case "help":
            # print help command
            print("""help
    - lists user commands.
login <USERNAME>
    - logs in to account. enables all commands below this line.
create account <USERNAME>
    - creates a new account. More fields will be prompted.
logout
    - logs out of user account.
profile
    - views your profile
create collection <NAME> <game_1> <game_2> <game_3> ...
    - creates a collection linked to the user with name NAME and contents gamei.
view collections
    - prints the list of collections associated with the user, ascending order. returns collection name, # of games, and total playtime.
find game <name|platform|release_date|developer|publisher|playtime|ratings> <VALUE> sort by <name|price|genre|release_year> <ascending|descending>
    - finds a game by VALUE (specified by type) and sorts by field (asc / desc). Sorted ascending by name then release date by default.
update collection <C_NAME> <add|remove> <G_NAME>
    - adds / removes game with name G_NAME to collection C_NAME.
update collection <C_NAME> <N_NAME>
    - updates collection named C_NAME to N_NAME.
rate <NAME> <1|2|3|4|5>
    - rates game with name NAME between 1-5 stars.
play <NAME> <MINUTES>
    - logs a play session with start and end date - ends from command, starts MINUTES minutesbefore.
follow <NAME>
    - follows a user by their username.
follow remove <NAME>
    - unfollows a user by their username.
find user <EMAIL>
    - finds a user by their email (partial or total)
delete collection <COLLECTION>
    - deletes a collection by its name
add platform <PLATFORM>
    - adds a platform to your repertiore
remove platform <PLATFORM>
    - removes a platform from your repertoire
""")
        case "login":
            print(command[1])
            login(connection, cursor, command[1])
        case "logout":
            logout(connection, cursor)
        case "profile":
            get_profile(connection, cursor)
        case "create":
            match (command[1]):
                case "collection":
                    create_collection(connection, cursor, command[2], command[3::])      
                case "account":
                    x = input("Please enter your email address: ")
                    a = input("please enter your password: ")
                    y = input("Please enter your first name: ")
                    z = input("Please enter your last name: ")
                    print(command)
                    create_account(connection, cursor, command[2], x, a, y, z)
        case "view":
            match (command[1]):
                case "collections":
                    print(get_all_collections(connection, cursor))
        case "find":
            match (command[1]):
                case "game":
                    find_game(connection, cursor, command[2:])
                case "user":
                    print(get_users_by_email(connection, cursor, command[2]))
        case "update":
            match (command[1]):
                case "collection":
                    if (command[2] == "name"):
                        update_collection_name(connection, cursor, command[3], command[4])
                    else:
                        if (command[3] == "add"):
                            update_collection(connection, cursor, True, command[2], command[4])
                        elif (command[3] == "remove"):
                            update_collection(connection, cursor, False, command[2], command[4])
                        else:
                            print("Neither add or remove found.")
        case "rate":
            rate(connection, cursor, command[1], command[2])
        case "play":
            play_with_duration(connection, cursor, command[1], command[2])
        case "delete":
            if (command[1] == "collection"):
                delete_collection(connection, cursor, command[2])
        case "follow":
            if (command[1] == "remove"):
                unfollow(connection, cursor, command[2])
            else:
                follow(connection, cursor, command[1])
        case "unfollow":
            unfollow(connection, cursor, command[1])
        case "add":
            if command[1] == "platform":
                add_platform(connection, cursor, command[2])
        case "remove":
            if command[1] == "platform":
                remove_platform(connection, cursor, command[2])
        case _:
            print("User may not be logged in. Double check spelling of command or login before running other commands.")
    return


def main(connection, cursor, server):
    # don't run this
    # it's already been run
    # there's a chance (slim) for duplicate users to be generated.
    # so yeah
    # don't run it
    # gen_random_users(connection, cursor)
    # exit()
    # don't run this is over
    # run this vvv
    print(  """Welcome to our wonderful database! Login with command login <USERNAME>.\nIf username does not exist, creates a new account.
            """)

    try:
        while True:
            command = input()
            if command.lower() == "quit":
                break
            checkCommandsList(connection, cursor, command)
    except Exception as e:
        # fail cleanly
        cursor.close()
        connection.close()
        server.close()
        raise e
    else:
        cursor.close()
        connection.close()
    print("Goodbye!")


def connectToStarbug():
    with open("login.env") as login: # login.env is gitignored, so it's safe (enough) to put credentials in
        starbugUsername = login.readline().split()[-1]
        starbugPassword = login.readline().split()[-1]
    server = SSHTunnelForwarder(('starbug.cs.rit.edu', 22),
                            ssh_username=starbugUsername,
                            ssh_password=starbugPassword,
                            remote_bind_address=('127.0.0.1', 5432))
    server.start()
    print("SSH tunnel established")
    params = {
        'database': "p320_23",
        'user': starbugUsername,
        'password': starbugPassword,
        'host': 'localhost',
        'port': server.local_bind_port
    }

    connection = psycopg2.connect(**params)
    cursor = connection.cursor()
    
    print("Database connection established")
    main(connection, cursor, server)
    # Use cursor.execute() to perform SQL queries;
    # use connection.commit() to make any changes permanent;
    # use cursor.fetchall() to get the results of a SELECT query;

        
if __name__ == "__main__":
    connectToStarbug()
