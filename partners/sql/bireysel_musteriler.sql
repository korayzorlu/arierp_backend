SELECT TOP 100 PERCENT
    dbo.CrmContact.FullName,
    dbo.CrmContact.Name AS FirstName,
    dbo.CrmContact.SECOND_NAME AS SecondName,
    dbo.CrmContact.Surname AS Surname,
    dbo.CrmContact.FullName AS ContactCompanyName,
    dbo.CrmIndividualCustomer.IndividualCustomerCode AS CustomerCode,
    dbo.CrmIndividualCustomer.IndividualCustomerId,
    SalariedTitle,
    CASE ISNULL(dbo.CrmTaxDepartment.TaxDepartmentName,'')
         WHEN '' THEN td.TaxDepartmentName
         ELSE dbo.CrmTaxDepartment.TaxDepartmentName
    END TaxDepartmentName,
    CASE ISNULL(dbo.CrmIndividualCustomer.CommercialTaxNo,'')
         WHEN '' THEN CrmContact.TaxNo
         ELSE dbo.CrmIndividualCustomer.CommercialTaxNo
    END CommercialTaxNo,
    dbo.CrmIndividualCustomer.MainSectorId,
    dbo.CrmIndividualCustomer.IndividualCustomerCode,
    ca.Phone,
    ca.Address,
    ca.CityName,
    dbo.CrmContact.TCIdentityNo,
    dbo.CrmContact.TCIdentityNo AS TaxAndTCIdentity,
    dbo.CrmContact.FathersName,
    dbo.CrmContact.BirthPlace,
    dbo.CrmContact.BirthDate,
    dbo.CrmContact.SgkJobCode,
    dbo.CrmContact.PepList,
    dbo.CrmContact.PepListDegree,
    dbo.CrmContact.PepListDescription,
    ca.CountryCode,
    ca.Email,
    PassportNo,
    CASE IS_TURKKEP_CUSTOMER
         WHEN '1' THEN 'Evet'
         ELSE 'Hayır'
    END AS IS_TURKKEP_CUSTOMER
FROM dbo.CrmIndividualCustomer
INNER JOIN CrmContact
    ON dbo.CrmIndividualCustomer.ContactId = dbo.CrmContact.ContactId
LEFT OUTER JOIN dbo.CrmTaxDepartment
    ON dbo.CrmContact.TaxDepartmentId = dbo.CrmTaxDepartment.TaxDepartmentId
LEFT OUTER JOIN dbo.CrmAddressDefaultContactList ca
    ON dbo.CrmContact.ContactId = ca.ObjectId
LEFT OUTER JOIN dbo.CrmTaxDepartment td
    ON dbo.CrmIndividualCustomer.CommercialTaxDepartment = td.TaxDepartmentId
-- WHERE
--     dbo.CrmContact.PepList = '1'
-- ORDER BY
--     dbo.CrmContact.FullName ASC