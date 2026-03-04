SELECT *,
    dbo.CrmContact.FullName,
    dbo.CrmContact.Name AS FirstName,
    dbo.CrmContact.SECOND_NAME AS SecondName,
    dbo.CrmContact.Surname AS Surname,
    dbo.CrmContact.FullName AS ContactCompanyName
FROM
    CrmIndividualCustomer
INNER JOIN CrmContact
    ON dbo.CrmIndividualCustomer.ContactId = dbo.CrmContact.ContactId
WHERE
    IndividualCustomerId = '33625'
