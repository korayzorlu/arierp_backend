SELECT
    TrnId,
    TrnIsDeleted,
    TrnJournalHeaderId,
    TrnTemplateType,
    TrnPostingType,
    TrnPostingTypeDetail,
    TrnPostingGroupId,
    TrnAccountId,
    TrnAccountCode,
    TrnOprCustomerId,
    TrnOprContractId,
    TrnOprProjectId,
    TrnOprLeasingOperationPrjId,
    TrnCurrencyCode,
    TrnAmountType,

    (CASE
        WHEN (
            lopStatu.RiskIncludingTypeId = 6
            AND TrnLedgerStatu = 10
            AND (
                (TrnIsDeleted <> 9 AND TrnPostingType >= 110 AND TrnPostingType <= 120)
                OR (TrnPostingType = 420 AND TrnReturnDocumentNo LIKE 'P%')
            )
            AND TrnDueDate <= '20250912'
            AND ISNULL(xx.OperationProjectId_Count, 0) = 0
        )
        THEN TrnAmountCapital + TrnAmountInterest + TrnVATAmount
        ELSE TrnAmount
    END) AS TrnAmount,

    ROUND((
        (CASE
            WHEN (
                lopStatu.RiskIncludingTypeId = 6
                AND TrnLedgerStatu = 10
                AND (
                    (TrnIsDeleted <> 9 AND TrnPostingType >= 110 AND TrnPostingType <= 120)
                    OR (TrnPostingType = 420 AND TrnReturnDocumentNo LIKE 'P%')
                )
                AND TrnDueDate <= '20250912'
                AND ISNULL(xx.OperationProjectId_Count, 0) = 0
            )
            THEN TrnAmountCapital + TrnAmountInterest + TrnVATAmount
            ELSE TrnAmount
        END) * TrnExchangeRateLocal), 2
    ) AS TrnAmountLocal,

    TrnExchangeRateLocal,
    TrnExchangeRateCILocal,
    TrnAmountCapital,
    TrnAmountCapitalLocal,
    TrnAmountInterest,
    TrnVATAmount,
    TrnVATRate,
    TrnDueDate,
    TrnReturnDocumentDate,
    TrnReturnDocumentNo,
    TrnReturnDocumentDescription,

    JrnStpPstGrpName AS JrnStpPstGrpName,
    ISNULL(JrnStpPstGrpOverdueId, JrnStpPstGrpId) AS TrnPostingGroupIdOverdue,
    PART_ID,
    con.CustomerTypeId,
    AccName AS viewTrnAccountId,
    lopStatu.VatRate,
    lopStatu.RiskIncludingTypeId,
    lopStatu.OperationProjectCode,

    CAST(0 AS NUMERIC(18, 2)) AS TrnRateBSMV,
    lopStatu.AppliedTaxAdvantageAmount AS TrnRateKKDF,
    lopStatu.OVERDUE_GRACE_PERIOD,
    cp.ContractProjectCode,
    e1.JrnStpEnumDescription AS viewTrnPostingType,
    0 AS IsDeleted,

    ContractHeaderCode = CASE
        WHEN ISNULL(con.TransferCode, '') = '' THEN con.ContractHeaderCode
        ELSE con.TransferCode
    END,

    ContractHeaderCodeLop = CASE
        WHEN ISNULL(lopStatu.TransferCode, '') = '' THEN lopStatu.OperationProjectCode
        ELSE lopStatu.TransferCode
    END,

    dbo.CrmGetCustomerMailAddress(CrmCustomerWithTypesLight.OBJECT_ID, CrmCustomerWithTypesLight.CustomerTypeId) AS Email

FROM TradeTransaction (NOLOCK)

LEFT JOIN LOPRevisionJoinMainList lopStatu (NOLOCK)
    ON TrnOprLeasingOperationPrjId = lopStatu.SourceLOPId
AND TrnOprCustomerId = lopStatu.CustomerId

