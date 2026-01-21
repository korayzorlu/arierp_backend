SELECT TOP 10
OperationProjectId
FROM
    LeasingOperationProject
WHERE NOT (
        RiskIncludingTypeId IN (3, 6)
        OR (RiskIncludingTypeId IN (9, 5, 7) AND OperationTypeId = 1)
    )