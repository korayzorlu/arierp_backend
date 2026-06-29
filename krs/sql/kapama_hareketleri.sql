-- ============================================================================
-- krs / kapama_hareketleri.sql
--
-- Kaynak: LeasFlexToOracle.exe -> Program.cs -> Transfer() -> TEMERRUT_OLUSTUR
--         bloğu (aktif olan, yorum satırı OLMAYAN sorgu; dosyada bir de eski/
--         kullanılmayan bir versiyonu yorum satırı olarak duruyor, o alınmadı).
--
-- Ne döner: Her sözleşme (ContractHeaderId) + tarih (Tarih) kombinasyonu için
-- o gün için toplam fatura tutarı, ödeme tutarı, ödenmiş temerrüt (gecikme
-- faizi/ceza olarak zaten tahsil edilmiş tutar) ve "gerçek ödeme" (odeme_kaydi)
-- tutarlarını döner. Bu satırlar, krs/services/kapama.py içindeki FIFO
-- eşleştirme algoritmasının girdisidir.
--
-- ÖNEMLİ: Orijinal C# kodunda bu sorgunun sonunda ORDER BY yoktu (sonuçlar
-- C# tarafında sıraya bakılmaksızın işleniyordu, çünkü .NET tarafı sadece
-- ham INSERT yapıyordu, FIFO eşleştirmesini PL/SQL ayrı bir adımda yapıyordu).
-- Burada ORDER BY ContractHeaderId, Tarih EKLENDİ çünkü Python tarafında
-- itertools.groupby ile sözleşme bazlı gruplama bu sıralamaya güveniyor.
-- Bu eklenti sonuçları DEĞİŞTİRMEZ, sadece organize eder.
-- ============================================================================

SELECT
    a.ContractHeaderId,
    a.Tarih,
    SUM(a.fatura_tutar)  AS fatura_tutar,
    SUM(a.odeme_tutar)   AS odeme_tutar,
    SUM(a.odenenTemerrut) AS odenen_temerrut,
    SUM(a.odeme_kaydi)   AS odeme_kaydi,
    SUM(a.PROTOKOL)      AS protokol
