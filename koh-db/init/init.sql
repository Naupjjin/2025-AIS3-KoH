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



