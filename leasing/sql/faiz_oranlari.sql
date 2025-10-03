SELECT *
FROM TradeOverdueInterestRate
WHERE 
    OverdueType=1 AND LeasingOperationProjectId IN (
        SELECT LeasingOperationProjectId
        FROM TradeOverdueInterestRate
        WHERE OverdueType=1
        GROUP BY LeasingOperationProjectId
        HAVING COUNT(LeasingOperationProjectId) > 1
    )
ORDER BY 
    LeasingOperationProjectId