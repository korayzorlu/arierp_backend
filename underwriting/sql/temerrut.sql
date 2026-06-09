SELECT a.ContractHeaderId,
       a.Tarih,
       SUM(fatura_tutar) fatura_tutar,
       SUM(odeme_tutar) odeme_tutar,
       SUM(odenenTemerrut) odenen_temerrut,
       SUM(odeme_kaydi) odeme_kaydi,
       SUM(PROTOKOL)
  FROM (
    SELECT k.ContractHeaderId,
           lt.DueDate Tarih,
           'Ödeme' grup,
           0 fatura_tutar,
           0 odeme_tutar,
           0 odeme_kaydi,
           SUM(lt.AmountLocal) OdenenTemerrut,
           0 PROTOKOL
      FROM LeasingOperationProjectList k
      LEFT JOIN LedgerTransaction lt
        ON lt.Dimension8 = k.ContractHeaderId
     WHERE postingType = 5052
       AND TradeAccountType = 11
       AND IsReverse + IsReverted = 0
       AND k.RiskIncludingTypeName NOT IN ('İptal Edildi', 'Feshedildi')
     GROUP BY k.ContractHeaderId, lt.DueDate
    HAVING SUM(lt.AmountLocal) > 0

    UNION ALL

    SELECT ISNULL(lopStatu.ContractHeaderId, TrnOprContractId),
           TrnDueDate,
           JrnStpPstGrpName grup,
           CASE WHEN TrnAmountType = 1 THEN TrnAmount ELSE 0 END fatura_tutar,
           CASE WHEN TrnAmountType = 0 THEN -1 * TrnAmount ELSE 0 END odeme_tutar,
           CASE WHEN TrnPostingType NOT IN (111, 112, 113, 114, 115, 126)
                THEN (CASE WHEN TrnAmountType = 1 THEN 1 ELSE -1 END) * TrnAmount
                ELSE 0
           END odeme_kaydi,
           0 OdenenTemerrut,
           (CASE WHEN TrnPostingType IN (420, 411) AND ISNULL(TrnReturnDocumentNo, '1') LIKE 'P/%'
                 THEN (CASE WHEN TrnAmountType = 0 THEN -1 ELSE 1 END) * TrnAmount
                 ELSE 0
           END) PROTOKOL
      FROM TradeTransaction (NOLOCK) lt
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
       --AND (lopMain.RiskIncludingTypeId != 6 OR JrnStpPstGrpName LIKE 'K%ra%')
       AND NOT (TrnIsDeleted = 2 AND TrnPostingType > 120 AND TrnPostingType < 110)
       AND TrnPostingType <> 461
       AND (lopStatu.LastSubStatuId IN (405, 415, 402, 2028, 2041, 408, 806, 412, 503,
                                        1026, 1014, 2032, 406, 2031, 1009, 414, 1010,
                                        410, 401, 403, 1007, 1019, 805, 1041, 2029, 400, 404, 2072)
            OR TrnOprLeasingOperationPrjId = 0)
       AND TrnPostingGroupId IN (1, 2, 3, 4, 6, 7, 8, 9, 10, 11, 12, 13,
                                  14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26)
       AND TrnAccountType = 11
  ) a
 WHERE a.Grup IN ('Kira', 'Ödeme')
 GROUP BY a.ContractHeaderId, a.Tarih
 ORDER BY odenen_temerrut DESC, a.Tarih ASC
