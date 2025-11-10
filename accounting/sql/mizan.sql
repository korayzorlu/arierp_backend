SELECT TOP 99999999
--SELECT TOP 100
    AccountId,
    LedgerAccount.AccountCode AS AccountCode,
    LedgerAccount.AccountCode AS AccountCodeTrim,
    LedgerAccount.AccountName AS AccountName,
    LedgerAccount.Dimension8 AS ContractId,
    AccountType AS BalanceAccountType,
    LedgerAccount.AccountCurrencyCode AS CurrencyCode,
    CRMCode AS CRMCode,
    CASE
        WHEN SUM(ISNULL(AmountLocal, 0)) > 0 THEN SUM(ISNULL(AmountLocal, 0))
        ELSE 0
    END AS BalanceDebit,
    CASE
        WHEN SUM(ISNULL(AmountLocal, 0)) < 0 THEN ABS(SUM(ISNULL(AmountLocal, 0)))
        ELSE 0
    END AS BalanceCredit,
    ISNULL(SUM(AmountLocalD), 0) AS TotalDebit,
    ISNULL(SUM(ABS(AmountLocalC)), 0) AS TotalCredit,
    CASE
        WHEN SUM(ISNULL(AmountCurrency, 0)) > 0 THEN SUM(ISNULL(AmountCurrency, 0))
        ELSE 0
    END AS BalanceDebitAlternate,
    CASE
        WHEN SUM(ISNULL(AmountCurrency, 0)) < 0 THEN ABS(SUM(ISNULL(AmountCurrency, 0)))
        ELSE 0
    END AS BalanceCreditAlternate,
    ISNULL(SUM(AmountCurrencyD), 0) AS TotalDebitAlternate,
    ISNULL(SUM(ABS(AmountCurrencyC)), 0) AS TotalCreditAlternate
FROM
    LedgerAccount (NOLOCK)
    LEFT JOIN (
        SELECT
            AccountCode AS AccountCodeTransaction,
            AmountType,
            SUM(AmountLocal) AS AmountLocal,
            SUM(AmountLocal * AmountType) AS AmountLocalD,
            SUM(AmountLocal * (1 - AmountType)) AS AmountLocalC,
            SUM(AmountCurrency) AS AmountCurrency,
            SUM(AmountCurrency * AmountType) AS AmountCurrencyD,
            SUM(AmountCurrency * (1 - AmountType)) AS AmountCurrencyC,
            Dimension3 AS CRMCode
        FROM
            LedgerTransaction (NOLOCK)
        WHERE
            IsDummy = 0
            AND IsReverse + IsReverted >= 0
            AND IsAccrual >= 0
            AND TransactionDate >= CONVERT(DATETIME, '2025-1-1', 102)
            AND TransactionDate <= CONVERT(DATETIME, CONVERT(VARCHAR(10), GETDATE(), 102), 102)
            AND VoucherType IN (
                1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,
                35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,0
            )
            -- AND AccountCode >= '392'
            -- AND AccountCode <= '393999'
        GROUP BY
            AccountCode,
            AmountType,
            Dimension3
    ) lt ON AccountCodeTransaction = LedgerAccount.AccountCode
WHERE
    ISNULL(MZ110UFAccountCode, '') = ''
    -- AND CRMCode = '23919'
    -- AND LedgerAccount.AccountCode >= '392'
    -- AND LedgerAccount.AccountCode <= '393999'
    -- AND (LedgerAccount.AccountCode LIKE '392.99.2.00%' OR LedgerAccount.AccountCode LIKE '393.99.2.01%')
GROUP BY
    LedgerAccount.AccountId,
    LedgerAccount.AccountCode,
    LedgerAccount.AccountName,
    AccountType,
    LedgerAccount.AccountCurrencyCode,
    CRMCode,
    LedgerAccount.Dimension8
HAVING
    SUM(AmountLocal) <> 0
ORDER BY
    AccountName