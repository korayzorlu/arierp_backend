SELECT TransactionId,
    LedgerPeriod,
    TransactionText,
    AccountCode,
    AmountType,
    AmountLocal,
    AmountCurrency,
    TransactionDate,
    UserCodeCreated
FROM
    LedgerTransaction
-- WHERE
--    AccountCode = '981.58.01.67814.01'
-- ORDER BY
--     TransactionDate DESC,
--     TransactionId DESC