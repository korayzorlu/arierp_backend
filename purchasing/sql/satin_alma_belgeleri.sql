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
WHERE VendorId NOT IN ('1461', '3374', '3781', '5451', '5785', '7987', '10356', '10506', '10681', '10682', '23670', '28814', '29447')
    --AND OperationProjectId = '97594'
--AND DocumentHeaderId = '20341'
ORDER BY VendorName