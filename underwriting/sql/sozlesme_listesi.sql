SELECT lop.QuotationHeaderId,
       lop1.QuotationProjectId,
       lop1.QuotationPaymentPlanId,
       lop1.OperationProjectId,
       lop1.SourceLOPId SourceLopId,
       0 SourceLopId2,
       lop.CreditHeaderId,
       lop.ContractHeaderId,
       lop1.ContractProjectId,
       lop.RiskIncludingTypeId,
       lop.OperationProjectCode KIRA_PLANI_KODU,
       lop.QuotationUserName SORUMLU_CALISAN,
       lop.CustomerID MUSTERI_ID,
       lop.TaxAndTCIdentity KIMLIK_NO,
       lop.CustomerName MUSTERI_ADI,
       (SELECT TOP 1 StockName
          FROM dbo.QuotationLine ql
          LEFT JOIN dbo.InventoryStockCode stk
            ON ql.StockCodeId = stk.StockCodeId
         WHERE ProjectId = lop1.QuotationProjectId
           AND ISNULL(Deleted, 0) = 0
           AND ql.ItemTreeId <> 14
         ORDER BY UnitPrice DESC) PROJE,
       lop.currencycode PARA_BIRIMI,
       lop.Activationdate AKTIFLESTIRME_TARIHI,
       (SELECT TOP 1 ApprovedDate
          FROM ContractNotaryPublicEntry
         WHERE contractheaderId = lop.contractHeaderId
           AND NotaryOwnerTypeId = 1) SOZLESME_TARIHI,
       (SELECT MAX(b.StatuteDate)
          FROM FoundationStatuteList b
         WHERE TableName = 'ContractHeader'
           AND lop.ContractHeaderId = b.RecordId) FESIH_IPTAL_TARIHI,
       lop.RiskIncludingTypeName ANA_STATU,
       lop.SubStatuteName ALT_STATU,
       lop1.OperationBaseCost,
       lop1.TotalInterest,
       lop1.ProductAmount AS ANAPARA,
       (SELECT ISNULL(SUM(ISNULL(TotalPrice, 0) + ISNULL(VatAmount, 0)), 0)
          FROM dbo.QuotationLine
         WHERE ProjectId = lop1.QuotationProjectId
           AND ISNULL(Deleted, 0) = 0
           AND ItemTreeId = 14
           AND StockCodeId = 1071) ARI_KOMISYON,
       lop1.AdvancePaymentAmount AS PESINAT,
       lop1.VatRate KDV_ORANI,
       ISNULL(ap.AmountCurrency, 0) AS ALACAK_TOPLAM,
       (SELECT TOP 1 tig.ItemGroupName
          FROM dbo.QuotationLine ql
          LEFT JOIN TradeItemGroup tig
            ON tig.ItemGroupId = ql.ItemGroupId
         WHERE ISNULL(Deleted, 0) = 0
           AND ql.ItemTreeId <> 14
           AND ql.ProjectId = lop1.QuotationProjectId) TIP_GRUBU,
       (SELECT TOP 1 cr.Customername
          FROM dbo.QuotationLine ql
          LEFT JOIN dbo.InventoryStockCode stk ON ql.StockCodeId = stk.StockCodeId
          LEFT JOIN CrmCustomerWithTypes cr ON cr.customerId = ql.vendorId
         WHERE ProjectId = lop1.QuotationProjectId
           AND ISNULL(Deleted, 0) = 0
           AND ql.ItemTreeId <> 14
         ORDER BY UnitPrice DESC) SATICI_ADI,
       ISNULL((SELECT SUM(CASE WHEN PaymentTypeId = 5 THEN TradeOpenAmount ELSE PaymentAmountKPB END)
                 FROM dbo.LPVendorPaymentList
                WHERE ContractProjectId = (SELECT ContractProjectId FROM dbo.LeasingOperationProject WHERE OperationProjectId = lop1.SourceLopId)
                  AND PaymentTypeId IN (5, 1, 2)
                  AND TransactionLayerId = 1), 0) SATICI_ODEMELERI,
       (SELECT TOP 1 (CASE WHEN cr.CustomerCode IN ('54577', '54578', '54840', '56988', '59145', '62980') THEN 'KONUT' ELSE 'DİĞER' END) TIP
          FROM dbo.QuotationLine ql
          LEFT JOIN dbo.InventoryStockCode stk ON ql.StockCodeId = stk.StockCodeId
          LEFT JOIN CrmCustomerWithTypes cr ON cr.customerId = ql.vendorId
         WHERE ProjectId = lop1.QuotationProjectId
           AND ISNULL(Deleted, 0) = 0
           AND ql.ItemTreeId <> 14
         ORDER BY UnitPrice DESC) TIPI,
       ISNULL((SELECT TOP 1 ExchangeRateForexBuying AS kur
                 FROM dbo.GeneralCurrencyExchange AS e
                WHERE e.ExchangeTypeCode = 'TCMB'
                  AND e.CurrencyCode = lop.CurrencyCode
                ORDER BY e.StartingDate DESC), 1) AS DOVIZ_KURU,
       lop1.VatRate,
       ROUND(lop1.AnnualRate, 4) YillikOran,
       ROUND(lop1.OperationBaseIRR, 4) OperasyonOran,
       ROUND(lop1.MarketingBaseIRR, 4) PazarlamaOran,
       ISNULL((SELECT LOPId FROM QuotationHeader qh WHERE lop1.QuotationHeaderId = qh.QuotationHeaderId), -1) PREV_LOP_ID,
       lop1.MainLopId,
       lop1.SequenceNo,
       ISNULL((SELECT ProjectHeaderId FROM dbo.LeasePurchaseProjectHeader pph WHERE pph.QuotationProjectId = lop1.QuotationProjectId AND ISNULL(pph.IsDeleted, 0) = 0), ''),
       CASE WHEN lop.Corporates = 'Evet' THEN 1 ELSE 0 END Musterek_mi
  FROM dbo.LeasingOperationProjectList lop
  LEFT JOIN dbo.LeasingOperationProject lop1
    ON lop.OperationProjectId = lop1.OperationProjectId
  LEFT JOIN dbo.QuotationPaymentPlan pl
    ON lop1.QuotationProjectId = pl.ProjectId
   AND OriginAlternative = 1
  LEFT JOIN (SELECT dimension8 AS ContractHeaderId,
                    SUM(lt.AmountCurrency) AmountCurrency
               FROM ledgertransaction lt
              WHERE Isreverse + Isreverted = 0
                AND IsAccrual >= 0
                AND (accountcode LIKE '392.99.1%' OR accountcode LIKE '393.99.1%')
              GROUP BY dimension8) ap
    ON ap.ContractHeaderId = lop.ContractHeaderId
 WHERE lop.RiskIncludingTypeId IN (1, 3, 4, 5, 6, 7, 8, 9)
