import psycopg2

conn = psycopg2.connect(
    host='localhost',
    dbname='sklad',
    user='postgres',
    password='XDXDlol69'  # sem dej své heslo
)
conn.set_client_encoding('UTF8')
cur = conn.cursor()

cur.execute("UPDATE zbozi SET nazev = 'Čisticí prostředek' WHERE id = 3")
cur.execute("UPDATE zbozi SET nazev = 'Čisticí ubrousky' WHERE id = 4")
cur.execute("UPDATE zbozi SET nazev = 'Kancelářský papír A4' WHERE id = 1")
cur.execute("UPDATE kategorie SET nazev = 'Kancelář' WHERE id = 1")
cur.execute("UPDATE kategorie SET nazev = 'Chemie' WHERE id = 2")
cur.execute("UPDATE kategorie SET nazev = 'Elektronika' WHERE id = 3")
cur.execute("UPDATE dodavatel SET kontakt = 'Jan Novák' WHERE id = 1")
cur.execute("UPDATE dodavatel SET kontakt = 'Eva Malá' WHERE id = 2")
cur.execute("UPDATE dodavatel SET kontakt = 'Ondřej Král' WHERE id = 3")
cur.execute("UPDATE odberatel SET kontakt = 'Petr Novák' WHERE id = 1")
cur.execute("UPDATE odberatel SET kontakt = 'Lenka Bílá' WHERE id = 2")

conn.commit()
cur.close()
conn.close()
print('Hotovo!')