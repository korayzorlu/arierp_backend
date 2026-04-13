SELECT
    dbo.LeasePurchaseDocumentLine.DocumentLineId,
    dbo.LeasePurchaseDocumentLine.DocumentHeaderId,
    dbo.LPCollectingType.CollectingType        AS CollectingTypeId,
    dbo.LPCollectingType.CollectingTypeId      AS CTypeId,
    cus.InstitutionalCustomerName              AS DealerWillBeInvoicedId,
    dbo.InventoryStockCode.StockName,
    dbo.LeasePurchaseDocumentLine.PurchaseTypeId,
    dbo.LPPurchaseType.PurchaseType,
    dbo.LeasePurchaseDocumentLine.Explanation  AS OffsetInfo,
    dbo.LeasePurchaseDocumentLine.Quantity,
    dbo.GeneralCurrency.CurrencyCode,
    dbo.LeasePurchaseDocumentLine.ExchangeRate,
    dbo.LeasePurchaseDocumentLine.UnitPrice,
    dbo.LeasePurchaseDocumentLine.TotalPrice,
    dbo.LeasePurchaseDocumentLine.VatTotal,
    dbo.LeasePurchaseDocumentLine.GeneralTotal,
    dbo.LeasePurchaseDocumentLine.ExpenseTypeId

FROM dbo.LeasePurchaseDocumentLine

LEFT OUTER JOIN dbo.InventoryStockCode
    ON dbo.LeasePurchaseDocumentLine.StockCodeId = dbo.InventoryStockCode.StockCodeId

LEFT OUTER JOIN dbo.LPCollectingType
    ON dbo.LeasePurchaseDocumentLine.CollectingTypeId = dbo.LPCollectingType.CollectingTypeId

LEFT OUTER JOIN dbo.LPPurchaseType
    ON dbo.LeasePurchaseDocumentLine.PurchaseTypeId = dbo.LPPurchaseType.PurchaseTypeId

LEFT OUTER JOIN dbo.GeneralCurrency
    ON dbo.LeasePurchaseDocumentLine.CurrencyId = dbo.GeneralCurrency.CurrencyId

LEFT OUTER JOIN (
    SELECT DISTINCT
        c.CustomerId   AS InstitutionalCustomerId,
        c.CustomerName AS InstitutionalCustomerName,
        c.IsPassive
    FROM dbo.CrmRelationship1
    RIGHT OUTER JOIN dbo.CrmCustomerListCombo c
        ON dbo.CrmRelationship1.SourceId = c.CustomerId
    WHERE
        (
            dbo.CrmRelationship1.RelationshipId = 2
            OR dbo.CrmRelationship1.RelationshipId = 4
        )
        AND ISNULL(dbo.CrmRelationship1.TargetId, 0) = 0
) cus
    ON cus.InstitutionalCustomerId = LeasePurchaseDocumentLine.DealerWillBeInvoicedId

WHERE
    dbo.LeasePurchaseDocumentLine.IsDeleted IS NULL
    OR dbo.LeasePurchaseDocumentLine.IsDeleted = 0;
