SELECT 
    MAX(TransactionDate) AS MAXTransactionDate,
    MIN(TransactionDate) AS MINTransactionDate
FROM 
    LedgerTransaction (NOLOCK)
    LEFT JOIN LedgerAccount (NOLOCK) 
        ON LedgerTransaction.AccountCode = LedgerAccount.AccountCode
WHERE 
    IsDummy = 0
    AND (IsReverse + IsReverted) >= 0
    AND IsAccrual >= 0
    AND LedgerAccount.AccountCode >= '392'
    AND LedgerAccount.AccountCode <= '393999'
    AND TransactionDate >= CONVERT(DATETIME, '2025-1-1', 102)
    AND VoucherType IN (
        0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18,
        35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55
    )