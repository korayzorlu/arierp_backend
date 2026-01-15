SELECT TOP 10000
    dbo.QuotationHeader.QuotationHeaderId,
    m.DefinitionName AS Status,
    dbo.CrmCustomerListCombo.CustomerName,
    r.CustomerName AS ReferenceName,
    rt.TypeName AS ReferenceTypeName,
    dbo.QuotationAmount.CustomerBaseCost AS LeasingBaseCost,
    dbo.GeneralCurrency.CurrencyCode,
    dbo.FoundationUsers.Name + ' ' + dbo.FoundationUsers.Surname AS CustomerRepresentative,
    dbo.QuotationHeader.CreditHeaderId,
    dbo.QuotationHeader.ContractHeaderId,
    ContractHeader.ContractHeaderCode,
    dbo.QuotationHeader.CustomerId,
    dbo.QuotationHeader.RequestDate,
    dbo.FoundationPart.PartName,
    location.UnitId AS LocationId,
    location.UnitName AS LocationName,
    CrmCustomerListCombo.PART_ID,
    dbo.LeasingOperationProject.OperationProjectCode,
    LOPRevisionDate,
    ISNULL(QuotationHeader.IsLOPRevision, 0) AS IsLOPRevision,
    dbo.QuotationHeader.LastParentStatuId AS ParentStatuteId,
    dbo.QuotationHeader.LastSubStatuId AS SubStatuteId,
    m.DefinitionName AS SubStatuteDefinition,
    p.Name AS ParentStatuteDefinition,
    QuotationHeader.Reference,
    QuotationHeader.ApplicationID,
    qlt.LeasingTypeName,
    cr.CustomerName AS REFCOMPNAME,
    (
        SELECT TOP 1 tac.AccName
        FROM dbo.TradeAccountAndTypeComboCrmList tac
        WHERE tac.AccCrmId = (
            SELECT TOP 1 qld.VendorId
            FROM dbo.QuotationLineDetail qld
            WHERE qld.QuotationHeaderId = dbo.QuotationHeader.QuotationHeaderId
                AND ISNULL(qld.Deleted, 0) = 0
                AND qld.ItemTreeId <> 14
        )
        AND tac.AccTypType = 21
    ) AS Vendor,
    (
        SELECT TOP 1 stk.StockName
        FROM dbo.InventoryStockCode stk
        WHERE stk.StockCodeId = (
            SELECT TOP 1 qld.StockCodeId
            FROM dbo.QuotationLineDetail qld
            WHERE qld.QuotationHeaderId = dbo.QuotationHeader.QuotationHeaderId
                AND ISNULL(qld.Deleted, 0) = 0
                AND qld.ItemTreeId <> 14
        )
    ) AS Project
FROM dbo.QuotationHeader
INNER JOIN dbo.QuotationAmount
    ON dbo.QuotationHeader.QuotationHeaderId = dbo.QuotationAmount.ObjectId
LEFT OUTER JOIN dbo.ContractHeader
    ON dbo.QuotationHeader.ContractHeaderId = dbo.ContractHeader.ContractHeaderId
LEFT OUTER JOIN dbo.QuotationLeasingType qlt
    ON dbo.QuotationHeader.LeasingType = qlt.LeasingTypeId
LEFT OUTER JOIN dbo.CrmCustomerListCombo
    ON dbo.QuotationHeader.CustomerId = dbo.CrmCustomerListCombo.CustomerId
LEFT OUTER JOIN dbo.FoundationUsers
    ON dbo.QuotationHeader.CustomerRepresentative = dbo.FoundationUsers.UserId
LEFT OUTER JOIN dbo.GeneralCurrency
    ON dbo.QuotationHeader.CurrencyId = dbo.GeneralCurrency.CurrencyId
LEFT OUTER JOIN dbo.FoundationPart
    ON CrmCustomerListCombo.PART_ID = dbo.FoundationPart.PartId
LEFT OUTER JOIN dbo.FoundationUnit location
    ON dbo.QuotationHeader.LocationId = location.UnitId
LEFT OUTER JOIN dbo.LeasingOperationProject
    ON dbo.QuotationHeader.LOPId = dbo.LeasingOperationProject.OperationProjectId
LEFT OUTER JOIN dbo.QuotationReferenceType AS rt
    ON QuotationHeader.ReferenceType = rt.TypeId
LEFT OUTER JOIN dbo.CrmCustomerListComboLight AS r
    ON QuotationHeader.Reference = r.CustomerId
LEFT OUTER JOIN FoundationStatuteMenu AS m
    ON dbo.QuotationHeader.LastSubStatuId = m.DefinitionId
    AND m.TableName = 'QuotationHeader'
LEFT OUTER JOIN FoundationStatuteMenuParent AS p
    ON dbo.QuotationHeader.LastParentStatuId = p.Id
LEFT OUTER JOIN dbo.CrmCustomerWithTypes AS cr
    ON dbo.QuotationHeader.Reference = cr.CustomerId
WHERE
    (dbo.QuotationHeader.Deleted IS NULL OR dbo.QuotationHeader.Deleted = '0')
    AND (dbo.QuotationAmount.ObjectTypeId = 1)
    AND (dbo.QuotationHeader.IsTemplate = 0 OR dbo.QuotationHeader.IsTemplate = 2)
    AND CreditTypeId <> 2
    AND ISNULL(ContractHeader.IS_DELETED, 0) = 0