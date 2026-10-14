SELECT
    DB_NAME() AS DatabaseName,
    s.name AS SchemaName,
 
    CASE
        WHEN o.type = 'U' THEN 'TABLE'
        WHEN o.type = 'V' THEN 'VIEW'
        ELSE o.type_desc
    END AS ObjectType,
 
    o.name AS ObjectName,
 
    c.column_id AS ColumnOrder,
    c.name AS ColumnName,
 
    t.name AS DataType,
 
    CASE
        WHEN t.name IN ('nvarchar', 'nchar')
             AND c.max_length > 0
            THEN c.max_length / 2
        ELSE c.max_length
    END AS MaxLength,
 
    c.precision AS NumericPrecision,
    c.scale AS NumericScale,
 
    c.is_nullable AS IsNullable,
    c.is_identity AS IsIdentity,
 
    CASE
        WHEN EXISTS (
            SELECT 1
            FROM sys.indexes i
            INNER JOIN sys.index_columns ic
                ON i.object_id = ic.object_id
                AND i.index_id = ic.index_id
            WHERE
                i.object_id = o.object_id
                AND ic.column_id = c.column_id
                AND i.is_primary_key = 1
        )
        THEN 1
        ELSE 0
    END AS IsPrimaryKey,
 
    CAST(te.value AS nvarchar(max)) AS TableDescription,
    CAST(ce.value AS nvarchar(max)) AS ColumnDescription
 
FROM sys.objects o
 
INNER JOIN sys.schemas s
    ON o.schema_id = s.schema_id
 
INNER JOIN sys.columns c
    ON o.object_id = c.object_id
 
INNER JOIN sys.types t
    ON c.user_type_id = t.user_type_id
 
LEFT JOIN sys.extended_properties te
    ON te.major_id = o.object_id
    AND te.minor_id = 0
    AND te.name = 'MS_Description'
 
LEFT JOIN sys.extended_properties ce
    ON ce.major_id = o.object_id
    AND ce.minor_id = c.column_id
    AND ce.name = 'MS_Description'
 
WHERE
    o.is_ms_shipped = 0
    AND o.type IN ('U', 'V')
 
ORDER BY
    s.name,
    o.name,
    c.column_id;