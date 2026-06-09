SELECT IndividualCustomerId CUSTOMER_ID,
       CustomerCode CUSTOMER_CODE,
       FirstName FIRST_NAME,
       Surname LAST_NAME,
       Fullname FULL_NAME,
       2 CUSTOMER_TYPE,
       Address ADDRESS,
       CityName CITY_NAME,
       DistrictName DISTRICT_NAME,
       Countryname COUNTRY_NAME,
       CountryCode COUNTRY_CODE,
       Citizen CITIZEN,
       Email EMAIL,
       TaxAndTCIdentity IDENTITY_NO,
       FathersName FATHERS_NAME,
       MothersName MOTHERS_NAME,
       BirthDate BIRTH_DATE,
       BirthPlace BIRTH_PLACE,
       TaxDepartmentName TAX_DEPARTMENT_NAME,
       NULL RISK_GRUP_KODU,
       NULL RISK_GRUP_NEDENI,
       NULL SEKTOR_KODU,
       NULL SEKTOR_ADI,
       PHONE TELEFON,
       (SELECT TOP 1 CommunicationValue
          FROM CrmAddressCommunicationInformation a
         WHERE a.AddressId = cust.AddressId
           AND CommunicationType = '5') MOBIL,
       FAX
  FROM (
    SELECT TOP 100 PERCENT
           dbo.CrmContact.FullName,
           dbo.CrmContact.Name AS FirstName,
           dbo.CrmContact.SECOND_NAME AS SecondName,
           dbo.CrmContact.Surname AS Surname,
           dbo.CrmContact.FullName AS ContactCompanyName,
           dbo.CrmContact.MothersName AS MothersName,
           dbo.CrmContact.MAIDEN_NAME AS MaidenName,
           dbo.CrmContact.BirthPlace,
           '' AS TaskGroupName,
           dbo.CrmIndividualCustomer.IndividualCustomerCode AS CustomerCode,
           dbo.CrmIndividualCustomer.IndividualCustomerId,
           dbo.CrmIndividualCustomer.ContactId,
           CASE ISNULL(dbo.CrmTaxDepartment.TaxDepartmentName, '')
             WHEN '' THEN td.TaxDepartmentName
             ELSE dbo.CrmTaxDepartment.TaxDepartmentName
           END TaxDepartmentName,
           CASE ISNULL(dbo.CrmIndividualCustomer.CommercialTaxNo, '')
             WHEN '' THEN CrmContact.TaxNo
             ELSE dbo.CrmIndividualCustomer.CommercialTaxNo
           END CommercialTaxNo,
           dbo.CrmIndividualCustomer.CommercialRegisterNo,
           dbo.CrmIndividualCustomer.MainSectorId,
           dbo.TradeSector.SectorName,
           dbo.CrmCommercialRegistrationDepartment.CommercialRegistrationDepName,
           dbo.CrmIndividualCustomer.RetiredFromAssociation,
           ISNULL(dbo.CrmContact.RecordStatus, 0) AS IsPassive,
           dbo.CrmIndividualCustomer.PART_ID,
           dbo.CrmIndividualCustomer.TRIGGER_CALCULATED,
           dbo.CrmIndividualCustomer.TRIGGER_FIXED,
           dbo.CrmIndividualCustomer.TRIGGER_OPERATION,
           dbo.CrmIndividualCustomer.RISK_KEY_CUSTOMER,
           dbo.CRM_RATING_DEF.RATING,
           dbo.CrmIndividualCustomer.IndividualCustomerCode,
           dbo.CrmIndividualCustomer.MBB_GROUP_CODE,
           dbo.CrmIndividualCustomer.RATING_REVISION_DATE,
           dbo.CrmIndividualCustomer.BANK_BRANCH_CODE,
           dbo.CrmIndividualCustomer.MBB_BRANCH_TYPE_ID,
           dbo.CrmIndividualCustomer.CR_MANAGER_NAME,
           dbo.CrmIndividualCustomer.CR_SEGMENT_CODE,
           ca.Phone,
           ca.Fax,
           ca.Address,
           ca.DistrictName,
           ca.CityName,
           ca.RegionName,
           dbo.CrmContact.TCIdentityNo,
           ca.QuarterName,
           dbo.CrmContact.TCIdentityNo AS TaxAndTCIdentity,
           ca.CountryId AS COUNTRYID,
           ca.CountryName AS COUNTRYNAME,
           dbo.CrmContact.FathersName,
           dbo.CrmContact.Citizen,
           ca.PostalCode,
           ca.CityId,
           dbo.CrmContact.BirthDate,
           dbo.CRM_CRPRTN_RSDNT_TYPE_DEF.CRPRTN_RSDNT_TYPE_NAME,
           dbo.CRM_CRPRTN_RSDNT_TYPE_DEF.CRPRTN_RSDNT_TYPE_ID,
           ca.CountryCode,
           ca.Email,
           dbo.CrmIndividualCustomer.REFERENCE_TYPE,
           dbo.CrmIndividualCustomer.REFERENCE,
           dbo.CrmIndividualCustomer.REFERENCE_CONTACT_ID,
           dbo.CrmIndividualCustomer.CDD_RENEWAL_DATE,
           dbo.CrmIndividualCustomer.CDD_RISK_LEVEL_ID,
           dbo.CrmIndividualCustomer.CDD_TICKBOX,
           dbo.CrmIndividualCustomer.COMPANY_GROUP_ID,
           dbo.CrmIndividualCustomer.BANK_CODE,
           cg.CompanyGroupName,
           cg.CompanyGroupCode,
           IndividualCustomerStatute AS CustomerStatute,
           IS_EINVOICE_CUSTOMER,
           EINVOICE_TYPE_ID,
           WebAddress,
           Street,
           BuildingNumber,
           dbo.CRM_FOLLOW_STATUS_DEF.FOLLOW_STATUS_ID,
           CRM_FOLLOW_STATUS_DEF.FOLLOW_STATUS_NAME AS FOLLOW_STATUS,
           NON_CASH_LIMIT,
           CASH_LIMIT,
           NON_CASH_RISK,
           CASH_RISK,
           dbo.CrmContact.DataStatusId,
           CreditRiskProvisionTypeId,
           ca.AddressId
      FROM dbo.CrmIndividualCustomer
      INNER JOIN CrmContact
        ON dbo.CrmIndividualCustomer.ContactId = dbo.CrmContact.ContactId
      LEFT OUTER JOIN dbo.CrmTaxDepartment
        ON dbo.CrmContact.TaxDepartmentId = dbo.CrmTaxDepartment.TaxDepartmentId
      LEFT OUTER JOIN dbo.CrmAddressDefaultContactList ca
        ON dbo.CrmContact.ContactId = ca.ObjectId
      LEFT OUTER JOIN dbo.CRM_CRPRTN_RSDNT_TYPE_DEF
        ON dbo.CrmContact.RESIDENT_TYPE_ID = dbo.CRM_CRPRTN_RSDNT_TYPE_DEF.CRPRTN_RSDNT_TYPE_ID
       AND CRPRTN_RSDNT_TYPE_NO = 2
      LEFT OUTER JOIN dbo.CRM_RATING_DEF
        ON dbo.CrmIndividualCustomer.RATING_ID = dbo.CRM_RATING_DEF.RATING_ID
      LEFT OUTER JOIN dbo.CRM_FOLLOW_STATUS_DEF
        ON dbo.CrmIndividualCustomer.FOLLOW_STATUS_ID = dbo.CRM_FOLLOW_STATUS_DEF.FOLLOW_STATUS_ID
      LEFT OUTER JOIN dbo.CrmCommercialRegistrationDepartment
        ON dbo.CrmIndividualCustomer.CommercialRegistrationDepId = dbo.CrmCommercialRegistrationDepartment.CommercialRegistrationDepId
      LEFT OUTER JOIN dbo.TradeSector
        ON dbo.CrmIndividualCustomer.MainSectorId = dbo.TradeSector.SectorId
      LEFT OUTER JOIN dbo.CrmTaxDepartment td
        ON dbo.CrmIndividualCustomer.CommercialTaxDepartment = td.TaxDepartmentId
      LEFT JOIN dbo.CrmCompanyGroup cg
        ON dbo.CrmIndividualCustomer.COMPANY_GROUP_ID = cg.CompanyGroupId
  ) AS cust
