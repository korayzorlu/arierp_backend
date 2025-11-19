SELECT 
    TrnConsolideId,
    TrnConsolideInfo,
    PART_ID,
    TrnAccountId,
    TrnAccountCode,
    TrnAccountCrmId,
    TrnAccountIdText,
    TrnDescription,
    SUM(TrnAmountLocal) AS TrnAmountLocal
FROM (
    SELECT 
        0 AS TrnConsolideId,
        '' AS TrnConsolideInfo,
        PART_ID,
        TrnAccountId,
        TrnAccountCode,
        CrmCustomerWithTypesLightTradeRisk.CustomerId AS TrnAccountCrmId,
        CrmCustomerWithTypesLightTradeRisk.CustomerName AS TrnAccountIdText,
        'Bakiyesi' AS TrnDescription,
        (TrnAmountLocal * TrnAmountType) - (TrnAmountLocal * (1 - TrnAmountType)) AS TrnAmountLocal
    FROM TradeTransaction (NOLOCK)
        LEFT JOIN TradeAccount (NOLOCK) 
            ON TrnAccountId = TradeAccount.AccId
        LEFT JOIN CrmCustomerWithTypesLightTradeRisk (NOLOCK) 
            ON AccCrmId = CrmCustomerWithTypesLightTradeRisk.CustomerId
        LEFT JOIN LOPRevisionJoinMainList lopStatu (NOLOCK)  
            ON TrnOprLeasingOperationPrjId = lopStatu.SourceLopId 
            AND TrnOprCustomerId = lopStatu.CustomerId
        LEFT JOIN ContractProject cprj (NOLOCK) 
            ON TrnOprProjectId = cprj.ContractProjectId
        LEFT JOIN FoundationStatuteMenu substatu (NOLOCK) 
            ON lopStatu.LastSubStatuId = substatu.DefinitionId
        LEFT JOIN JournalSetupPostingTypeGroups (NOLOCK) 
            ON TrnPostingGroupId = JournalSetupPostingTypeGroups.JrnStpPstGrpId
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
                        WHERE 
                            (lll.OperationProjectId = TrnOprRevisionLOPId AND TrnOprRevisionLOPId <> 0)
                            OR (lll.OperationProjectId = TrnOprLeasingOperationPrjId AND TrnOprRevisionLOPId = 0)
                    ) = 7 
                THEN 3
                ELSE TrnIsDeleted
            END NOT IN (6, 4, 2, 8, 1)
            OR (TrnIsDeleted = 6 AND TrnAmount <> 0)
        )
        AND (TrnAmount <> 0 OR TrnAmountLocal <> 0 OR TrnAmountCompany <> 0)
        AND TrnLayer = 1
        AND TrnLedgerStatu = 50
        AND NOT (
            TrnIsDeleted = 2 
            AND TrnPostingType > 120 
            AND TrnPostingType < 110
        )
        AND TrnPostingType <> 461
        AND (
            lopStatu.LastSubStatuId IN (
                405,416,415,402,2028,2057,2041,2058,2059,408,2073,806,412,2047,503,1026,1014,2032,2072,
                4507,2060,406,2031,2061,1009,414,1010,2065,2066,2062,410,401,403,1007,1019,805,1041,
                2029,2063,2064,400,404
            )
            OR ISNULL(TrnOprLeasingOperationPrjId, 0) = 0
        )
        AND TrnPostingGroupId = 13
        AND TrnAccountType = 11
        --AND CrmCustomerWithTypesLightTradeRisk.CustomerName LIKE 'AYŞE KELEŞ%'
) X
GROUP BY 
    TrnConsolideId,
    TrnConsolideInfo,
    PART_ID,
    TrnAccountId,
    TrnAccountCode,
    TrnAccountCrmId,
    TrnAccountIdText,
    TrnDescription
HAVING SUM(TrnAmountLocal) <> 0