LEFT JOIN (
    SELECT
        kk.OperationProjectId AS OperationProject_Id,
        COUNT(*) AS OperationProjectId_Count
    FROM LeasingOperationProject kk (NOLOCK)
    WHERE NOT (
        kk.RiskIncludingTypeId IN (3, 6)
        OR (kk.RiskIncludingTypeId IN (9, 5) AND kk.OperationTypeId = 1)
    )
    GROUP BY kk.OperationProjectId
) xx
    ON xx.OperationProject_Id = lopStatu.OperationProjectId

LEFT JOIN LeasingOperationProject lopX (NOLOCK)
    ON lopX.OperationProjectId = (
        CASE
            WHEN TrnOprRevisionLOPId <> 0 THEN TrnOprRevisionLOPId
            ELSE TrnOprLeasingOperationPrjId
        END
    )

LEFT JOIN JournalSetupPostingTypeGroups (NOLOCK)
    ON TrnPostingGroupId = JournalSetupPostingTypeGroups.JrnStpPstGrpId

LEFT JOIN TradeAccount (NOLOCK)
    ON TrnAccountId = TradeAccount.AccId

LEFT JOIN ContractProject cp (NOLOCK)
    ON TrnOprProjectId = cp.ContractProjectId

LEFT JOIN ContractHeader con (NOLOCK)
    ON TrnOprContractId = con.ContractHeaderId

LEFT JOIN JournalSetupEnums e1 (NOLOCK)
    ON TrnPostingType = e1.JrnStpEnumValue
AND e1.JrnStpEnumType = 50

LEFT JOIN CrmCustomerWithTypesLight (NOLOCK)
    ON con.CustomerId = CrmCustomerWithTypesLight.CustomerId

WHERE
    TrnDummy = 0
    AND (
        TrnIsDeleted NOT IN (6,4,2,8,1)
        OR (TrnIsDeleted = 6 AND TrnAmount <> 0)
    )
    AND (
        TrnLayer = 1
        OR (
            lopStatu.RiskIncludingTypeId = 6
            AND TrnLayer = 3
            AND (
                (TrnPostingType >= 110 AND TrnPostingType <= 120)
                OR (TrnPostingType = 420 AND TrnReturnDocumentNo LIKE 'P%')
            )
            AND TrnDueDate <= '20250912'
            AND ISNULL(xx.OperationProjectId_Count, 0) = 0
        )
    )
    AND (
        ISNULL(xx.OperationProjectId_Count, 0) > 0
        OR (
            ISNULL(xx.OperationProjectId_Count, 0) = 0
            AND TrnPostingType <> 126
        )
    )
    AND (
        TrnLedgerStatu = 50
        OR (
            lopStatu.RiskIncludingTypeId = 6
            AND TrnLedgerStatu = 10
            AND TrnPostingType >= 110
            AND TrnPostingType <= 120
            AND TrnDueDate <= '20250912'
            AND ISNULL(xx.OperationProjectId_Count, 0) = 0
        )
    )
    AND TrnAccountType = 11
    AND TrnAccountId <> 0
    AND TrnDueDate <= CONVERT(DATETIME, '2025-09-12', 102)

    -- FARK BURADA
    AND TrnOprLeasingOperationPrjId IN (93235)
    --AND TrnOprContractId IN ()

    AND (
        lopStatu.LastSubStatuId IN (
            405,416,415,402,2028,2057,2041,2058,2059,
            408,2073,806,412,2047,503,1026,1014,2032,
            2072,4507,2060,406,2031,2061,1009,414,1010,
            2065,2066,2062,410,401,403,1007,1019,805,
            1041,2029,2063,2064,400,404
        )
        OR TrnOprLeasingOperationPrjId = 0
    )

    AND JrnStpPstGrpName = 'Kira'

ORDER BY
    TrnAccountId,
    TrnPostingGroupId,
    TrnOprContractId,
    TrnOprProjectId,
    TrnOprLeasingOperationPrjId,
    TrnCurrencyCode,
    TrnDueDate,
    TrnId;