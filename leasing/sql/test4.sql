SELECT TOP 10 *,
    tt.TrnOprLeasingOperationPrjId
FROM
    TradeTransactionAllInvoices tta (NOLOCK)
    LEFT JOIN TradeTransaction tt (NOLOCK) ON tta.TrnId = tt.TrnId
WHERE
    tt.TrnOprLeasingOperationPrjId = '98457'

    