select pg_drop_replication_slot('replication_slot');
SELECT pg_create_physical_replication_slot('replication_slot');

ALTER ROLE postgres WITH PASSWORD 'Qq12345';

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = 'pt_db') THEN
        CREATE DATABASE pt_db;
    END IF;
END $$;

CREATE TABLE IF NOT EXISTS emails (
    id serial PRIMARY KEY,
    email VARCHAR(255) 
);
CREATE TABLE IF NOT EXISTS phones (
    id serial PRIMARY KEY,
    phone VARCHAR(255)
);

