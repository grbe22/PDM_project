"""
    Team 23 python handler for user commands.
    Takes input commands from the user & converts them to SQL commands.
    Pings the CS server with commands & expects results.
"""
import psycopg2
from sshtunnel import SSHTunnelForwarder
import argparse

user:str = None
server:SSHTunnelForwarder = None
cursor = None
connection = None

def login(connection, cursor, username):
    ...

def logout(connection, cursor, username):
    ...

def create_collection(connection, cursor, username, name, games):
    ...

def view_collection(connection, cursor, username):
    ...

def find_game(connection, cursor, args): # boy thats a lot of args
    ...

def update_collection(connection, cursor, isAdd, collection, game):
    ...

def update_collection_name(connection, cursor, oldName, newName):
    ...

def rate(connection, cursor, username, gamename, rating):
    ...

def play(connection, cursor, username, game, start, end):
    ...

def follow(connection, cursor, follower, followee):
    cursor.execute(f"""
        INSERT INTO following(follower_id, following_id) VALUES 
            ((SELECT user_id FROM users WHERE name={follower}), (SELECT user_id FROM users WHERE name={followee}))
    """)
    connection.commit()

def unfollow(connection, cursor, follower, followee):
    ...

def checkCommandsList(connection, cursor, username, command):
    """
    help
        - lists user commands.
    login <USERNAME>
        - logs in to account. enables all commands below this line.
    logout
        - logs out of user account.
    create collection <NAME> (game1, game2, game3...)
        - creates a collection linked to the user with name NAME and contents gamei.
    view collection
        - prints the list of collections associated with the user, ascending order. returns collection name, # of games, and total playtime.
    find game <(n)ame|(p)latform|(r)elease date|(d)eveloper|(pu)blisher|(pl)aytime|(ra)tings> <VALUE> sort by <(n)ame|(p)rice|(g)enre|(r)elease year> <(a)scending|(d)escending>
        - finds a game by VALUE (specified by type) and sorts by field (asc / desc). Sorted ascending by name then release date by default.
    update collection <(a)dd|(r)emove> <NAME1> <NAME2>
        - adds / removes game with name NAME2 to collection NAME1. returns a warning if collection is not owned by the user.
    update collection (n)ame <NAME1> <NAME2>
        - updates collection named NAME1 to NAME2. If NAME1 does not exist, or does not belong to user, return a warning.
    rate <NAME> <1|2|3|4|5>
        - rates game with name NAME between 1-5 stars.
    play <NAME> <START_DATE> <END_DATE>
        - logs a play session with start and end date. Total playtime is derived from this.
    follow <(u)sername|(e)mail> <NAME>
        - follows a user by either their email or username.
    follow remove <(u)sername|(e)mail> <NAME>
        - unfollows a user by either email or username.
    """

    # mock object
    dummy_usernames = ["Gabe", "Loser", "Gabe2"]
    dummy_collections = {"Loser_collection":"Loser", "Winner_collection":"Gabe", "Good_games":"Gabe"}
    
    command = command.split()
    match (command[0]):
        case "help":
            # print help command
            print("""help
                    - lists user commands.
                login <USERNAME>
                    - logs in to account. enables all commands below this line.
                logout
                    - logs out of user account.
                create collection <NAME> (game1, game2, game3...)
                    - creates a collection linked to the user with name NAME and contents gamei.
                view collection
                    - prints the list of collections associated with the user, ascending order. returns collection name, # of games, and total playtime.
                find game <(n)ame|(p)latform|(r)elease date|(d)eveloper|(pu)blisher|(pl)aytime|(ra)tings> <VALUE> sort by <(n)ame|(p)rice|(g)enre|(r)elease year> <(a)scending|(d)escending>
                    - finds a game by VALUE (specified by type) and sorts by field (asc / desc). Sorted ascending by name then release date by default.
                update collection <(a)dd|(r)emove> <NAME1> <NAME2>
                    - adds / removes game with name NAME2 to collection NAME1. returns a warning if collection is not owned by the user.
                update collection (n)ame <NAME1> <NAME2>
                    - updates collection named NAME1 to NAME2. If NAME1 does not exist, or does not belong to user, return a warning.
                rate <NAME> <1|2|3|4|5>
                    - rates game with name NAME between 1-5 stars.
                play <NAME> <START_DATE> <END_DATE>
                    - logs a play session with start and end date. Total playtime is derived from this.
                follow <(u)sername|(e)mail> <NAME>
                    - follows a user by either their email or username.
                follow remove <(u)sername|(e)mail> <NAME>
                    - unfollows a user by either email or username.
                """)
        case "login":
            login(connection, cursor, command[1])
        case "logout":
            logout(connection, cursor, command[1])
        case "create":
            match (command[1]):
                case "collection":
                    create_collection(connection, cursor, user, command[2], command[3::])
        case "view":
            match (command[1]):
                case "collection":
                    view_collection(connection, cursor, user)
        case "find":
            match (command[1]):
                case "game":
                    find_game(connection, cursor, command[2::])
        case "update":
            match (command[1]):
                case "collection":
                    if (command[2] == "name"):
                        update_collection_name(connection, cursor, command[3], command[4])
                    else:
                        update_collection(connection, cursor, command[2], command[3], command[4])
        case "rate":
            rate(connection, cursor, user, command[1], command[2])
        case "play":
            play(connection, cursor, user, command[1], command[2], command[3])
        case "follow":
            if (command[1] == "remove"):
                unfollow(connection, cursor, command[2], command[3])
            else:
                follow(connection, cursor, command[1], command[2])
        case _:
            print("User may not be logged in. Double check spelling of command or login before running other commands.")
    return


def main(cursor, connection):
    print(  """Welcome to our wondrous database! Login with command (l)ogin <USERNAME>.\nIf username does not exist, creates a new account.
            """)
    try:
        while True:
            command = input()
            if command.lower() == "quit":
                break
            checkCommandsList(connection, cursor, user, command)
    except Exception as e:
        # fail cleanly
        cursor.close()
        connection.close()
        server.close()
        raise e
    else:
        cursor.close()
        connection.close()
        server.close()
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
    main(cursor, connection)
    # Use cursor.execute() to perform SQL queries;
    # use connection.commit() to make any changes permanent;
    # use cursor.fetchall() to get the results of a SELECT query;

        
if __name__ == "__main__":
    connectToStarbug()
