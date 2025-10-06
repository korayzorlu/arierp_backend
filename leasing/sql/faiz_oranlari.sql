SELECT LeasingOperationProjectId,
    InterestRate
FROM TradeOverdueInterestRate
WHERE 
    OverdueType=1
    --AND LeasingOperationProjectId IN (35129)
ORDER BY 
    LeasingOperationProjectId