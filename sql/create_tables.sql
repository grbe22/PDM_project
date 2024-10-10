CREATE TABLE user(
    user_id INT PRIMARY KEY,
    username VARCHAR(16) UNIQUE,
    email VARCHAR(100) UNIQUE,
    password VARCHAR(30) UNIQUE,
    first_name VARCHAR(16),
    last_name VARCHAR(16),
    creation_date DATETIME,
    last_access_time DATETIME
);

CREATE TABLE following(
    follow_id INT PRIMARY KEY,
    follower_id INT FOREIGN KEY uid REFERENCES user.user_id,
    following_id INT FOREIGN KEY uid REFERENCES user.user_id
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
    user_id INT FOREIGN KEY user_id REFERENCES user.user_id,
    game_id INT FOREIGN KEY game_id REFERENCES game.game_id,
    start_time DATETIME,
    end_time DATETIME,
    uc1 CONSTRAINT (user_id, start_time) UNIQUE
);

CREATE TABLE platform(
    platform_id INT PRIMARY KEY,
    name VARCHAR(20)
);

CREATE TABLE release(
    release_id INT PRIMARY KEY,
    platform_id INT FOREIGN KEY platform_id REFERENCES platform.platform_id,
    game_id INT FOREIGN KEY game_id REFERENCES game.game_id,
    price FLOAT(3,2),
    release_date DATETIME
);

CREATE TABLE publishing(
    publishing_id INT PRIMARY KEY,
    game_id INT FOREIGN KEY game_id REFERENCES game.game_id,
    publisher_id INT FOREIGN KEY publisher_id REFERENCES publisher.publisher_id
    uc1 CONSTRAINT (game_id, publisher_id) UNIQUE
);

CREATE TABLE developing(
    developing_ID INT PRIMARY KEY,
    game_id INT FOREIGN KEY game_id REFERENCES game.game_id,
    developer_id INT FOREIGN KEY developer_id REFERENCES developer.developer_id,
    uc1 CONSTRAINT (game_id, developer_id) UNIQUE
);

CREATE TABLE game_genre(
    game_genre_id INT PRIMARY KEY,
    game_id INT FOREIGN KEY game_id REFERENCES game.game_id,
    genre_id INT FOREIGN KEY genre_id REFERENCES genre.genre_id,
    uc1 CONSTRAINT (game_id, genre_id) UNIQUE
);

CREATE TABLE collection(
    collection_id INT PRIMARY KEY,
    name VARCHAR(50),
    user_id INT FOREIGN KEY user_id REFERENCES user.user_id
);

CREATE TABLE rating(
    rating_id INT PRIMARY KEY,
    user_id INT FOREIGN KEY user_id REFERENCES user.user_id,
    game_id INT FOREIGN KEY game_id REFERENCES game.game_id,
    rating INT,
    rating_range CONSTRAINT (rating >= 1 and rating <= 5)
);

CREATE TABLE platform_owned_by_user(
    platform_owned_by_user_id INT PRIMARY KEY,
    user_id INT FOREIGN KEY user_id REFERENCES user.user_id,
    platform_id INT FOREIGN KEY platform_id REFERENCES platform.platform_id,
    uc1 CONSTRAINT (user_id, platform_id) UNIQUE,
);

CREATE TABLE game_in_collection(
    game_in_collection_id INT PRIMARY KEY,
    game_id INT FOREIGN KEY game_id REFERENCES game.game_id,
    collection_id INT FOREIGN KEY collection_id REFERENCES collection.collection_id,
    uc1 CONSTRAINT (game_id, collection_id) UNIQUE
);