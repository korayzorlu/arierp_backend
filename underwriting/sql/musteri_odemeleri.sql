SELECT TrnOprLeasingOperationPrjId SourceLopId,
       ABS(SUM(TrnAmount * ((TrnAmountType * 2) - 1))) totalAmount
  FROM TradeTransaction(NOLOCK)
  LEFT JOIN AriRevisionJoinMainList lopStatu(NOLOCK)
    ON TrnOprLeasingOperationPrjId = lopStatu.SourceLOPId
   AND TrnOprCustomerId = lopStatu.CustomerId
  LEFT JOIN TradeAccount(NOLOCK)
    ON TrnAccountId = TradeAccount.AccId
  LEFT JOIN CrmCustomerWithTypesLightTradeRisk(NOLOCK)
    ON AccCrmId = CrmCustomerWithTypesLightTradeRisk.CustomerId
  LEFT JOIN JournalSetupPostingTypeGroups(NOLOCK)
    ON TrnPostingGroupId = JournalSetupPostingTypeGroups.JrnStpPstGrpId
  LEFT JOIN JournalSetupEnums e1(NOLOCK)
    ON TrnPostingType = e1.JrnStpEnumValue
   AND e1.JrnStpEnumType = 50
  LEFT JOIN FoundationStatuteMenu substatu(NOLOCK)
    ON lopStatu.LastSubStatuId = substatu.DefinitionId
  LEFT JOIN ContractProject cp(NOLOCK)
    ON TrnOprProjectId = cp.ContractProjectId
 WHERE TrnPostingType NOT IN (111, 112, 113, 114, 115, 126)
   AND TrnDummy = 0
   AND (CASE
         WHEN TrnIsDeleted = 4 AND lopStatu.RiskIncludingTypeId = 7 AND
              (SELECT lll.RiskIncludingTypeId
                 FROM LeasingOperationProject lll(NOLOCK)
                WHERE lll.OperationProjectId = lopStatu.OperationProjectId) = 6 THEN
          3
         WHEN TrnIsDeleted = 4 AND lopStatu.RiskIncludingTypeId = 6 AND
              (SELECT TOP 1 lll.RiskIncludingTypeId
                 FROM LOPRevisionJoinListOutPlan lll(NOLOCK)
                WHERE (lll.OperationProjectId = TrnOprRevisionLOPId AND
                      TrnOprRevisionLOPId <> 0)
                   OR (lll.OperationProjectId = TrnOprLeasingOperationPrjId AND
                      TrnOprRevisionLOPId = 0)) = 7 THEN
          3
         ELSE
          TrnIsDeleted
       END NOT IN (6, 4, 2, 8, 1) OR (TrnIsDeleted = 6 AND TrnAmount <> 0))
   AND (TrnAmount <> 0 OR TrnAmountLocal <> 0 OR TrnAmountCompany <> 0)
   AND TrnLayer = 1
   AND TrnLedgerStatu = 50
   AND NOT
        (TrnIsDeleted = 2 AND TrnPostingType > 120 AND TrnPostingType < 110)
   AND TrnPostingType <> 461
   AND TrnPostingGroupId = 1
   AND TrnAccountType = 11
 GROUP BY TrnOprLeasingOperationPrjId
