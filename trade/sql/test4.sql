SELECT TOP 10000 *
FROM
    TradeTransaction
WHERE
    --TrnDescription LIKE '%SANAL POS%'
TrnFromLedgerAccountId = '710880'

