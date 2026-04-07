SELECT TOP 100 *,
    lw.BBSN_NO
FROM LeasingOperationProject lop
LEFT OUTER JOIN dbo.ContractHeader ch (NOLOCK) ON lop.ContractHeaderId = ch.ContractHeaderId
LEFT JOIN LeasingOperationProjectList lw ON lop.OperationProjectId = lw.OperationProjectId
WHERE lw.BBSN_NO LIKE ('103925')