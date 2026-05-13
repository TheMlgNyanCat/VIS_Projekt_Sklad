from db import execute

def get_all(search="", kategorie_id=None):
    sql = """
        SELECT z.id, z.nazev, k.nazev AS kategorie, k.id AS kategorie_id,
               z.jednotka, z.mnozstvi_na_sklade, z.min_mnozstvi, z.cena_za_jednotku
        FROM zbozi z
        JOIN kategorie k ON k.id = z.kategorie_id
        WHERE (%s = '' OR z.nazev ILIKE %s)
          AND (%s::int IS NULL OR z.kategorie_id = %s::int)
        ORDER BY z.nazev
    """
    like = f"%{search}%"
    kid = str(kategorie_id) if kategorie_id else None
    return execute(sql, (search, like, kid, kid), fetch='all')

def get_by_id(zbozi_id):
    return execute("SELECT * FROM zbozi WHERE id = %s", (zbozi_id,), fetch='one')

def create(kategorie_id, nazev, jednotka, min_mnozstvi, cena_za_jednotku):
    execute("""
        INSERT INTO zbozi (kategorie_id, nazev, jednotka, min_mnozstvi, cena_za_jednotku)
        VALUES (%s, %s, %s, %s, %s)
    """, (kategorie_id, nazev, jednotka, min_mnozstvi, cena_za_jednotku))

def update(zbozi_id, kategorie_id, nazev, jednotka, min_mnozstvi, cena_za_jednotku):
    execute("""
        UPDATE zbozi
        SET kategorie_id = %s, nazev = %s, jednotka = %s,
            min_mnozstvi = %s, cena_za_jednotku = %s, aktualizovano = NOW()
        WHERE id = %s
    """, (kategorie_id, nazev, jednotka, min_mnozstvi, cena_za_jednotku, zbozi_id))

def delete(zbozi_id):
    execute("DELETE FROM zbozi WHERE id = %s", (zbozi_id,))

def get_nizky_stav():
    return execute("SELECT * FROM nizky_stav", fetch='all')
