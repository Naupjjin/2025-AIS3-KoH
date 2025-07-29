import psycopg2
import hashlib

def get_connection():
    return psycopg2.connect(
        dbname="koh-db",
        user="koh-admin",
        password="9c7f6b1b946aad1a6333dfb6e25f8d21945de8b33d5c67050cf66ec3a94b5dc2",
        host="127.0.0.1",    
        port="5432"
    )


def init_token_table():
    tokens = [
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
        (10, 'wearenpcyeahhhhh', False)
    ]

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("DELETE FROM teams;")

    for team_id, token, is_admin in tokens:
        hashed = hashlib.sha256(token.encode()).hexdigest()
        cur.execute(
            "INSERT INTO teams (team_id, team_token, is_admin) VALUES (%s, %s, %s);",
            (team_id, hashed, is_admin)
        )
    conn.commit()
    cur.close()
    conn.close()

