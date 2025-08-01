import psycopg2
import hashlib
import os

DB_HOST = os.environ.get('DB_HOST', "127.0.0.1")
DB_PORT = os.environ.get('DB_PORT', "127.0.0.1")
DB_USER = os.environ.get("DB_USER", "koh-admin")
DB_PASS = os.environ.get("DB_PASS", "9c7f6b1b946aad1a6333dfb6e25f8d21945de8b33d5c67050cf66ec3a94b5dc2")

def get_connection():
    return psycopg2.connect(
        dbname="koh-db",
        user=DB_USER,
        password=DB_PASS,
        host=DB_HOST,    
        port="5432"
    )


def save_game_scores_to_db(round_num, scores_dict):
    conn = get_connection()
    cur = conn.cursor()

    for team_id, score in scores_dict.items():

        cur.execute("""
            INSERT INTO game_history (round, team_id, game_scores)
            VALUES (%s, %s, %s)
            ON CONFLICT (round, team_id)
            DO UPDATE SET game_scores = EXCLUDED.game_scores
        """, (round_num, team_id, score))

    conn.commit()
    cur.close()
    conn.close()


def update_score_for_round(round_number: int):
    ranking_score = {
        1: 30,
        2: 20,
        3: 15,
        4: 8, 5: 8,
        6: 3, 7: 3,
        8: 1, 9: 1, 10: 1
    }

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT team_id, game_scores FROM game_history WHERE round = %s ORDER BY game_scores DESC",
        (round_number,)
    )
    results = cur.fetchall()  # [(team_id, score), ...]

    prev_score = None
    rank = 0      
    real_rank = 0  
    for i, (team_id, score) in enumerate(results, start=1):
        if score == 0:
            cur.execute(
                "INSERT INTO scores (round, team_id, scores) VALUES (%s, %s, %s) "
                "ON CONFLICT (round, team_id) DO UPDATE SET scores = EXCLUDED.scores",
                (round_number, team_id, 0)
            )
            continue
        if score != prev_score:
            rank = i
            prev_score = score

        assign_score = ranking_score.get(rank, 0)

        cur.execute(
            "INSERT INTO scores (round, team_id, scores) VALUES (%s, %s, %s) "
            "ON CONFLICT (round, team_id) DO UPDATE SET scores = EXCLUDED.scores",
            (round_number, team_id, assign_score)
        )

    conn.commit()
    cur.close()
    conn.close()
