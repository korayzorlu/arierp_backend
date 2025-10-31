SELECT TOP 1000 
    *
FROM 
    LedgerAccount
WHERE
    AccountCode LIKE '226.00.1.00.025160.49085%'
ORDER BY
    AccountCode