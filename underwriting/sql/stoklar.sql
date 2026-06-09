SELECT CustomerName,
       FREE_PART_ID,
       PROJECT_ID,
       HizliTeklifSozlesmeNo,
       TeklifSozlesmeNo,
       QUO_HEADER_ID,
       ContractHeaderId,
       PROJECT_NAME,
       STAGE_NAME,
       BLOCK_NO,
       FREE_PART_NO,
       ISLAND_NO,
       PLOT_NO,
       PARCEL_NO,
       ISNULL(IS_DELETED, 0),
       BBSN_NO
  FROM (
    SELECT
        CASE WHEN (CASE WHEN rf.QUO_HEADER_ID = 0 THEN ISNULL(item.QUO_HEADER_ID, 0) ELSE rf.QUO_HEADER_ID END) > 0
             THEN qh.CustomerName
             ELSE qh2.CustomerName
        END AS CustomerName,
        rf.FREE_PART_ID,
        rf.NET_AREA,
        rf.PROJECT_ID,
        qh.ContractHeaderId HizliTeklifSozlesmeNo,
        qh2.ContractHeaderId TeklifSozlesmeNo,
        CASE WHEN rf.QUO_HEADER_ID = 0 THEN ISNULL(item.QUO_HEADER_ID, 0) ELSE rf.QUO_HEADER_ID END QUO_HEADER_ID,
        CASE WHEN ISNULL(item.QUO_HEADER_ID, 0) > 0
             THEN qh.ContractHeaderId
             ELSE qh2.ContractHeaderId
        END AS ContractHeaderId,
        rp.PROJECT_NAME,
        ISNULL(rs.STAGE_NAME, '') STAGE_NAME,
        rb.BLOCK_NO,
        rf.FREE_PART_NO,
        rf.ISLAND_NO,
        rf.PLOT_NO,
        rf.PARCEL_NO,
        rf.IS_DELETED,
        rf.BBSN_NO
      FROM dbo.RPR_PROJECT_FREE_PART rf
      LEFT JOIN (
            SELECT *
              FROM RPR_QUO_ITEM q
             WHERE RPR_QUO_ID = (SELECT MAX(i.RPR_QUO_ID) FROM RPR_QUO_ITEM i WHERE i.FREE_PART_ID = q.FREE_PART_ID AND i.IS_DELETED = 0)
           ) item ON item.FREE_PART_ID = rf.FREE_PART_ID AND item.IS_DELETED = 0
      LEFT JOIN (
            SELECT TOP 100 PERCENT
                   dbo.QuotationHeader.QuotationHeaderId,
                   dbo.CrmCustomerWithTypes.CustomerName,
                   dbo.QuotationCreditType.TypeName AS CreditTypeName,
                   dbo.QuotationAmount.CustomerBaseCost AS LeasingBaseCost,
                   dbo.GeneralCurrency.CurrencyCode,
                   dbo.QuotationHeader.RequestDate,
                   dbo.FoundationUsers.Name + ' ' + dbo.FoundationUsers.Surname AS CustomerRepresentative,
                   dbo.QuotationHeader.CreditHeaderId,
                   dbo.QuotationHeader.ContractHeaderId,
                   CAST(dbo.QuotationHeader.QuotationHeaderId AS varchar)
                   + ', ' + ISNULL(dbo.CrmCustomerWithTypes.CustomerName, '<>')
                   + ', ' + CAST(DAY(dbo.QuotationHeader.RequestDate) AS VARCHAR)
                   + '.' + CAST(MONTH(dbo.QuotationHeader.RequestDate) AS VARCHAR)
                   + '.' + CAST(YEAR(dbo.QuotationHeader.RequestDate) AS VARCHAR)
                   + ', ' + CAST(dbo.QuotationAmount.LeasingBaseCost AS varchar)
                   + ' ' + dbo.GeneralCurrency.CurrencyCode AS QuotationSummary,
                   dbo.QuotationReferenceType.TypeName AS ReferenceTypeName,
                   CrmInstitutionalCustomer_reference.InstitutionalCustomerName AS ReferenceName,
                   dbo.QuotationHeader.CustomerRepresentative AS CustomerRepresentativeId,
                   dbo.QuotationHeader.CustomerId,
                   dbo.QuotationHeader.TargetDate,
                   dbo.QuotationHeader.IsLOPRevision,
                   dbo.CrmContact.Name + ' ' + dbo.CrmContact.Surname AS ContactName,
                   dbo.QuotationHeader.ReferenceType,
                   dbo.QuotationHeader.CurrencyId,
                   dbo.QuotationHeader.Reference,
                   dbo.FoundationStatuteMenu.DefinitionName AS SubStatuteName,
                   dbo.QuotationHeader.ValidityDate,
                   dbo.FndStatuteOrderedQuo.ParentStatuteId,
                   dbo.FndStatuteOrderedQuo.SubStatuteId,
                   CrmCustomerWithTypes.TaxNo,
                   CrmCustomerWithTypes.Phone
              FROM dbo.QuotationHeader
              INNER JOIN dbo.QuotationAmount ON dbo.QuotationHeader.QuotationHeaderId = dbo.QuotationAmount.ObjectId
              LEFT OUTER JOIN dbo.FndStatuteOrderedQuo ON dbo.QuotationHeader.QuotationHeaderId = dbo.FndStatuteOrderedQuo.RecordId
              LEFT OUTER JOIN dbo.CrmContact ON dbo.QuotationHeader.ContactId = dbo.CrmContact.ContactId
              LEFT OUTER JOIN dbo.CrmInstitutionalCustomer CrmInstitutionalCustomer_reference ON dbo.QuotationHeader.Reference = CrmInstitutionalCustomer_reference.InstitutionalCustomerId
              LEFT OUTER JOIN dbo.QuotationReferenceType ON dbo.QuotationHeader.ReferenceType = dbo.QuotationReferenceType.TypeId
              LEFT OUTER JOIN dbo.QuotationCreditType ON dbo.QuotationHeader.CreditTypeId = dbo.QuotationCreditType.TypeId
              LEFT OUTER JOIN dbo.CrmCustomerWithTypes ON dbo.QuotationHeader.CustomerId = dbo.CrmCustomerWithTypes.CustomerId
              LEFT OUTER JOIN dbo.FoundationUsers ON dbo.QuotationHeader.CustomerRepresentative = dbo.FoundationUsers.UserId
              LEFT OUTER JOIN dbo.GeneralCurrency ON dbo.QuotationHeader.CurrencyId = dbo.GeneralCurrency.CurrencyId
              LEFT OUTER JOIN dbo.FoundationStatuteMenu ON dbo.FoundationStatuteMenu.DefinitionId = dbo.FndStatuteOrderedQuo.SubStatuteId
             WHERE ISNULL(dbo.QuotationHeader.Deleted, '0') = '0'
               AND (dbo.QuotationHeader.IsTemplate = 0 OR dbo.QuotationHeader.IsTemplate = 2)
               AND dbo.QuotationAmount.ObjectTypeId = 1
             ORDER BY dbo.QuotationHeader.QuotationHeaderId DESC
           ) qh2 ON rf.QUO_HEADER_ID = -qh2.QuotationHeaderId
      LEFT JOIN (
            SELECT TOP 100 PERCENT
                   dbo.QuotationHeader.QuotationHeaderId,
                   dbo.CrmCustomerWithTypes.CustomerName,
                   dbo.QuotationCreditType.TypeName AS CreditTypeName,
                   dbo.QuotationAmount.CustomerBaseCost AS LeasingBaseCost,
                   dbo.GeneralCurrency.CurrencyCode,
                   dbo.QuotationHeader.RequestDate,
                   dbo.FoundationUsers.Name + ' ' + dbo.FoundationUsers.Surname AS CustomerRepresentative,
                   dbo.QuotationHeader.CreditHeaderId,
                   dbo.QuotationHeader.ContractHeaderId,
                   CAST(dbo.QuotationHeader.QuotationHeaderId AS varchar)
                   + ', ' + ISNULL(dbo.CrmCustomerWithTypes.CustomerName, '<>')
                   + ', ' + CAST(DAY(dbo.QuotationHeader.RequestDate) AS VARCHAR)
                   + '.' + CAST(MONTH(dbo.QuotationHeader.RequestDate) AS VARCHAR)
                   + '.' + CAST(YEAR(dbo.QuotationHeader.RequestDate) AS VARCHAR)
                   + ', ' + CAST(dbo.QuotationAmount.LeasingBaseCost AS varchar)
                   + ' ' + dbo.GeneralCurrency.CurrencyCode AS QuotationSummary,
                   dbo.QuotationReferenceType.TypeName AS ReferenceTypeName,
                   CrmInstitutionalCustomer_reference.InstitutionalCustomerName AS ReferenceName,
                   dbo.QuotationHeader.CustomerRepresentative AS CustomerRepresentativeId,
                   dbo.QuotationHeader.CustomerId,
                   dbo.QuotationHeader.TargetDate,
                   dbo.QuotationHeader.IsLOPRevision,
                   dbo.CrmContact.Name + ' ' + dbo.CrmContact.Surname AS ContactName,
                   dbo.QuotationHeader.ReferenceType,
                   dbo.QuotationHeader.CurrencyId,
                   dbo.QuotationHeader.Reference,
                   dbo.FoundationStatuteMenu.DefinitionName AS SubStatuteName,
                   dbo.QuotationHeader.ValidityDate,
                   dbo.FndStatuteOrderedQuo.ParentStatuteId,
                   dbo.FndStatuteOrderedQuo.SubStatuteId,
                   CrmCustomerWithTypes.TaxNo,
                   CrmCustomerWithTypes.Phone
              FROM dbo.QuotationHeader
              INNER JOIN dbo.QuotationAmount ON dbo.QuotationHeader.QuotationHeaderId = dbo.QuotationAmount.ObjectId
              LEFT OUTER JOIN dbo.FndStatuteOrderedQuo ON dbo.QuotationHeader.QuotationHeaderId = dbo.FndStatuteOrderedQuo.RecordId
              LEFT OUTER JOIN dbo.CrmContact ON dbo.QuotationHeader.ContactId = dbo.CrmContact.ContactId
              LEFT OUTER JOIN dbo.CrmInstitutionalCustomer CrmInstitutionalCustomer_reference ON dbo.QuotationHeader.Reference = CrmInstitutionalCustomer_reference.InstitutionalCustomerId
              LEFT OUTER JOIN dbo.QuotationReferenceType ON dbo.QuotationHeader.ReferenceType = dbo.QuotationReferenceType.TypeId
              LEFT OUTER JOIN dbo.QuotationCreditType ON dbo.QuotationHeader.CreditTypeId = dbo.QuotationCreditType.TypeId
              LEFT OUTER JOIN dbo.CrmCustomerWithTypes ON dbo.QuotationHeader.CustomerId = dbo.CrmCustomerWithTypes.CustomerId
              LEFT OUTER JOIN dbo.FoundationUsers ON dbo.QuotationHeader.CustomerRepresentative = dbo.FoundationUsers.UserId
              LEFT OUTER JOIN dbo.GeneralCurrency ON dbo.QuotationHeader.CurrencyId = dbo.GeneralCurrency.CurrencyId
              LEFT OUTER JOIN dbo.FoundationStatuteMenu ON dbo.FoundationStatuteMenu.DefinitionId = dbo.FndStatuteOrderedQuo.SubStatuteId
             WHERE ISNULL(dbo.QuotationHeader.Deleted, '0') = '0'
               AND (dbo.QuotationHeader.IsTemplate = 0 OR dbo.QuotationHeader.IsTemplate = 2)
               AND dbo.QuotationAmount.ObjectTypeId = 1
             ORDER BY dbo.QuotationHeader.QuotationHeaderId DESC
           ) qh ON item.QUO_HEADER_ID = qh.QuotationHeaderId
      LEFT JOIN dbo.RPR_PROJECT_BLOCK rb ON rb.BLOCK_ID = rf.BLOCK_ID
      LEFT JOIN dbo.RPR_PROJECT rp ON rp.PROJECT_ID = rf.PROJECT_ID
      LEFT JOIN dbo.RPR_PROJECT_STAGE rs ON rs.STAGE_ID = rb.STAGE_ID
  ) x
 WHERE ISNULL(IS_DELETED, 0) = 0
