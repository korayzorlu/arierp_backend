SELECT
    dbo.CrmInstitutionalCustomer.BANK_CODE,
    dbo.CrmInstitutionalCustomer.InstitutionalCustomerId,
    dbo.CrmInstitutionalCustomer.InstitutionalCustomerCode,
    dbo.CrmInstitutionalCustomer.InstitutionalCustomerName,
    dbo.CrmInstitutionalCustomer.COMPANYNAME_ARABIC,
    dbo.TradeSector.MultipleCompanyCode AS SECTOR_CODE,
    CrmInstitutionalCustomer_1.InstitutionalCustomerName AS ParentCompanyName,
    dbo.CrmInstitutionalCustomer.BusinessArea,
    dbo.ParameterSelectTypeValue(
        'CompanyOrganizationalStatus',
        dbo.CrmInstitutionalCustomer.OrganizationalStatus,
        'tr-TR'
    ) AS OrganizationalStatusText,
    dbo.CrmInstitutionalCustomerType.TypeCode AS InstitutionalCustomerType,
    dbo.CrmInstitutionalCustomer.InstitutionalCustomerType AS InstitutionalCustomerTypeId,
    dbo.TradeSector.SectorName,
    dbo.CrmInstitutionalCustomer.EMail,
    dbo.CrmInstitutionalCustomer.Phone,
    dbo.CrmAddressDefaultCompanyList.Fax,
    dbo.CrmInstitutionalCustomer.WebSite,
    dbo.CrmAddressDefaultCompanyList.RegionId,
    dbo.CrmAddressDefaultCompanyList.Address,
    dbo.CrmCountry.CountryId,
    dbo.CrmCountry.CountryName,
    dbo.CrmAddressDefaultCompanyList.CityId,
    dbo.CrmAddressDefaultCompanyList.CityName,
    dbo.CrmAddressDefaultCompanyList.QuarterName,
    dbo.CrmAddressDefaultCompanyList.DistrictName,
    dbo.CrmAddressDefaultCompanyList.PostalCode,
    dbo.CrmInstitutionalCustomer.ParentCompanyId,
    dbo.CrmInstitutionalCustomer.OrganizationalStatus,
    dbo.CrmInstitutionalCustomer.InstitutionalCustomerStatus,
    cs.InstitutionalCustomerStatusName,
    dbo.CrmInstitutionalCustomer.MainSectorId,
    dbo.CrmInstitutionalCustomer.EstablishmentStructure,
    dbo.CrmInstitutionalCustomer.ForeignCapital,
    dbo.CrmInstitutionalCustomer.ForeignCapitalRatio,
    dbo.CrmInstitutionalCustomer.ForeignCapitalCountryId,
    dbo.CrmInstitutionalCustomer.EstablishmentYear,
    dbo.CrmInstitutionalCustomer.CommercialRegisterNo,
    dbo.CrmTaxDepartment.TaxDepartmentName,
    dbo.CrmInstitutionalCustomer.TaxNo,
    dbo.CrmCompanyGroup.CompanyGroupName,
    dbo.CrmInstitutionClass.InstitutionClassName,
    dbo.CrmInstitutionSubClass.InstitutionSubClassName,
    dbo.CrmInstitutionalCustomer.Approved,
    dbo.CrmInstitutionalCustomer.Deleted,
    dbo.CrmInstitutionalCustomer.CompanyGroupId,
    dbo.CrmInstitutionalCustomer.CreatorCompanyCode,
    dbo.CrmInstitutionalCustomer.CreatorCompanyId,
    dbo.CrmInstitutionalCustomer.MultipleCompanyCode,
    dbo.CrmInstitutionalCustomer.MultipleCompanyId,
    dbo.CrmInstitutionalCustomer.InstitutionClassId,
    dbo.CrmInstitutionalCustomer.RecordStatus,
    ISNULL(dbo.CrmInstitutionalCustomer.RecordStatus, 0) AS IsPassive,
    CASE ISNULL(dbo.CrmInstitutionalCustomer.RecordStatus, 0)
        WHEN 0 THEN 'H'
        ELSE 'E'
    END AS IS_PASSIVE,
    dbo.CrmInstitutionalCustomer.PART_ID,
    dbo.CrmInstitutionalCustomer.InstitutionalCustomerId AS CustomerNo,
    dbo.CrmInstitutionalCustomer.CommercialRegistrationDepId,
    dbo.CrmCommercialRegistrationDepartment.CommercialRegistrationDepName,
    dbo.GetInstitutionalCustomerRelations(
        CrmInstitutionalCustomer.InstitutionalCustomerId
    ) AS RelationshipId,
    ISNULL(FoundationUsers.Name, '') + ' ' + ISNULL(FoundationUsers.Surname, '') AS CustomerRepresentative,
    crml.CustomerRepresentativeManagerName,
    CrmPersonelRelationshipList.UserId AS CustomerRepresentativeId,
    (
        SELECT ParameterName
        FROM   dbo.FoundationParameter
        WHERE  ParameterGroupCode = 'CrmDataStatus'
          AND  ParameterId = CrmInstitutionalCustomer.DataStatusId
    ) AS DataStatusName,
    dbo.CrmInstitutionalCustomer.COMMERCIAL_REG_BEGIN_DATE,
    dbo.CrmInstitutionalCustomer.COMMERCIAL_REG_END_DATE,
    CRM_RATING_DEF.RATING,
    crml.BeginDate AS CustomerRepresentativeManagerDate,
    csd.InstitutionalCustomerGroupName,
    CONVERT(
        VARCHAR(10),
        (SELECT DATEPART(YEAR, dbo.CrmInstitutionalCustomer.EstablishmentYear))
    ) AS EstablishmentYearOnly,
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
