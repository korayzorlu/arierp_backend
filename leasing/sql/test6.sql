SELECT
    lop.OperationProjectId,
    lop.CustomerId,
    cclc.CustomerName,
    cclc.TaxAndTCIdentity,
    lop.OperationProjectCode,
    ch.ContractHeaderId,
    ch.ContractHeaderCode,
    lop.QuotationHeaderId,
    lop.CreditHeaderId,
    lot.TypeName,
    lorit.TypeName AS RiskIncludingTypeName,
    lop.VatRate,
    lop.ActivationDate,
    lop.NotaryPublicDate,
    lop.ContractRegistrationNumber,
    QuotationUser.Name + ' ' + QuotationUser.Surname AS QuotationUserName,
    OperationUser.Name + ' ' + OperationUser.Surname AS OperationUserName,
    lop.AppliedTaxAdvantageRate,
    lop.KKDF_RATE,
    lop.CustomerBaseCost,
    gc.CurrencyCode,
    lop.PaymentCount,
    lop.AnnualRate,
    lop.ContractProjectId,
    lop.TransferCode,
    lop.LastSubStatuId AS SubStatuteId,
    lop.LastParentStatuId AS ParentStatuteId,
    d.DefinitionName AS SubStatuteName,
    fu.UnitName,
    lop.OperationBaseIRR,
    cclc.PART_ID,
    lop.OperationTypeId,
    lop.RiskIncludingTypeId,
    (
        CASE
            WHEN lop.ApplicationID < 0 THEN 'S' + CAST(ABS(lop.ApplicationID) AS VARCHAR(50))
            ELSE CAST(lop.ApplicationID AS VARCHAR(50))
        END
    ) AS ApplicationID,
    CAST(lop.IsInterestSupport AS BIT) AS IsInterestSupport,
    qlt.LeasingTypeName,
    CAST(lop.SpecialSituationId AS BIT) AS IsCancelFromActivation,
    lop.FacilityID,
    fu.UnitName AS ADNLBranch,
    (
        SELECT TOP 1 tac.AccName
        FROM dbo.TradeAccountAndTypeComboCrmList tac
        WHERE tac.AccCrmId = (
            SELECT TOP 1 qld.VendorId
            FROM dbo.QuotationLineDetail qld
            WHERE qld.QuotationHeaderId = qh.QuotationHeaderId
              AND ISNULL(qld.Deleted, 0) = 0
              AND qld.ItemTreeId <> 14
        )
        AND tac.AccTypType = 21
    ) AS Vendor,
    (
        SELECT TOP 1 stk.StockName
        FROM dbo.InventoryStockCode stk
        WHERE stk.StockCodeId = (
            SELECT TOP 1 qld.StockCodeId
            FROM dbo.QuotationLineDetail qld
            WHERE qld.QuotationHeaderId = qh.QuotationHeaderId
              AND ISNULL(qld.Deleted, 0) = 0
              AND qld.ItemTreeId <> 14
        )
    ) AS Project,
    lop.IS_LAST_PROJECT,
    CASE
        WHEN lop.IS_PERT_APPROVED = 1 THEN 'Tam Pert Talebi'
        WHEN lop.IS_PERT_APPROVED = 2 THEN 'Revize Talebi'
        WHEN lop.IS_PERT_APPROVED = 3 THEN 'Erken Kapama Talebi'
        WHEN lop.IS_PERT_APPROVED = 4 THEN 'Ana Statüyü Kredi Kapandı Statüsüne Alma Talebi'
        WHEN lop.IS_PERT_APPROVED = 5 THEN 'Ana Statüyü Kapanmadan Önceki Statüye Alma Talebi'
        ELSE ''
    END AS CurrentRequest,
    qpvt.VendorTypeName,
    CASE
        WHEN (
            SELECT TOP 1 pay.IsCpiRent
            FROM dbo.LeasingOperationPayment pay
            WHERE pay.OperationProjectId = lop.OperationProjectId
            ORDER BY pay.IsCpiRent DESC
        ) = 1 THEN 'Evet'
        ELSE 'Hayır'
    END AS IsCpiContract,
    CASE
        WHEN (
            SELECT TOP 1 SOURCE_LOP_ID
            FROM dbo.LOP_CORPORATES (NOLOCK)
            WHERE SOURCE_LOP_ID = lop.SourceLOPId
              AND ISNULL(IS_DELETED, 0) = 0
        ) >= 1 THEN 'Evet'
        ELSE 'Hayır'
    END AS Corporates,
    (
        SELECT TOP 1 BBSN_NO
        FROM dbo.RPR_PROJECT_FREE_PART (NOLOCK)
        WHERE QUO_HEADER_ID = lop.ApplicationID
          AND ISNULL(IS_DELETED, 0) = 0
    ) AS BBSN_NO
FROM
    dbo.LeasingOperationProject lop
    INNER JOIN dbo.GeneralCurrency gc (NOLOCK) ON lop.CurrencyId = gc.CurrencyId
    LEFT OUTER JOIN dbo.ContractHeader ch (NOLOCK) ON lop.ContractHeaderId = ch.ContractHeaderId
    LEFT OUTER JOIN dbo.QuotationHeader qh (NOLOCK) ON lop.QuotationHeaderId = qh.QuotationHeaderId
    LEFT OUTER JOIN dbo.QuotationLeasingType qlt (NOLOCK) ON qh.LeasingType = qlt.LeasingTypeId
    LEFT OUTER JOIN dbo.FoundationUnit fu (NOLOCK) ON lop.LocationId = fu.UnitId
    LEFT OUTER JOIN dbo.LeasingOperationRiskIncludingType lorit (NOLOCK) ON lop.RiskIncludingTypeId = lorit.TypeId
    LEFT OUTER JOIN dbo.CrmCustomerListCombo cclc (NOLOCK) ON lop.CustomerId = cclc.CustomerId
    LEFT OUTER JOIN dbo.LeasingOperationType lot (NOLOCK) ON lop.OperationTypeId = lot.TypeId
    LEFT OUTER JOIN FoundationStatuteMenu m (NOLOCK) ON lop.LastSubStatuId = m.DefinitionId AND m.TableName = 'LeasingOperationProject'
    LEFT OUTER JOIN dbo.FoundationStatuteMenuParent p (NOLOCK) ON lop.LastParentStatuId = p.Id
    LEFT OUTER JOIN FoundationStatuteMenu d (NOLOCK) ON m.DefinitionId = d.DefinitionId AND d.TableName = 'LeasingOperationProject'
    LEFT OUTER JOIN FoundationUsers QuotationUser (NOLOCK) ON QuotationUser.UserId = lop.QuotationUserId
    LEFT OUTER JOIN FoundationUsers OperationUser (NOLOCK) ON OperationUser.UserId = lop.OperationUserId
    LEFT OUTER JOIN dbo.QuotationProjectVendorType qpvt (NOLOCK) ON qpvt.VendorTypeId = lop.VendorTypeId