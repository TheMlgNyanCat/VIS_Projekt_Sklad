# SkladIS — Skladový informační systém

Desktop aplikace pro správu skladu. Python + PyQt6 + PostgreSQL.

## Požadavky
- Python 3.11+
- PostgreSQL 16+

## Instalace

### 1. Klonování repozitáře
git clone https://github.com/TheMlgNyanCat/VIS_Projekt_Sklad.git
cd VIS_Projekt_Sklad

### 2. Instalace závislostí
pip install -r requirements.txt

### 3. Databáze
Vytvoř databázi v PostgreSQL:
psql -U postgres -c "CREATE DATABASE sklad;"

Nastav .env soubor (viz krok 4) a pak spusť:
python setup.py

### 4. Konfigurace
Zkopíruj `.env.example` jako `.env` a vyplň údaje:
DB_HOST=localhost
DB_PORT=5432
DB_NAME=sklad
DB_USER=postgres
DB_PASSWORD=tvoje_heslo

### 5. Spuštění
python main.py