-- ============================================================
--  Skladový informační systém — PostgreSQL schéma
-- ============================================================

-- Rozšíření pro automatické časové razítko
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ------------------------------------------------------------
--  1. KATEGORIE
-- ------------------------------------------------------------
CREATE TABLE kategorie (
    id          SERIAL PRIMARY KEY,
    nazev       VARCHAR(100) NOT NULL UNIQUE,
    popis       TEXT,
    vytvoreno   TIMESTAMP DEFAULT NOW()
);

-- ------------------------------------------------------------
--  2. DODAVATEL
-- ------------------------------------------------------------
CREATE TABLE dodavatel (
    id          SERIAL PRIMARY KEY,
    nazev       VARCHAR(150) NOT NULL,
    kontakt     VARCHAR(100),
    email       VARCHAR(150),
    telefon     VARCHAR(30),
    vytvoreno   TIMESTAMP DEFAULT NOW()
);

-- ------------------------------------------------------------
--  3. ODBERATEL
-- ------------------------------------------------------------
CREATE TABLE odberatel (
    id          SERIAL PRIMARY KEY,
    nazev       VARCHAR(150) NOT NULL,
    kontakt     VARCHAR(100),
    email       VARCHAR(150),
    telefon     VARCHAR(30),
    vytvoreno   TIMESTAMP DEFAULT NOW()
);

-- ------------------------------------------------------------
--  4. ZBOZI
-- ------------------------------------------------------------
CREATE TABLE zbozi (
    id                  SERIAL PRIMARY KEY,
    kategorie_id        INTEGER NOT NULL REFERENCES kategorie(id) ON DELETE RESTRICT,
    nazev               VARCHAR(200) NOT NULL,
    jednotka            VARCHAR(20)  NOT NULL DEFAULT 'ks',   -- ks, kg, l, m, …
    mnozstvi_na_sklade  INTEGER      NOT NULL DEFAULT 0 CHECK (mnozstvi_na_sklade >= 0),
    min_mnozstvi        INTEGER      NOT NULL DEFAULT 0 CHECK (min_mnozstvi >= 0),
    cena_za_jednotku    NUMERIC(10,2) NOT NULL DEFAULT 0 CHECK (cena_za_jednotku >= 0),
    vytvoreno           TIMESTAMP DEFAULT NOW(),
    aktualizovano       TIMESTAMP DEFAULT NOW()
);

-- Index pro rychlé vyhledávání pod minimem
CREATE INDEX idx_zbozi_nizky_stav
    ON zbozi (mnozstvi_na_sklade)
    WHERE mnozstvi_na_sklade <= min_mnozstvi;

-- ------------------------------------------------------------
--  5. POHYB
-- ------------------------------------------------------------
CREATE TYPE typ_pohybu AS ENUM ('prijem', 'vydej');

CREATE TABLE pohyb (
    id              SERIAL PRIMARY KEY,
    zbozi_id        INTEGER      NOT NULL REFERENCES zbozi(id) ON DELETE RESTRICT,
    typ             typ_pohybu   NOT NULL,
    mnozstvi        INTEGER      NOT NULL CHECK (mnozstvi > 0),
    dodavatel_id    INTEGER      REFERENCES dodavatel(id) ON DELETE SET NULL,
    odberatel_id    INTEGER      REFERENCES odberatel(id) ON DELETE SET NULL,
    datum           TIMESTAMP    NOT NULL DEFAULT NOW(),
    poznamka        TEXT,

    -- Příjem musí mít dodavatele, výdej musí mít odběratele
    CONSTRAINT chk_partner CHECK (
        (typ = 'prijem' AND dodavatel_id IS NOT NULL AND odberatel_id IS NULL)
        OR
        (typ = 'vydej'  AND odberatel_id IS NOT NULL AND dodavatel_id IS NULL)
    )
);

