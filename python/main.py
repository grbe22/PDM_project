"""
    Team 23 python handler for user commands.
    Takes input commands from the user & converts them to SQL commands.
    Pings the CS server with commands & expects results.
"""
import psycopg2
from sshtunnel import SSHTunnelForwarder

def connectToStarbug():
    try:
        with open("login.env") as login: # login.env is gitignored, so it's safe (enough) to put credentials in
            starbugUsername = login.readline().split()[-1]
            starbugPassword = login.readline().split()[-1]
        with SSHTunnelForwarder(('starbug.cs.rit.edu', 22),
                                ssh_username=starbugUsername,
                                ssh_password=starbugPassword,
                                remote_bind_address=('127.0.0.1', 5432)) as server:
            server.start()
            print("SSH tunnel established")
            params = {
                'database': "p320_23",
                'user': starbugUsername,
                'password': starbugPassword,
                'host': 'localhost',
                'port': server.local_bind_port
            }

            conn = psycopg2.connect(**params)
            curs = conn.cursor()
            print("Database connection established")

            # Use curs.execute() to perform SQL queries;
            # use conn.commit() to make any changes permanent;
            # use curs.fetchall() to get the results of a SELECT query;
            
            return curs, conn
    except:
        print("Connection failed")
    return None, None

def login(username):
    ...

def logout(username):
    ...

def create_collection(username, name, games):
    ...

def view_collection(username):
    ...

def find_game(args): # boy thats a lot of args
    ...

def update_collection(isAdd, collection, game):
    ...

def update_collection_name(oldName, newName):
    ...

def rate(username, gamename, rating):
    ...

def play(username, game, start, end):
    ...

def follow(follower, followee):
    ...

def unfollow(follower, followee):
    ...

def checkCommandsList(username, command):
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
    if command[0] == "help":
        # Print help command!
        ...
    elif command[0] == "login":
        if len(command) != 2:
            print("Incorrect usage of login command. Should be login <USERNAME>.")
            return;
        if command[1] in dummy_usernames:
            username = command[1]
        else:
            x = input("Type (y)es to create account.")
            if x == "y" or x == "yes":
                dummy_usernames.append(command[1])
    elif username != None:
        # this doesn't really work without a database, but the general idea exists.
        if command[0] == "create" and command[1] == "collection":
            if command[2] in dummy_collections:
                print("Collection named", command[2], "already exists.")
                return;
            dummy_collections[command[2]] = username
            
    else:
        print("User not logged in. Double check spelling of command or login before running commands.")
        return


def main():
    username = None
    print(  """Welcome to our wondrous database! Login with command (l)ogin <USERNAME>.\nIf username does not exist, creates a new account.
            """)
    command = input().split()
    if len(command) != 2 or (command[0] != "l" and command[0] != "login"):
        print("Oh,,,,, you idiot..... I gave you ONE COMMAND. YOU NEED to sign in first! Use l or login, then your username! No spaces in username!")

        
if __name__ == "__main__":
    cursor, connection = connectToStarbug()
    main()
    cursor.close()
    connection.close()