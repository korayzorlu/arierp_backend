SELECT TOP 1000 lop.OperationProjectId,
    lop.OperationProjectCode,
    lop.ContractHeaderCode,
    lop.TypeName,
    lop.VatRate,
    lop.ActivationDate,
    lop.RiskIncludingTypeName,
    l.RiskIncludingLastUpdateDate AS RiskIncludingLastUpdateDate,
    lop.CurrencyCode,
    lop.CustomerBaseCost,
    lop.CustomerBaseCost * 1.1 AS CustomerBaseCostWithIncrease,
    lop.PaymentCount,
    lop.AnnualRate,
    lop.OperationBaseIRR,
    lop.SubStatuteName,
    lop.LeasingTypeName,
    lop.ApplicationID,
    lop.IS_LAST_PROJECT,
    lop.CurrentRequest,
    l.MainLopId
FROM LeasingOperationProjectList lop
LEFT JOIN LeasingOperationProject l ON lop.OperationProjectId = l.OperationProjectId
-- WHERE lop.OperationProjectCode = '66665.1.0'
-- WHERE
--     lop.ActivationDate > '2023-07-10'
--     AND lop.VatRate = '18.00'
--     AND lop.IS_LAST_PROJECT = 1