SELECT
    dbo.CrmInstitutionalCustomer.InstitutionalCustomerId,
    dbo.CrmInstitutionalCustomer.InstitutionalCustomerCode,
    dbo.CrmInstitutionalCustomer.InstitutionalCustomerName,
    dbo.CrmInstitutionalCustomer.EMail,
    dbo.CrmInstitutionalCustomer.Phone,
    dbo.CrmAddressDefaultCompanyList.Address,
    dbo.CrmCountry.CountryName,
    dbo.CrmAddressDefaultCompanyList.CityName,
    dbo.CrmTaxDepartment.TaxDepartmentName,
    dbo.CrmInstitutionalCustomer.TaxNo,
    CASE dbo.CrmInstitutionalCustomer.IS_TURKKEP_CUSTOMER
         WHEN '1' THEN 'Evet'
         ELSE 'Hayır'
    END AS IS_TURKKEP_CUSTOMER,
    dbo.CrmInstitutionalCustomer.KEP_ADDRESS,
    dbo.CrmInstitutionalCustomer.KEP_FINISH_DATE

FROM dbo.CrmInstitutionalCustomer

    LEFT JOIN dbo.CrmCompanyGroup
        ON  dbo.CrmInstitutionalCustomer.CompanyGroupId = dbo.CrmCompanyGroup.CompanyGroupId

    LEFT OUTER JOIN dbo.CrmCommercialRegistrationDepartment
        ON  dbo.CrmInstitutionalCustomer.CommercialRegistrationDepId = dbo.CrmCommercialRegistrationDepartment.CommercialRegistrationDepId

    LEFT OUTER JOIN dbo.CrmTaxDepartment
        ON  dbo.CrmInstitutionalCustomer.TaxDepartmentId = dbo.CrmTaxDepartment.TaxDepartmentId

    LEFT OUTER JOIN dbo.CrmInstitutionalCustomer AS CrmInstitutionalCustomer_1
        ON  dbo.CrmInstitutionalCustomer.ParentCompanyId = CrmInstitutionalCustomer_1.InstitutionalCustomerId
        AND ISNULL(CrmInstitutionalCustomer_1.Deleted, '0') = 0

    LEFT OUTER JOIN dbo.CrmAddressDefaultCompanyList
        ON  dbo.CrmInstitutionalCustomer.InstitutionalCustomerId = dbo.CrmAddressDefaultCompanyList.ObjectId

    LEFT OUTER JOIN dbo.CrmCountry
        ON  dbo.CrmAddressDefaultCompanyList.CountryId = dbo.CrmCountry.CountryId

    LEFT OUTER JOIN dbo.TradeSector
        ON  dbo.CrmInstitutionalCustomer.MainSectorId = dbo.TradeSector.SectorId

    LEFT OUTER JOIN dbo.CrmInstitutionalCustomerType
        ON  dbo.CrmInstitutionalCustomer.InstitutionalCustomerType = dbo.CrmInstitutionalCustomerType.TypeId

    LEFT OUTER JOIN dbo.CrmInstitutionClass
        ON  dbo.CrmInstitutionalCustomer.InstitutionClassId = dbo.CrmInstitutionClass.InstitutionClassId

    LEFT OUTER JOIN dbo.CrmInstitutionSubClass
        ON  dbo.CrmInstitutionalCustomer.InstitutionSubClassId = dbo.CrmInstitutionSubClass.InstitutionSubClassId

    LEFT JOIN CrmPersonelRelationshipList
        ON  CrmInstitutionalCustomer.InstitutionalCustomerId = CrmPersonelRelationshipList.InstitutionalCustomerId

    LEFT JOIN FoundationUsers
        ON  CrmPersonelRelationshipList.UserId = FoundationUsers.UserId

    LEFT JOIN CrmCustomerRepresentativeManagerList crml
        ON  CrmInstitutionalCustomer.InstitutionalCustomerId = crml.InstitutionalCustomerId

    LEFT OUTER JOIN CRM_RATING_DEF
        ON  dbo.CrmInstitutionalCustomer.RATING_ID = dbo.CRM_RATING_DEF.RATING_ID

    LEFT JOIN CRM_CUST_SECTOR_GROUP_LIST sector
        ON  dbo.CrmInstitutionalCustomer.InstitutionalCustomerId = sector.InstitutionalCustomerId

    LEFT JOIN dbo.CrmInstitutionalCustomerGroupDefinition csd
        ON  sector.InstitutionalCustomerGroupId = csd.InstitutionalCustomerGroupId

    LEFT JOIN dbo.CrmInstitutionalCustomerStatus cs
        ON  dbo.CrmInstitutionalCustomer.InstitutionalCustomerStatus = cs.InstitutionalCustomerStatusId

WHERE ISNULL(dbo.CrmInstitutionalCustomer.Deleted, '0') = 0
