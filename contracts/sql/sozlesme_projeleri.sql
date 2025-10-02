SELECT 
    v.CustomerId AS VendorId,
    c.ContractHeaderId AS ContractHeaderId
FROM 
    dbo.QuotationLine l

    LEFT JOIN dbo.CrmCustomerWithTypesLight v 
        ON l.VendorId = v.CustomerId

    LEFT JOIN dbo.ContractHeaderLightList c 
        ON l.QuotationHeaderId = c.QuotationHeaderId
WHERE  
    l.Deleted = 0 
    AND l.ItemType = 0