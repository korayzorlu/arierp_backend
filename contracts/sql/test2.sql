SELECT *
FROM TradeTransaction
WHERE
    TrnOprContractId = '61579'
    AND TrnDueDate <= CAST(GETDATE() AS DATE)
    -- AND TrnFromToType = 10
ORDER BY
    TrnDueDate,
    TrnId