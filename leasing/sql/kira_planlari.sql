SELECT
    lop.OperationTypeId,
    lop.OperationProjectId,
    lop.OperationProjectCode,
    ch.ContractHeaderCode,
    lot.TypeName,
    lorit.TypeName AS RiskIncludingTypeName,
    l.RiskIncludingLastUpdateDate AS RiskIncludingLastUpdateDate,
    lop.VatRate,
    lop.ActivationDate,
    lop.CustomerBaseCost,
    gc.CurrencyCode,
    lop.PaymentCount,
    lop.AnnualRate,
    d.DefinitionName AS SubStatuteName,
    lop.OperationBaseIRR,
    (
        CASE
            WHEN lop.ApplicationID < 0 THEN 'S' + CAST(ABS(lop.ApplicationID) AS VARCHAR(50))
            ELSE CAST(lop.ApplicationID AS VARCHAR(50))
        END
    ) AS ApplicationID,
    qlt.LeasingTypeName,
    (
        SELECT TOP 1 tac.AccCrmId
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
        SELECT TOP 1 stk.StockCodeId
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
    l.MainLopId,
    l.NotaryPublicDate,
    pb.BLOCK_NO,
    fp.FREE_PART_NO,
    fp.ISLAND_NO,
    fp.PARCEL_NO,
    fpp.TIMESHARE_PERIOD,
    pl.CityName,
    pl.DistrictName,
    lw.BBSN_NO
FROM
    dbo.LeasingOperationProject lop (NOLOCK)
    INNER JOIN dbo.GeneralCurrency gc (NOLOCK) ON lop.CurrencyId = gc.CurrencyId
    LEFT OUTER JOIN dbo.ContractHeader ch (NOLOCK) ON lop.ContractHeaderId = ch.ContractHeaderId
    LEFT OUTER JOIN dbo.QuotationHeader qh (NOLOCK) ON lop.QuotationHeaderId = qh.QuotationHeaderId
    LEFT OUTER JOIN dbo.QuotationLeasingType qlt (NOLOCK) ON qh.LeasingType = qlt.LeasingTypeId
    LEFT OUTER JOIN dbo.LeasingOperationRiskIncludingType lorit (NOLOCK) ON lop.RiskIncludingTypeId = lorit.TypeId
    LEFT OUTER JOIN dbo.LeasingOperationType lot (NOLOCK) ON lop.OperationTypeId = lot.TypeId
    LEFT OUTER JOIN FoundationStatuteMenu m (NOLOCK) ON lop.LastSubStatuId = m.DefinitionId AND m.TableName = 'LeasingOperationProject'
    LEFT OUTER JOIN dbo.FoundationStatuteMenuParent p (NOLOCK) ON lop.LastParentStatuId = p.Id
    LEFT OUTER JOIN FoundationStatuteMenu d (NOLOCK) ON m.DefinitionId = d.DefinitionId AND d.TableName = 'LeasingOperationProject'
    LEFT JOIN LeasingOperationProject l (NOLOCK) ON lop.OperationProjectId = l.OperationProjectId
    LEFT JOIN RPR_QUO_ITEM qi (NOLOCK) ON qh.QuotationHeaderId = qi.QUO_HEADER_ID
    LEFT JOIN RPR_FREE_PART_LIST_FOR_DET fp (NOLOCK) ON qi.FREE_PART_ID = fp.FREE_PART_ID
    LEFT JOIN RPR_PROJECT_FREE_PART fpp (NOLOCK) ON qi.FREE_PART_ID = fpp.FREE_PART_ID
    LEFT JOIN RPR_PROJECT_BLOCK_LIST pb (NOLOCK) ON qi.BLOCK_ID = pb.BLOCK_ID
    LEFT JOIN RPR_PROJECT_LIST pl ON qi.PROJECT_ID = pl.PROJECT_ID
    LEFT JOIN LeasingOperationProjectList lw ON lop.OperationProjectId = lw.OperationProjectId
-- WHERE
--     ch.ContractHeaderCode = '59674'
-- WHERE
-- lw.BBSN_NO = 'BBSN.140915'
--     AND lop.IS_LAST_PROJECT = 1
--     AND (
--         RiskIncludingTypeName = 'Aktifleştirildi'
--         OR RiskIncludingTypeName = 'Planlandı'
--         OR RiskIncludingTypeName = 'Durduruldu'
--     )
ORDER BY 
    pb.BLOCK_NO,
    lop.OperationProjectId DESC;