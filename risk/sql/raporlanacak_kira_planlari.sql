SELECT lop.*
FROM LeasingOperationProjectPartList lop (NOLOCK)
LEFT JOIN (
    SELECT
        kk.OperationProjectId AS OperationProject_Id,
        COUNT(*) OperationProjectId_Count
    FROM LeasingOperationProject kk (NOLOCK)
    WHERE NOT (
        kk.RiskIncludingTypeId IN (3, 6)
        OR (kk.RiskIncludingTypeId IN (9, 5, 7) AND kk.OperationTypeId = 1)
    )
    GROUP BY kk.OperationProjectId
) xx ON xx.OperationProject_Id = lop.SourceLopId
WHERE (
    (lop.OperationTypeId = 2 AND ISNULL(xx.OperationProjectId_Count, 0) <> 0)
    OR (lop.OperationTypeId = 1 AND ISNULL(xx.OperationProjectId_Count, 0) = 0)
)
AND RiskIncludingTypeId IN (1, 3, 4, 6, 7, 8, 9, 10, 11, 12, 13, 0)
AND FirstActivationDate <= CONVERT(DATETIME, '2026-7-22', 102)
AND IS_LAST_PROJECT = 1