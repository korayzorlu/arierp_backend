SELECT definition AS LedgerTransaction
FROM sys.sql_modules
WHERE object_id = OBJECT_ID('LedgerTransaction');