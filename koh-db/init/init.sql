CREATE TABLE IF NOT EXISTS teams (
    team_id INTEGER PRIMARY KEY CHECK (team_id >= 0 AND team_id <= 10),
    team_token CHAR(64) NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE
);


/*
每 round 建一個 table 會有 
turn object_type(0 代表本體 1 代表fork 2代表treashure) x座標 y座標 

CREATE TABLE objects_round_{n} (
    turn INTEGER NOT NULL CHECK (turn >= 0 AND turn < 200),
    object_type SMALLINT NOT NULL CHECK (object_type IN (0,1,2)),
    x INTEGER NOT NULL,
    y INTEGER NOT NULL
);


stores scripts

CREATE TABLE Script (
    id SERIAL PRIMARY KEY,
    content TEXT,
    teamid INT REFERENCES Team(id),
    upload_time DATE
);

每 round 建一個 score table  
CREATE TABLE scores_round_{n} (
    team_id INTEGER PRIMARY KEY,
    game_scores INTEGER NOT NULL
);
*/


