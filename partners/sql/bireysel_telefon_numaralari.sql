SELECT 
    cw.CustomerId,
    cw.CustomerName,
    com.CommunicationValue
FROM dbo.CrmCustomerWithTypesLight cw
LEFT JOIN dbo.CrmContact cc 
    ON cw.CONTACTID = cc.ContactId
LEFT JOIN dbo.CrmAddress ad 
    ON ad.ObjectId = cc.ContactId
LEFT JOIN dbo.CrmAddressCommunicationInformation com 
    ON com.AddressId = ad.AddressId
LEFT JOIN dbo.LeasingOperationProject lop 
    ON cw.CustomerId = lop.CustomerId
WHERE ad.AddressTypeId = 4
AND com.CommunicationType IN (5,6)
AND lop.RiskIncludingTypeId NOT IN (3,8,9,4)
GROUP BY 
    cw.CustomerId,
    cw.CustomerName,
    com.CommunicationValue