CREATE USER docker;
CREATE USER replicator WITH REPLICATION ENCRYPTED PASSWORD 'Qq12345';

SELECT pg_create_physical_replication_slot('replication_slot');
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = 'pt_db') THEN
        CREATE DATABASE pt_db;
    END IF;
END $$;
GRANT ALL PRIVILEGES ON DATABASE pt_db TO docker;
CREATE TABLE IF NOT EXISTS emails (
    id serial PRIMARY KEY,
    email VARCHAR(255) 
);
CREATE TABLE IF NOT EXISTS phones (
    id serial PRIMARY KEY,
    phone VARCHAR(255)
);