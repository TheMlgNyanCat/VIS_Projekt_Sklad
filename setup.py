"""
Spusť tento skript pro vytvoření databázového schématu.
Použití: python setup.py
"""
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import os
import sys

load_dotenv()

DB_CONFIG = {
    "host":     os.getenv("DB_HOST", "localhost"),
    "port":     int(os.getenv("DB_PORT", 5432)),
    "dbname":   os.getenv("DB_NAME", "sklad"),
    "user":     os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", ""),
}

def run():
    print(f"Připojuji se k databázi '{DB_CONFIG['dbname']}'...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.set_client_encoding('UTF8')
        conn.autocommit = True
        cur = conn.cursor()
    except Exception as e:
        print(f"Chyba připojení: {e}")
        sys.exit(1)

    print("Vytvářím tabulky...")

    cur.execute("""
        CREATE EXTENSION IF NOT EXISTS "pgcrypto";

        CREATE TABLE IF NOT EXISTS kategorie (
            id          SERIAL PRIMARY KEY,
            nazev       VARCHAR(100) NOT NULL UNIQUE,
            popis       TEXT,
            vytvoreno   TIMESTAMP DEFAULT NOW()
        );

        CREATE TABLE IF NOT EXISTS dodavatel (
            id          SERIAL PRIMARY KEY,
            nazev       VARCHAR(150) NOT NULL,
            kontakt     VARCHAR(100),
            email       VARCHAR(150),
            telefon     VARCHAR(30),
            vytvoreno   TIMESTAMP DEFAULT NOW()
        );

        CREATE TABLE IF NOT EXISTS odberatel (
            id          SERIAL PRIMARY KEY,
            nazev       VARCHAR(150) NOT NULL,
            kontakt     VARCHAR(100),
            email       VARCHAR(150),
            telefon     VARCHAR(30),
            vytvoreno   TIMESTAMP DEFAULT NOW()
        );

        CREATE TABLE IF NOT EXISTS zbozi (
            id                  SERIAL PRIMARY KEY,
            kategorie_id        INTEGER NOT NULL REFERENCES kategorie(id) ON DELETE RESTRICT,
            nazev               VARCHAR(200) NOT NULL,
            jednotka            VARCHAR(20)  NOT NULL DEFAULT 'ks',
            mnozstvi_na_sklade  INTEGER      NOT NULL DEFAULT 0 CHECK (mnozstvi_na_sklade >= 0),
            min_mnozstvi        INTEGER      NOT NULL DEFAULT 0 CHECK (min_mnozstvi >= 0),
            cena_za_jednotku    NUMERIC(10,2) NOT NULL DEFAULT 0 CHECK (cena_za_jednotku >= 0),
            vytvoreno           TIMESTAMP DEFAULT NOW(),
            aktualizovano       TIMESTAMP DEFAULT NOW()
        );

        DO $$ BEGIN
            CREATE TYPE typ_pohybu AS ENUM ('prijem', 'vydej');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;

        CREATE TABLE IF NOT EXISTS pohyb (
            id              SERIAL PRIMARY KEY,
            zbozi_id        INTEGER      NOT NULL REFERENCES zbozi(id) ON DELETE RESTRICT,
            typ             typ_pohybu   NOT NULL,
            mnozstvi        INTEGER      NOT NULL CHECK (mnozstvi > 0),
            dodavatel_id    INTEGER      REFERENCES dodavatel(id) ON DELETE SET NULL,
            odberatel_id    INTEGER      REFERENCES odberatel(id) ON DELETE SET NULL,
            datum           TIMESTAMP    NOT NULL DEFAULT NOW(),
            poznamka        TEXT,
            CONSTRAINT chk_partner CHECK (
                (typ = 'prijem' AND dodavatel_id IS NOT NULL AND odberatel_id IS NULL)
                OR
                (typ = 'vydej'  AND odberatel_id IS NOT NULL AND dodavatel_id IS NULL)
            )
        );

        CREATE INDEX IF NOT EXISTS idx_zbozi_nizky_stav ON zbozi (mnozstvi_na_sklade);
        CREATE INDEX IF NOT EXISTS idx_pohyb_zbozi ON pohyb (zbozi_id);
        CREATE INDEX IF NOT EXISTS idx_pohyb_datum ON pohyb (datum DESC);
    """)

    print("Vytvářím trigger a views...")

    cur.execute("""
        CREATE OR REPLACE FUNCTION aktualizuj_mnozstvi()
        RETURNS TRIGGER AS $$
        BEGIN
            IF NEW.typ = 'prijem' THEN
                UPDATE zbozi
                SET mnozstvi_na_sklade = mnozstvi_na_sklade + NEW.mnozstvi,
                    aktualizovano      = NOW()
                WHERE id = NEW.zbozi_id;
            ELSIF NEW.typ = 'vydej' THEN
                IF (SELECT mnozstvi_na_sklade FROM zbozi WHERE id = NEW.zbozi_id) < NEW.mnozstvi THEN
                    RAISE EXCEPTION 'Nedostatek zboží na skladě (id: %)', NEW.zbozi_id;
                END IF;
                UPDATE zbozi
                SET mnozstvi_na_sklade = mnozstvi_na_sklade - NEW.mnozstvi,
                    aktualizovano      = NOW()
                WHERE id = NEW.zbozi_id;
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    cur.execute("""
        DROP TRIGGER IF EXISTS trg_pohyb_mnozstvi ON pohyb;
        CREATE TRIGGER trg_pohyb_mnozstvi
        AFTER INSERT ON pohyb
        FOR EACH ROW EXECUTE FUNCTION aktualizuj_mnozstvi();
    """)

    cur.execute("""
        CREATE OR REPLACE VIEW nizky_stav AS
        SELECT z.id, z.nazev, k.nazev AS kategorie, z.jednotka,
               z.mnozstvi_na_sklade, z.min_mnozstvi,
               (z.min_mnozstvi - z.mnozstvi_na_sklade) AS chybi
        FROM zbozi z
        JOIN kategorie k ON k.id = z.kategorie_id
        WHERE z.mnozstvi_na_sklade <= z.min_mnozstvi
        ORDER BY chybi DESC;
    """)

    cur.execute("""
        CREATE OR REPLACE VIEW pohyby_detail AS
        SELECT p.id, p.datum, p.typ, z.nazev AS zbozi, z.jednotka,
               p.mnozstvi, d.nazev AS dodavatel, o.nazev AS odberatel, p.poznamka
        FROM pohyb p
        JOIN zbozi    z ON z.id = p.zbozi_id
        LEFT JOIN dodavatel d ON d.id = p.dodavatel_id
        LEFT JOIN odberatel o ON o.id = p.odberatel_id
        ORDER BY p.datum DESC;
    """)

    print("Vkládám testovací data...")

    cur.execute("""
        INSERT INTO kategorie (nazev, popis) VALUES
            ('Kancelář',   'Kancelářské potřeby a vybavení'),
            ('Chemie',     'Čisticí a hygienické prostředky'),
            ('Elektronika','Počítače, tiskárny, příslušenství')
        ON CONFLICT (nazev) DO NOTHING;
    """)

    cur.execute("""
        INSERT INTO dodavatel (nazev, kontakt, email, telefon) VALUES
            ('PaperCo s.r.o.',  'Jan Novák',   'jan@paperco.cz',     '+420 777 111 222'),
            ('ChemSupply a.s.', 'Eva Malá',    'eva@chemsupply.cz',  '+420 602 333 444'),
            ('TechDist s.r.o.', 'Ondřej Král', 'ondrej@techdist.cz', '+420 605 999 000')
        ON CONFLICT DO NOTHING;
    """)

    cur.execute("""
        INSERT INTO odberatel (nazev, kontakt, email, telefon) VALUES
            ('Novák & syn',      'Petr Novák', 'petr@novak.cz',      '+420 603 555 666'),
            ('ABC Office s.r.o.','Lenka Bílá', 'lenka@abcoffice.cz', '+420 776 888 111')
        ON CONFLICT DO NOTHING;
    """)

    cur.execute("""
        INSERT INTO zbozi (kategorie_id, nazev, jednotka, mnozstvi_na_sklade, min_mnozstvi, cena_za_jednotku) VALUES
            (1, 'Kancelářský papír A4', 'ks', 500, 100, 0.85),
            (1, 'Toner HP LaserJet',    'ks',   2,   5, 890.00),
            (2, 'Čisticí prostředek',   'l',   24,  10,  45.00),
            (2, 'Čisticí ubrousky',     'ks',   4,  20,   8.50),
            (3, 'USB hub 4-port',       'ks',  10,   3, 299.00)
        ON CONFLICT DO NOTHING;
    """)

    cur.close()
    conn.close()
    print("✓ Hotovo! Databáze je připravena. Spusť aplikaci přes: python main.py")

if __name__ == "__main__":
    run()
