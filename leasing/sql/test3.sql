SELECT
    TrnOprContractId,
    TrnOprLeasingOperationPrjId,
    TrnPostingGroupId,
    TrnAmountCapital,
    TrnAmountInterest,
    TrnVATAmount,
    TrnAmountType,
    TrnAmount,
    TrnCurrencyCode,
    SUM(
        (
            CASE
                WHEN (
                    (
                        lopStatu.RiskIncludingTypeId IN (6)
                        AND TrnLedgerStatu = 10
                        AND TrnPostingType BETWEEN 110 AND 120
                        AND TrnIsDeleted <> 9
                        AND TrnDueDate <= '20260121'
                        AND ISNULL(xx.OperationProjectId_Count, 0) = 0
                    )
                    OR
                    (
                        lopStatu.RiskIncludingTypeId IN (6)
                        AND TrnLedgerStatu = 10
                        AND TrnPostingType BETWEEN 110 AND 120
                        AND TrnIsDeleted <> 9
                        AND TrnDueDate <= '20260121'
                        AND ISNULL(xx.OperationProjectId_Count, 0) = 1
                    )
                )
                THEN TrnAmountCapital + TrnAmountInterest + TrnVATAmount
                ELSE TrnAmount
            END
        ) * TrnAmountType
    ) AS AmountDebit,
    SUM(
        (
            CASE
                WHEN (
                    lopStatu.RiskIncludingTypeId = 6
                    AND TrnLedgerStatu = 10
                    AND (
                        (TrnIsDeleted <> 9 AND TrnPostingType BETWEEN 110 AND 120)
                        OR (TrnPostingType = 420 AND TrnReturnDocumentNo LIKE 'P%')
                    )
                    AND TrnDueDate <= '20260121'
                    AND ISNULL(xx.OperationProjectId_Count, 0) = 0
                )
                THEN TrnAmountCapital + TrnAmountInterest + TrnVATAmount
                ELSE TrnAmount
            END
        ) * (1 - TrnAmountType)
    ) AS AmountCredit
FROM TradeTransaction (NOLOCK)
LEFT JOIN LeasingOperationProject lopStatu (NOLOCK)
    ON TrnOprLeasingOperationPrjId = lopStatu.SourceLOPId
LEFT JOIN (
    SELECT
        kk.OperationProjectId AS OperationProject_Id,
        COUNT(*) AS OperationProjectId_Count
    FROM LeasingOperationProject kk (NOLOCK)
    WHERE NOT (
        kk.RiskIncludingTypeId IN (3, 6)
        OR (kk.RiskIncludingTypeId IN (9, 5, 7) AND kk.OperationTypeId = 1)
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
                        (lll.OperationProjectId = TrnOprRevisionLOPId AND TrnOprRevisionLOPId <> 0)
                        OR (lll.OperationProjectId = TrnOprLeasingOperationPrjId AND TrnOprRevisionLOPId = 0)
                    )
                ) = 7
            THEN 3
            ELSE TrnIsDeleted
        END
        NOT IN (6, 4, 2, 8, 1)
        OR (TrnIsDeleted = 6 AND TrnAmount <> 0)
    )
    AND TrnPostingType NOT IN (461, 113)
    AND (
        TrnLayer = 1
        OR (
            lopStatu.RiskIncludingTypeId IN (6, 7)
            AND TrnLayer = 3
            AND TrnPostingType BETWEEN 110 AND 120
            AND TrnDueDate <= '20260121'
            AND ISNULL(xx.OperationProjectId_Count, 0) = 0
        )
        OR (
            lopStatu.RiskIncludingTypeId IN (7)
            AND TrnLayer = 3
            AND TrnPostingType BETWEEN 110 AND 120
            AND TrnDueDate <= '20260121'
            AND ISNULL(xx.OperationProjectId_Count, 0) = 1
        )
    )
    AND (
        TrnLedgerStatu = 50
        OR (
            lopStatu.RiskIncludingTypeId IN (7, 6)
            AND TrnLedgerStatu = 10
            AND TrnPostingType BETWEEN 110 AND 120
            AND TrnDueDate <= '20260121'
            AND ISNULL(xx.OperationProjectId_Count, 0) = 0
        )
        OR (
            lopStatu.RiskIncludingTypeId IN (7)
            AND TrnLedgerStatu = 10
            AND TrnPostingType BETWEEN 110 AND 120
            AND TrnDueDate <= '20260121'
            AND ISNULL(xx.OperationProjectId_Count, 0) = 1
        )
    )
    AND TrnAccountType = 11
    AND lopStatu.IS_LAST_PROJECT = 1
    AND TrnOprLeasingOperationPrjId <> 0
    AND NOT (
        lopX.OperationTypeId = 1
        AND lopX.RiskIncludingTypeId IN (9)
        AND TrnPostingType BETWEEN 110 AND 120
    )
    AND TrnDueDate <= CONVERT(DATETIME, '2026-1-21', 102)
    AND TrnOprLeasingOperationPrjId = '67721'
GROUP BY
    TrnOprContractId,
    TrnOprLeasingOperationPrjId,
    TrnPostingGroupId,
    TrnAmountCapital,
    TrnAmountInterest,
    TrnVATAmount,
    TrnAmountType,
    TrnAmount,
    TrnCurrencyCode
