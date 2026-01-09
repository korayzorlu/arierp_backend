SELECT *
FROM TradeTransaction
WHERE
    TrnOprContractId = '62443'
    AND TrnDueDate <= CAST(GETDATE() AS DATE) 
ORDER BY
    TrnDueDate,
    TrnId