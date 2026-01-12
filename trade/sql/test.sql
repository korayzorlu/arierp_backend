SELECT TOP 1000 *
FROM
    TradeTransaction
WHERE
    TrnOprContractId = '2620'
    AND TrnDescription NOT LIKE '% Evalüasyonu (USD)%'