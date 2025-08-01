-- login
CREATE TABLE IF NOT EXISTS teams (
    team_id INTEGER PRIMARY KEY CHECK (team_id >= 0 AND team_id <= 10),
    team_token CHAR(64) NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE
);


-- store all rounds each team game score history
CREATE TABLE game_history (
    round INTEGER NOT NULL,
    team_id INTEGER NOT NULL,
    game_scores INTEGER NOT NULL,
    PRIMARY KEY (round, team_id)
);

-- store all rounds each team scores
CREATE TABLE scores (
    round INTEGER NOT NULL,
    team_id INTEGER NOT NULL,
    scores INTEGER NOT NULL,
    PRIMARY KEY (round, team_id)
);

-- stores scripts

CREATE TABLE scripts (
    round INTEGER NOT NULL,
    teamid INT NOT NULL,
    scripts TEXT NOT NULL,
    upload_time TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Taipei'),
    PRIMARY KEY (round, teamid)
);

INSERT INTO teams (team_id, team_token, is_admin) VALUES 
        (0, '91730e66027d966b74f8827c702a7bed', True),
        (1, '50b0eba76d7db935', False),
        (2, '6f8440739d0fadd4', False),
        (3, 'a5e644862d50a868', False),
        (4, 'a29ecef795013e98', False),
        (5, 'c51b015f5bf554a1', False),
        (6, 'abbcdad59a97e2ad', False),
        (7, '6ac6c8b1b29e6058', False),
        (8, 'c633e634a0c53770', False),
        (9, '062dd1e4b830abae', False),
        (10, 'wearenpcyeahhhhh', False);

INSERT INTO scripts (round, teamid, scripts)
SELECT r AS 1, t.team_id, 'ret #0'
FROM teams t
CROSS JOIN generate_series(1, 10) AS r;

