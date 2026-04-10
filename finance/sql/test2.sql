SELECT 
    DocumentHeaderId,
    DocumentHeaderCode,
    CustomerId,
    VendorId,
    VendorName,
    DocumentNumber,
    DocumentDate,
    CurrencyCode,
    ExchangeRate,
    LineTotal,
    VatTotal,
    GeneralTotal,
    DocumentStatus,
    OperationProjectId
FROM LeasePurchaseDocumentHeaderList
WHERE OperationProjectId = '97594'