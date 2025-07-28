CREATE TABLE Team (
    id INT PRIMARY KEY,
    scoreboard_score INT,
    password TEXT
);

CREATE TABLE Script (
    id SERIAL PRIMARY KEY,
    content TEXT,
    teamid INT REFERENCES Team(id),
    upload_time DATE
);

/*
CREATE TABLE Round1 (
    id SERIAL PRIMARY KEY,
    teamid INT REFERENCES Team(id),
    game_score INT
);
*/