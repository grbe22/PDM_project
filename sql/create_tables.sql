-- fun facts:
-- field REFERENCES table(field) instead of field REFERENCES table.field
-- constraints have to have unique names across tables (i.e. 2 different tables can't have a constraint of the same name)
-- NUMERIC in postgresql is how you specify decimal precision, not FLOAT

CREATE TABLE "user"( -- quotes b/c user is a keyword in sql... but it's probably fine to use it as a table name still
    user_id INT PRIMARY KEY,
    username VARCHAR(16) UNIQUE,
    email VARCHAR(100) UNIQUE,
    password VARCHAR(30) UNIQUE,
    first_name VARCHAR(16),
    last_name VARCHAR(16),
    creation_date TIMESTAMP,
    last_access_time TIMESTAMP
);

CREATE TABLE following(
    follow_id INT PRIMARY KEY,
    follower_id INT REFERENCES "user"(user_id),
    following_id INT REFERENCES "user"(user_id)
);

CREATE TABLE genre(
    genre_id INT PRIMARY KEY,
    name VARCHAR(25)
);

CREATE TABLE game(
    game_id INT PRIMARY KEY,
    title VARCHAR(50),
    esrb VARCHAR(3)
);

CREATE TABLE developer(
    developer_id INT PRIMARY KEY,
    name VARCHAR(50)
);

CREATE TABLE publisher(
    publisher_id INT PRIMARY KEY,
    name VARCHAR(50)
);

CREATE TABLE playtime(
    play_id INT PRIMARY KEY,
    user_id INT REFERENCES "user"(user_id),
    game_id INT REFERENCES game(game_id),
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    CONSTRAINT user_playtime_unique UNIQUE (user_id, start_time)
);

CREATE TABLE platform(
    platform_id INT PRIMARY KEY,
    name VARCHAR(20)
);

CREATE TABLE release(
    release_id INT PRIMARY KEY,
    platform_id INT REFERENCES platform(platform_id),
    game_id INT REFERENCES game(game_id),
    price NUMERIC(5,2),
    release_date DATE
);

CREATE TABLE publishing(
    publishing_id INT PRIMARY KEY,
    game_id INT REFERENCES game(game_id),
    publisher_id INT REFERENCES publisher(publisher_id),
    CONSTRAINT game_publisher_unique UNIQUE (game_id, publisher_id)
);

CREATE TABLE developing(
    developing_ID INT PRIMARY KEY,
    game_id INT REFERENCES game(game_id),
    developer_id INT REFERENCES developer(developer_id),
    CONSTRAINT game_developer_unique UNIQUE (game_id, developer_id)
);

CREATE TABLE game_genre(
    game_genre_id INT PRIMARY KEY,
    game_id INT REFERENCES game(game_id),
    genre_id INT REFERENCES genre(genre_id),
    CONSTRAINT game_genre_unique UNIQUE (game_id, genre_id)
);

CREATE TABLE collection(
    collection_id INT PRIMARY KEY,
    name VARCHAR(50),
    user_id INT REFERENCES "user"(user_id)
);

CREATE TABLE rating(
    rating_id INT PRIMARY KEY,
    user_id INT REFERENCES "user"(user_id),
    game_id INT REFERENCES game(game_id),
    rating INT,
    CONSTRAINT rating_range CHECK (rating >= 1 and rating <= 5)
);

CREATE TABLE platform_owned_by_user(
    platform_owned_by_user_id INT PRIMARY KEY,
    user_id INT REFERENCES "user"(user_id),
    platform_id INT REFERENCES platform(platform_id),
    CONSTRAINT user_platform_unique UNIQUE (user_id, platform_id)
);

CREATE TABLE game_in_collection(
    game_in_collection_id INT PRIMARY KEY,
    game_id INT REFERENCES game(game_id),
    collection_id INT REFERENCES collection(collection_id),
    CONSTRAINT game_collection_unique UNIQUE (game_id, collection_id)
);