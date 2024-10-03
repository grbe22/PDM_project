"""
    Team 23 python handler for user commands.
    Takes input commands from the user & converts them to SQL commands.
    Pings the CS server with commands & expects results.
"""
import pycopg2


def main():
    username = None
    print(  """ Welcome to our wondrous database! Login with command (l)ogin <USERNAME>.\n
                If username does not exist, creates a new account.
            """)
    command = input()
    
if __name__ == "__main__":
    main()