FROM (
    -- ---- Parça 1: Ledger'a düşmüş, zaten tahsil edilmiş gecikme/temerrüt faizi ----
    SELECT
        k.ContractHeaderId,
        lt.DueDate AS Tarih,
        'Ödeme' AS grup,
        0 AS fatura_tutar,
        0 AS odeme_tutar,
        0 AS odeme_kaydi,
        SUM(lt.AmountLocal) AS odenenTemerrut,
        0 AS PROTOKOL
    FROM LeasingOperationProjectList k
    LEFT JOIN LedgerTransaction lt
        ON lt.Dimension8 = k.ContractHeaderId
    WHERE lt.postingType = 5052
      AND lt.TradeAccountType = 11
      AND (lt.IsReverse + lt.IsReverted) = 0
      AND k.RiskIncludingTypeName NOT IN ('İptal Edildi', 'Feshedildi','planlandi')
    GROUP BY k.ContractHeaderId, lt.DueDate
    HAVING SUM(lt.AmountLocal) > 0

    UNION ALL

    -- ---- Parça 2: Asıl kira/ödeme cari hareketleri ----
    SELECT
        ISNULL(lopStatu.ContractHeaderId, lt.TrnOprContractId) AS ContractHeaderId,
        lt.TrnDueDate AS Tarih,
        JournalSetupPostingTypeGroups.JrnStpPstGrpName AS grup,
        CASE WHEN lt.TrnAmountType = 1 THEN lt.TrnAmount ELSE 0 END AS fatura_tutar,
        CASE WHEN lt.TrnAmountType = 0 THEN -1 * lt.TrnAmount ELSE 0 END AS odeme_tutar,
        CASE
            WHEN lt.TrnPostingType NOT IN (111, 112, 113, 114, 115, 126)
            THEN (CASE WHEN lt.TrnAmountType = 1 THEN 1 ELSE -1 END) * lt.TrnAmount
            ELSE 0
        END AS odeme_kaydi,
        0 AS odenenTemerrut,
        (
            CASE
                WHEN lt.TrnPostingType IN (420, 411)
                     AND ISNULL(lt.TrnReturnDocumentNo, '1') LIKE 'P/%'
                THEN (CASE WHEN lt.TrnAmountType = 0 THEN -1 ELSE 1 END) * lt.TrnAmount
                ELSE 0
            END
        ) AS PROTOKOL
    FROM TradeTransaction lt WITH (NOLOCK)
    LEFT JOIN LeasingOperationProject lop WITH (NOLOCK)
        ON lt.TrnOprLeasingOperationPrjId = lop.OperationProjectId
    LEFT JOIN LeasingOperationProject lopMain WITH (NOLOCK)
        ON lop.SourceLopId = lopMain.OperationProjectId
    LEFT JOIN AriRevisionJoinMainList lopStatu WITH (NOLOCK)
        ON lt.TrnOprLeasingOperationPrjId = (
            CASE
                WHEN lopMain.IsRevision = 1 AND lopMain.OperationTypeId = 1 AND lopMain.OperationProjectCode LIKE '%0'
                    THEN lopStatu.SourceLOPId
                WHEN lopMain.IsRevision = 1 AND lopMain.OperationTypeId = 1 AND lopMain.IsLOPRevision = 2
                    THEN lopStatu.OperationProjectId
                ELSE lopStatu.SourceLOPId
            END
        )
        AND lt.TrnOprCustomerId = lopStatu.CustomerId
    LEFT JOIN TradeAccount WITH (NOLOCK)
        ON lt.TrnAccountId = TradeAccount.AccId
    LEFT JOIN CrmCustomerWithTypesLightTradeRisk WITH (NOLOCK)
        ON TradeAccount.AccCrmId = CrmCustomerWithTypesLightTradeRisk.CustomerId
    LEFT JOIN JournalSetupPostingTypeGroups WITH (NOLOCK)
        ON lt.TrnPostingGroupId = JournalSetupPostingTypeGroups.JrnStpPstGrpId
    LEFT JOIN JournalSetupEnums e1 WITH (NOLOCK)
        ON lt.TrnPostingType = e1.JrnStpEnumValue
        AND e1.JrnStpEnumType = 50
    LEFT JOIN FoundationStatuteMenu substatu WITH (NOLOCK)
        ON lopStatu.LastSubStatuId = substatu.DefinitionId
    LEFT JOIN ContractProject cp WITH (NOLOCK)
        ON lt.TrnOprProjectId = cp.ContractProjectId
    LEFT JOIN QuotationProject qp WITH (NOLOCK)
        ON cp.QuotationProjectId = qp.ProjectId
    LEFT JOIN RPR_PROJECT_VGKA_REPORT_DATA rprData WITH (NOLOCK)
        ON lt.TrnOprLeasingOperationPrjId = rprData.OPERATION_PROJECT_ID
    WHERE lt.TrnDummy = 0
      AND (
            (
                CASE
                    WHEN lt.TrnIsDeleted = 4 AND lopStatu.RiskIncludingTypeId = 7
                         AND (SELECT lll.RiskIncludingTypeId FROM LeasingOperationProject lll WITH (NOLOCK)
                              WHERE lll.OperationProjectId = lopStatu.OperationProjectId) = 6
                        THEN 3
                    WHEN lt.TrnIsDeleted = 4 AND lopStatu.RiskIncludingTypeId = 6
                         AND (SELECT TOP 1 lll.RiskIncludingTypeId FROM LOPRevisionJoinListOutPlan lll WITH (NOLOCK)
                              WHERE (lll.OperationProjectId = lt.TrnOprRevisionLOPId AND lt.TrnOprRevisionLOPId <> 0)
                                 OR (lll.OperationProjectId = lt.TrnOprLeasingOperationPrjId AND lt.TrnOprRevisionLOPId = 0)) = 7
                        THEN 3
                    ELSE lt.TrnIsDeleted
                END NOT IN (6, 4, 2, 8, 1)
            )
            OR (lt.TrnIsDeleted = 6 AND lt.TrnAmount <> 0)
          )
      AND (lt.TrnAmount <> 0 OR lt.TrnAmountLocal <> 0 OR lt.TrnAmountCompany <> 0)
      AND lt.TrnLayer = 1
      AND lt.TrnLedgerStatu = 50
      AND NOT (lt.TrnIsDeleted = 2 AND lt.TrnPostingType > 120 AND lt.TrnPostingType < 110)
      AND lt.TrnPostingType <> 461
      AND (
            lopStatu.LastSubStatuId IN (
                405, 415, 402, 2028, 2041, 408, 806, 412, 503, 1026, 1014, 2032,
                406, 2031, 1009, 414, 1010, 410, 401, 403, 1007, 1019, 805, 1041,
                2029, 400, 404, 2072
            )
            OR lt.TrnOprLeasingOperationPrjId = 0
          )
      AND lt.TrnPostingGroupId IN (1,2,3,4,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26)
      AND lt.TrnAccountType = 11
) a
WHERE a.grup IN ('Kira', 'Ödeme')
GROUP BY a.ContractHeaderId, a.Tarih
ORDER BY a.ContractHeaderId, a.Tarih;
