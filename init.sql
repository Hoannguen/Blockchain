CREATE TABLE Transactions (
    index SERIAL PRIMARY KEY,
    proof integer NOT NULL,
    previous_hash text NOT NULL,
    timestamp timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);