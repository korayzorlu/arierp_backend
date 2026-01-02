SELECT TOP 1000
    *
FROM
    LedgerTransaction
WHERE
   AccountCode = '278.99.6.00.028888.58889.01'
ORDER BY
    TransactionDate DESC,
    TransactionId DESC