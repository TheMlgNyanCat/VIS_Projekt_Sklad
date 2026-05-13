from db import execute

# ── Dodavatel ──────────────────────────────────────────────

def get_all_dodavatele(search=""):
    like = f"%{search}%"
    return execute("""
        SELECT * FROM dodavatel
        WHERE %s = '' OR nazev ILIKE %s OR kontakt ILIKE %s
        ORDER BY nazev
    """, (search, like, like), fetch='all')

def create_dodavatel(nazev, kontakt, email, telefon):
    execute("INSERT INTO dodavatel (nazev, kontakt, email, telefon) VALUES (%s,%s,%s,%s)",
            (nazev, kontakt, email, telefon))

def update_dodavatel(did, nazev, kontakt, email, telefon):
    execute("UPDATE dodavatel SET nazev=%s, kontakt=%s, email=%s, telefon=%s WHERE id=%s",
            (nazev, kontakt, email, telefon, did))

def delete_dodavatel(did):
    execute("DELETE FROM dodavatel WHERE id=%s", (did,))

# ── Odberatel ──────────────────────────────────────────────

def get_all_odberatele(search=""):
    like = f"%{search}%"
    return execute("""
        SELECT * FROM odberatel
        WHERE %s = '' OR nazev ILIKE %s OR kontakt ILIKE %s
        ORDER BY nazev
    """, (search, like, like), fetch='all')

def create_odberatel(nazev, kontakt, email, telefon):
    execute("INSERT INTO odberatel (nazev, kontakt, email, telefon) VALUES (%s,%s,%s,%s)",
            (nazev, kontakt, email, telefon))

def update_odberatel(oid, nazev, kontakt, email, telefon):
    execute("UPDATE odberatel SET nazev=%s, kontakt=%s, email=%s, telefon=%s WHERE id=%s",
            (nazev, kontakt, email, telefon, oid))

def delete_odberatel(oid):
    execute("DELETE FROM odberatel WHERE id=%s", (oid,))

# ── Kategorie ──────────────────────────────────────────────

def get_all_kategorie():
    return execute("SELECT * FROM kategorie ORDER BY nazev", fetch='all')

def create_kategorie(nazev, popis=""):
    execute("INSERT INTO kategorie (nazev, popis) VALUES (%s,%s)", (nazev, popis))
