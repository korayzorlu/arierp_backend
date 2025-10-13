SELECT
    0 AS TrnConsolideId,
    '' AS TrnConsolideInfo,
    TrnId,
    TrnSourceType,
    TrnIsDeleted,
    PART_ID,
    CrmCustomerWithTypesLightTradeRisk.CustomerId AS CustomerId,
    CrmCustomerWithTypesLightTradeRisk.CustomerName AS viewTrnAccountId,
    RATING,
    TrnAccountId,
    TrnDescription,
    TrnOffsetInfo,
    TrnCurrencyCode,
    TrnContractBlock = CASE
        WHEN ISNULL(lopStatu.OperationProjectId, 0) <> 0 THEN lopStatu.OperationProjectCode
        WHEN ISNULL(cp.ContractProjectId, 0) <> 0 THEN cp.ContractProjectCode
        ELSE CAST(TrnOprContractId AS VARCHAR(100))
    END,
    substatu.DefinitionName,
    CASE WHEN ISNULL(lopStatu.HasGuarantor, 0) = 1 THEN 'Evet' ELSE 'Hayır' END AS HasGuarantor,
    TrnPostingGroupId,
    JrnStpPstGrpName AS JrnStpPstGrpName,
    TrnTemplateType,
    TrnPostingType,
    TrnPostingTypeDetail,
    e1.JrnStpEnumDescription AS viewTrnPostingType,
    TrnReturnDocumentNo,
    TrnDueDate,
    TrnDate AS LedgeredDate,
    TrnReturnDocumentDate AS TrnReturnDocumentDate,
    TrnExchangeRateLocal,
    TrnJournalHeaderId,
    TrnOprContractId,
    TrnOprProjectId,
    ISNULL(TrnOprLeasingOperationPrjId, 0) AS TrnOprLeasingOperationPrjId,
    TrnCreateDate,
    TrnAmountType,
    TrnAmount,
    TrnAmountLocal,
    0 AS VoucherCode,
    rprData.PROJECT_NAME,
    rprData.BLOCK_NO,
    rprData.FREE_PART_NO
FROM
    TradeTransaction (NOLOCK)
    LEFT JOIN LOPRevisionJoinMainList lopStatu (NOLOCK)
        ON TrnOprLeasingOperationPrjId = lopStatu.SourceLopId
        AND TrnOprCustomerId = lopStatu.CustomerId
    LEFT JOIN TradeAccount (NOLOCK)
        ON TrnAccountId = TradeAccount.AccId
    LEFT JOIN CrmCustomerWithTypesLightTradeRisk (NOLOCK)
        ON AccCrmId = CrmCustomerWithTypesLightTradeRisk.CustomerId
    LEFT JOIN JournalSetupPostingTypeGroups (NOLOCK)
        ON TrnPostingGroupId = JournalSetupPostingTypeGroups.JrnStpPstGrpId
    LEFT JOIN JournalSetupEnums e1 (NOLOCK)
        ON TrnPostingType = e1.JrnStpEnumValue
        AND e1.JrnStpEnumType = 50
    LEFT JOIN FoundationStatuteMenu substatu (NOLOCK)
        ON lopStatu.LastSubStatuId = substatu.DefinitionId
    LEFT JOIN ContractProject cp (NOLOCK)
        ON TrnOprProjectId = cp.ContractProjectId
    LEFT JOIN QuotationProject qp (NOLOCK)
        ON cp.QuotationProjectId = qp.ProjectId
    LEFT JOIN RPR_PROJECT_VGKA_REPORT_DATA rprData (NOLOCK)
        ON TrnOprLeasingOperationPrjId = rprData.OPERATION_PROJECT_ID
WHERE
    TrnDummy = 0
    AND (
        CASE
            WHEN TrnIsDeleted = 4
                AND lopStatu.RiskIncludingTypeId = 7
                AND (
                    SELECT lll.RiskIncludingTypeId
                    FROM LeasingOperationProject lll (NOLOCK)
                    WHERE lll.OperationProjectId = lopStatu.OperationProjectId
                ) = 6
            THEN 3
            WHEN TrnIsDeleted = 4
                AND lopStatu.RiskIncludingTypeId = 6
                AND (
                    SELECT TOP 1 lll.RiskIncludingTypeId
                    FROM LOPRevisionJoinListOutPlan lll (NOLOCK)
                    WHERE (
                        lll.OperationProjectId = TrnOprRevisionLOPId
                        AND TrnOprRevisionLOPId <> 0
                    )
                    OR (
                        lll.OperationProjectId = TrnOprLeasingOperationPrjId
                        AND TrnOprRevisionLOPId = 0
                    )
                ) = 7
            THEN 3
            ELSE TrnIsDeleted
        END NOT IN (6, 4, 2, 8, 1)
        OR (TrnIsDeleted = 6 AND TrnAmount <> 0)
    )
    AND (TrnAmount <> 0 OR TrnAmountLocal <> 0 OR TrnAmountCompany <> 0)
    AND TrnLayer = 1
    AND TrnLedgerStatu = 50
    AND NOT (TrnIsDeleted = 2 AND TrnPostingType > 120 AND TrnPostingType < 110)
    -- AND TrnAccountId = 36077
    AND TrnPostingType <> 461
    -- AND TrnOprContractId = 59061
    -- AND TrnOprProjectId = 61034
    -- AND TrnOprLeasingOperationPrjId = 93862
    AND (
        lopStatu.LastSubStatuId IN (
            405, 416, 415, 402, 2028, 2057, 2041, 2058, 2059, 408, 2073, 806, 412, 2047, 503, 1026, 1014, 2032, 2072,
            4507, 2060, 406, 2031, 2061, 1009, 414, 1010, 2065, 2066, 2062, 410, 401, 403, 1007, 1019, 805, 1041,
            2029, 2063, 2064, 400, 404
        )
        OR ISNULL(TrnOprLeasingOperationPrjId, 0) = 0
    )
    AND TrnPostingGroupId IN (1, 4, 6, 7, 9, 13, 16, 17, 19, 20, 21, 23, 27, 28, 29)
    AND TrnAccountType = 11
ORDER BY
    TrnAccountId,
    TrnCurrencyCode,
    TrnOprContractId,
    TrnOprProjectId,
    TrnDueDate,
    TrnId