-- LEFT OUTER JOIN dbo.CrmContactList ON dbo.CrmContactList.ContactId = cust.ContactId

UNION

SELECT CustomerId,
       CustomerCode,
       '' AS FirstName,
       '' AS Surname,
       CustomerName,
       1 AS CustomerTypeId,
       a.Address,
       a.CityName,
       a.DistrictName,
       a.CountryName AS COUNTRYNAME,
       a.CountryCode AS COUNTRY_CODE,
       NULL citizen,
       a.Email,
       TaxNo,
       NULL,
       NULL,
       NULL BirthDate,
       NULL,
       TaxDepartmentName,
       MBB_GROUP_CODE RISK_GRUP_KODU,
       MBB_BRANCH_NAME RISK_GRUP_NEDENI,
       (SELECT MappingCode FROM dbo.TradeSector s WHERE s.SectorId = a.SectorId) SEKTOR_KODU,
       SectorName SEKTOR_ADI,
       a.PHONE,
       (SELECT TOP 1 CommunicationValue
          FROM CrmAddressCommunicationInformation B
         WHERE B.AddressId = L.AddressId
           AND B.CommunicationType = '5') MOBIL,
       a.FAX
  FROM dbo.CrmInstitutionalCustomerLightList a
  LEFT JOIN CrmAddressDefaultCompanyList L
    ON a.CustomerId = L.ObjectId
