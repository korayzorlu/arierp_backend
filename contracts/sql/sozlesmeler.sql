SELECT c.ContractHeaderId,
    c.ContractHeaderCode,
    c.CustomerId,
    c.QuotationHeaderId,
    q.vendorId AS VendorId,
    c.CommitteeName,
    c.CreditTypeName,
    c.CustomerRepresentative,
    c.Vendor,
    c.Project,
    c.SubStatuteName,
    c.LopOpenDate,
    c.CurrencyCode
FROM ContractHeaderLightList c
LEFT JOIN QuotationLine q ON c.QuotationHeaderId = q.QuotationHeaderId
WHERE  
    q.Deleted = 0 
AND q.ItemType = 0