SELECT TOP 1000 
    *
FROM 
    LedgerAccount
WHERE
    AccountCode LIKE '226.00.1.00.019034.31197%'
ORDER BY
    AccountCode