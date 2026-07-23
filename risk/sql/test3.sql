
SELECT
    dbo.LeasingOperationProject.CustomerId,
    ContractHeaderId,
    ContractProjectId,
    SourceLOPId,
    OperationProjectId,
    OperationProjectCode,
    TransferCode,
    OperationTypeId,
    RiskIncludingTypeId,
    dbo.LeasingOperationProject.IS_LAST_PROJECT,
    (
        SELECT lop.ActivationDate
        FROM dbo.LeasingOperationProject AS lop
        WHERE (lop.OperationProjectId = dbo.LeasingOperationProject.SourceLOPId)
    ) AS FirstActivationDate,
    dbo.CrmCustomerWithTypesLight.PART_ID,
    dbo.LeasingOperationProject.LastSubStatuId,
    dbo.LeasingOperationProject.LastSubStatuId AS SubStatuteId,
    substatu.DefinitionName,
    CrmCustomerWithTypesLight.Companygroupid,
    LeasingOperationProject.VendorTypeId
FROM dbo.LeasingOperationProject
LEFT JOIN dbo.CrmCustomerWithTypesLight ON dbo.LeasingOperationProject.CustomerId = dbo.CrmCustomerWithTypesLight.CustomerId
LEFT JOIN FoundationStatuteMenu substatu ON substatu.DefinitionId = dbo.LeasingOperationProject.LastSubStatuId