CREATE INDEX idx_pohyb_zbozi  ON pohyb (zbozi_id);
CREATE INDEX idx_pohyb_datum  ON pohyb (datum DESC);

-- ------------------------------------------------------------
--  6. TRIGGER — automatická aktualizace množství na skladě
-- ------------------------------------------------------------
CREATE OR REPLACE FUNCTION aktualizuj_mnozstvi()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.typ = 'prijem' THEN
        UPDATE zbozi
        SET mnozstvi_na_sklade = mnozstvi_na_sklade + NEW.mnozstvi,
            aktualizovano      = NOW()
        WHERE id = NEW.zbozi_id;
    ELSIF NEW.typ = 'vydej' THEN
        -- Kontrola dostatečného množství
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

CREATE TRIGGER trg_pohyb_mnozstvi
AFTER INSERT ON pohyb
FOR EACH ROW EXECUTE FUNCTION aktualizuj_mnozstvi();

-- ------------------------------------------------------------
--  7. VIEW — zboží s nízkým stavem
-- ------------------------------------------------------------
CREATE VIEW nizky_stav AS
SELECT
    z.id,
    z.nazev,
    k.nazev          AS kategorie,
    z.jednotka,
    z.mnozstvi_na_sklade,
    z.min_mnozstvi,
    (z.min_mnozstvi - z.mnozstvi_na_sklade) AS chybi
FROM zbozi z
JOIN kategorie k ON k.id = z.kategorie_id
WHERE z.mnozstvi_na_sklade <= z.min_mnozstvi
ORDER BY chybi DESC;

-- ------------------------------------------------------------
--  8. VIEW — pohyby s detaily
-- ------------------------------------------------------------
CREATE VIEW pohyby_detail AS
SELECT
    p.id,
    p.datum,
    p.typ,
    z.nazev          AS zbozi,
    z.jednotka,
    p.mnozstvi,
    d.nazev          AS dodavatel,
    o.nazev          AS odberatel,
    p.poznamka
FROM pohyb p
JOIN zbozi    z ON z.id = p.zbozi_id
LEFT JOIN dodavatel d ON d.id = p.dodavatel_id
LEFT JOIN odberatel o ON o.id = p.odberatel_id
ORDER BY p.datum DESC;

-- ------------------------------------------------------------
--  9. Ukázková testovací data
-- ------------------------------------------------------------
INSERT INTO kategorie (nazev, popis) VALUES
    ('Kancelář',  'Kancelářské potřeby a vybavení'),
    ('Chemie',    'Čisticí a hygienické prostředky'),
    ('Elektronika','Počítače, tiskárny, příslušenství');

INSERT INTO dodavatel (nazev, kontakt, email, telefon) VALUES
    ('PaperCo s.r.o.',  'Jan Novák',  'jan@paperco.cz',     '+420 777 111 222'),
    ('ChemSupply a.s.', 'Eva Malá',   'eva@chemsupply.cz',  '+420 602 333 444'),
    ('TechDist s.r.o.', 'Ondřej Král','ondrej@techdist.cz', '+420 605 999 000');

INSERT INTO odberatel (nazev, kontakt, email, telefon) VALUES
    ('Novák & syn',     'Petr Novák', 'petr@novak.cz',      '+420 603 555 666'),
    ('ABC Office s.r.o.','Lenka Bílá','lenka@abcoffice.cz', '+420 776 888 111');

INSERT INTO zbozi (kategorie_id, nazev, jednotka, mnozstvi_na_sklade, min_mnozstvi, cena_za_jednotku) VALUES
    (1, 'Kancelářský papír A4', 'ks',  500, 100, 0.85),
    (1, 'Toner HP LaserJet',    'ks',    2,   5, 890.00),
    (2, 'Čisticí prostředek',   'l',    24,  10,  45.00),
    (2, 'Čisticí ubrousky',     'ks',    4,  20,   8.50),
    (3, 'USB hub 4-port',        'ks',   10,   3, 299.00);
