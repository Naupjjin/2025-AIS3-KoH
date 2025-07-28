-- Tables Team 
CREATE TABLE IF NOT EXISTS teams (
    team_id INTEGER PRIMARY KEY CHECK (team_id >= 0 AND team_id <= 10),
    team_token TEXT NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE
);

INSERT INTO teams (team_id, team_token, is_admin) VALUES
    (0, '91730e66027d966b74f8827c702a7bed', TRUE);

INSERT INTO teams (team_id, team_token, is_admin) VALUES
    (1, '50b0eba76d7db935', FALSE),
    (2, '6f8440739d0fadd4', FALSE),
    (3, 'a5e644862d50a868', FALSE),
    (4, 'a29ecef795013e98', FALSE),
    (5, 'c51b015f5bf554a1', FALSE),
    (6, 'abbcdad59a97e2ad', FALSE),
    (7, '6ac6c8b1b29e6058', FALSE),
    (8, 'c633e634a0c53770', FALSE),
    (9, '062dd1e4b830abae', FALSE);


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


