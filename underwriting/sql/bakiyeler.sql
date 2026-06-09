SELECT TrnOprContractId,
       OperationProjectId,
       Grup,
       SUM(tutar) bakiye
  FROM (
    SELECT TrnOprContractId,
           0 OperationProjectId,
           CASE WHEN JrnStpPstGrpName LIKE 'K%ra%' THEN 'Kira' ELSE JrnStpPstGrpName END grup,
           CASE WHEN TrnAmountType = 1 THEN TrnAmount
                WHEN TrnAmountType = 0 THEN -1 * TrnAmount
                ELSE 0
           END tutar
      FROM TradeTransaction (NOLOCK)
      LEFT JOIN LeasingOperationProject lop (NOLOCK)
        ON TrnOprLeasingOperationPrjId = lop.OperationProjectId
      LEFT JOIN LeasingOperationProject lopMain (NOLOCK)
        ON lop.SourceLopId = lopMain.OperationProjectId
      LEFT JOIN AriRevisionJoinMainList lopStatu (NOLOCK)
        ON TrnOprLeasingOperationPrjId = (CASE
             WHEN lopMain.IsRevision = 1 AND lopMain.OperationTypeId = 1 AND lopMain.OperationProjectCode LIKE '%0' THEN lopStatu.SourceLOPId
             WHEN lopMain.IsRevision = 1 AND lopMain.OperationTypeId = 1 AND lopMain.IsLOPRevision = 2 THEN lopStatu.OperationProjectId
             ELSE lopStatu.SourceLOPId
           END)
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
     WHERE TrnDummy = 0
       AND (CASE
              WHEN TrnIsDeleted = 4 AND lopStatu.RiskIncludingTypeId = 7 AND
                   (SELECT lll.RiskIncludingTypeId
                      FROM LeasingOperationProject lll (NOLOCK)
                     WHERE lll.OperationProjectId = lopStatu.OperationProjectId) = 6 THEN 3
              WHEN TrnIsDeleted = 4 AND lopStatu.RiskIncludingTypeId = 6 AND
                   (SELECT TOP 1 lll.RiskIncludingTypeId
                      FROM LOPRevisionJoinListOutPlan lll (NOLOCK)
                     WHERE (lll.OperationProjectId = TrnOprRevisionLOPId AND TrnOprRevisionLOPId <> 0)
                        OR (lll.OperationProjectId = TrnOprLeasingOperationPrjId AND TrnOprRevisionLOPId = 0)) = 7 THEN 3
              ELSE TrnIsDeleted
            END NOT IN (6, 4, 2, 8, 1) OR (TrnIsDeleted = 6 AND TrnAmount <> 0))
       AND (TrnAmount <> 0 OR TrnAmountLocal <> 0 OR TrnAmountCompany <> 0)
       AND TrnLayer = 1
       AND TrnLedgerStatu = 50
       AND NOT (TrnIsDeleted = 2 AND TrnPostingType > 120 AND TrnPostingType < 110)
       AND TrnPostingType <> 461
       AND (lopStatu.LastSubStatuId IN (405, 415, 402, 2028, 2041, 408, 806, 412, 503,
                                        1026, 1014, 2032, 406, 2031, 1009, 414, 1010,
                                        410, 401, 403, 1007, 1019, 805, 1041, 2029, 400, 404)
            OR TrnOprLeasingOperationPrjId = 0)
       AND TrnAccountType = 11

    UNION ALL

    SELECT ContractHeaderId,
           OperationProjectId,
           'Kira' grup,
           p.TotalPaymentAmount tutar
      FROM LeasingOperationPayment p
     WHERE p.InvoiceNo IS NULL
       AND p.PaymentTypeId != '5'
       AND p.PaymentDate <= GETDATE()
  ) s
 GROUP BY OperationProjectId, TrnOprContractId, grup
