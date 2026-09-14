-- UTOPIA_LOG veritabanındaki tüm tablolar
SELECT TABLE_SCHEMA, TABLE_NAME
FROM UTOPIA_LOG.INFORMATION_SCHEMA.TABLES
WHERE TABLE_TYPE = 'BASE TABLE'
ORDER BY TABLE_SCHEMA, TABLE_NAME;

-- Alternatif (sys kataloğu, şema + satır sayısı ile)
SELECT s.name AS schema_name,
       t.name AS table_name,
       p.rows AS row_count
FROM UTOPIA_LOG.sys.tables t
JOIN UTOPIA_LOG.sys.schemas s ON s.schema_id = t.schema_id
JOIN UTOPIA_LOG.sys.partitions p ON p.object_id = t.object_id AND p.index_id IN (0, 1)
ORDER BY s.name, t.name;

-- View'ler de dahil hepsi
SELECT TABLE_SCHEMA, TABLE_NAME, TABLE_TYPE
FROM UTOPIA_LOG.INFORMATION_SCHEMA.TABLES
ORDER BY TABLE_TYPE, TABLE_SCHEMA, TABLE_NAME;

-- Bir tablonun kolonları (ör. FoundationFailedUser)
SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH, IS_NULLABLE
FROM UTOPIA_LOG.INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'FoundationFailedUser'
ORDER BY ORDINAL_POSITION;

SELECT *
FROM UTOPIA_LOG.dbo.FoundationFailedUser
