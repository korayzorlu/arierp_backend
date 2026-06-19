SELECT TOP 1000
TrnId,
    CrmCustomerWithTypesLightTradeRisk.CustomerId AS CustomerId,
    TrnDescription,
    TrnCurrencyCode,
    TrnPostingGroupId,
    JrnStpPstGrpName AS JrnStpPstGrpName,
    TrnReturnDocumentNo,
    TrnDueDate,
    TrnExchangeRateLocal,
    ISNULL(TrnOprLeasingOperationPrjId, 0) AS TrnOprLeasingOperationPrjId,
    TrnCreateDate,
    TrnAmountType,
    TrnAmount,
    TrnAmountLocal,
    TrnIsDeleted
FROM
    TradeTransaction
    LEFT JOIN LOPRevisionJoinMainList lopStatu (NOLOCK)
        ON TrnOprLeasingOperationPrjId = lopStatu.SourceLopId
        AND TrnOprCustomerId = lopStatu.CustomerId
    LEFT JOIN TradeAccount (NOLOCK)
        ON TrnAccountId = TradeAccount.AccId
    LEFT JOIN CrmCustomerWithTypesLightTradeRisk (NOLOCK)
        ON AccCrmId = CrmCustomerWithTypesLightTradeRisk.CustomerId
    LEFT JOIN JournalSetupPostingTypeGroups (NOLOCK)
        ON TrnPostingGroupId = JournalSetupPostingTypeGroups.JrnStpPstGrpId
    LEFT JOIN ContractProject cp (NOLOCK)
        ON TrnOprProjectId = cp.ContractProjectId
    LEFT JOIN QuotationProject qp (NOLOCK)
        ON cp.QuotationProjectId = qp.ProjectId
WHERE
   TrnOprLeasingOperationPrjId = 97479
    --AND TrnDescription NOT LIKE '% Evalüasyonu (USD)%'
ORDER BY
    TrnCreateDate DESC