from db import execute

def get_all(search="", typ=None):
    sql = """
        SELECT * FROM pohyby_detail
        WHERE (%s = '' OR zbozi ILIKE %s)
          AND (%s::typ_pohybu IS NULL OR typ = %s::typ_pohybu)
        LIMIT 200
    """
    like = f"%{search}%"
    return execute(sql, (search, like, typ, typ), fetch='all')

def create(zbozi_id, typ, mnozstvi, dodavatel_id=None, odberatel_id=None, poznamka=""):
    execute("""
        INSERT INTO pohyb (zbozi_id, typ, mnozstvi, dodavatel_id, odberatel_id, poznamka)
        VALUES (%s, %s::typ_pohybu, %s, %s, %s, %s)
    """, (zbozi_id, typ, mnozstvi, dodavatel_id or None, odberatel_id or None, poznamka or None))

def get_report(datum_od, datum_do):
    return execute("""
        SELECT * FROM pohyby_detail
        WHERE datum BETWEEN %s AND %s
        ORDER BY datum DESC
    """, (datum_od, datum_do), fetch='all')
