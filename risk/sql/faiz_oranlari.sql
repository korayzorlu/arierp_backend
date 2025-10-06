SELECT LeasingOperationProjectId,
    InterestRate,
    ValidFromDate
FROM TradeOverdueInterestRate
WHERE 
    OverdueType=1