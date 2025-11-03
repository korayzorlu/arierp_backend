SELECT
    lop.OperationProjectId AS OPERATIONPROJECTID,
    lop.ContractProjectId AS CONTRACTPROJECTID,
    lop.OperationProjectCode AS OPERATIONPROJECTCODE,
    lop.TransferCode AS TRANSFERCODE,
    cust.CustomerName AS CUSTOMERNAME,
    cust.CustomerCode AS CUSTOMERCODE,
    (
        SELECT ActivationDate
        FROM dbo.LeasingOperationProject AS lop2
        WHERE lop2.OperationProjectId = lop.SourceLOPId
    ) AS ACTIVATIONDATE,
    pay.InvoiceDate AS INVOICEDATE,
    pay.VatRate AS VATRATE,
    lop.CurrencyId AS CURRENCYID,
    curr.CurrencyCode AS CURRENCYCODE,
    pay.TotalPaymentAmount AS TOTALPAYMENTAMOUNT,
    pay.VatAmount AS VATAMOUNT,
    ISNULL(inspol.InsuranceAmount, 0) AS InsuranceAmount,
    pay.TotalPaymentAmount + ISNULL(inspol.InsuranceAmount, 0) AS TotalPaymentAmountWithInsurance,
    pay.PaymentTypeId AS PAYMENTTYPEID,
    pay.Payment AS PAYMENT,
    pay.PrincipalDisplay AS PRINCIPALDISPLAY,
    pay.InterestDisplay AS INTERESTDISPLAY,
    lop.PaymentCount AS PAYMENTCOUNT,
    lop.QuotationUserId AS QUOTATIONUSERID,
    users.Name + users.Surname AS NAMESURNAME,
    lop.CustomerBaseCost AS CUSTOMERBASECOST,
    lop.CustomerId AS CUSTOMERID,
    lop.ContractHeaderId AS CONTRACTHEADERID,
    ch.ContractHeaderCode AS MAINCONTRACTHEADERID,
    pay.PaymentDate AS PAYMENTDATE,
    lop.RiskIncludingTypeId AS RISKINCLUDINGTYPEID,
    riskType.TypeName AS TYPENAME,
    cust.Companygroupid AS COMPANYGROUPID,
    CASE WHEN ISNULL(lop.FloatingId, 0) <> 0 THEN 1 ELSE 2 END AS INTERESTTYPEID,
    CASE WHEN ISNULL(lop.FloatingId, 0) <> 0 THEN 'FLOAT' ELSE 'FIXED' END AS INTERESTTYPENAME,
    lop.OperationBaseIRR,
    lop.LastSubStatuId AS SubStatuteId,
    qptd.TypeName AS LeaseType,
    statMenu.DefinitionName,
    pay.SequenceNo,
    lop.NotaryPublicDate AS NOTARYPUBLICDATE,
    cust.PART_ID,
    (
        SELECT TOP 1 ql.StockCodeId
        FROM dbo.QuotationLine ql
        WHERE ql.QuotationHeaderId = lop.QuotationHeaderId
            AND ISNULL(ql.ItemType, 0) = 0
            AND ISNULL(ql.Deleted, 0) = 0
    ) AS PROJECT_ID,
    (
        SELECT TOP 1 isc.StockName
        FROM InventoryStockCodeListForComboLight isc
        WHERE isc.StockCodeId = (
            SELECT TOP 1 ql.StockCodeId
            FROM dbo.QuotationLine ql
            WHERE ql.QuotationHeaderId = lop.QuotationHeaderId
                AND ISNULL(ql.ItemType, 0) = 0
                AND ISNULL(ql.Deleted, 0) = 0
        )
    ) AS PROJECT_NAME,
    (
        SELECT TOP 1 ql.VendorId
        FROM dbo.QuotationLine ql
        WHERE ql.QuotationHeaderId = lop.QuotationHeaderId
            AND ISNULL(ql.ItemType, 0) = 0
            AND ISNULL(ql.Deleted, 0) = 0
    ) AS VENDOR_ID,
    (
        SELECT TOP 1 ccw.CustomerName
        FROM CrmCustomerWithTypesLight ccw
        WHERE ccw.CustomerId = (
            SELECT TOP 1 ql.VendorId
            FROM dbo.QuotationLine ql
            WHERE ql.QuotationHeaderId = lop.QuotationHeaderId
                AND ISNULL(ql.ItemType, 0) = 0
                AND ISNULL(ql.Deleted, 0) = 0
        )
    ) AS VENDOR_NAME,
    ISNULL(prjBlock.BLOCK_NO, '') AS BLOCK_NO,
    prjFreePart.FREE_PART_NO,
    lop.VendorTypeId AS LopVendorTypeId,
    venType.VendorTypeName,
    pay.IsCpiCalculated,
    pay.IsCpiRent,
    CASE WHEN ISNULL(pay.IsCpiCalculated, 0) = 1 THEN 'E' ELSE 'H' END AS IsCpiCalculated_Text,
    CASE WHEN ISNULL(pay.IsCpiRent, 0) = 1 THEN 'E' ELSE 'H' END AS IsCpiRent_Text
FROM
    dbo.LeasingOperationProject lop
    INNER JOIN TradeLOPListAddPlaningDebit cont (NOLOCK) ON cont.OperationProjectId = lop.SourceLOPId
    LEFT JOIN QuotationProjectVendorType venType (NOLOCK) ON venType.VendorTypeId = lop.VendorTypeId
    LEFT JOIN dbo.ContractHeader ch ON lop.ContractHeaderId = ch.ContractHeaderId
    LEFT OUTER JOIN dbo.LeasingOperationRiskIncludingType riskType ON lop.RiskIncludingTypeId = riskType.TypeId
    LEFT OUTER JOIN dbo.FoundationUsers users ON lop.QuotationUserId = users.UserId
    LEFT OUTER JOIN dbo.GeneralCurrency curr ON lop.CurrencyId = curr.CurrencyId
    LEFT OUTER JOIN dbo.CrmCustomerWithTypesLight cust ON lop.CustomerId = cust.CustomerId
    LEFT OUTER JOIN dbo.LeasingOperationPayment pay ON lop.OperationProjectId = pay.OperationProjectId
    LEFT JOIN QuotationPaymentTypeDefinition qptd ON qptd.TypeId = pay.PaymentTypeId
    LEFT OUTER JOIN FoundationStatuteMenu statMenu ON statMenu.DefinitionId = lop.LastSubStatuId AND statMenu.TableName = 'LeasingOperationProject'
    LEFT OUTER JOIN RPR_QUO_ITEM rpritem ON rpritem.QUO_HEADER_ID = lop.QuotationHeaderId
    LEFT OUTER JOIN dbo.RPR_PROJECT project ON project.PROJECT_ID = rpritem.PROJECT_ID
    LEFT OUTER JOIN dbo.RPR_PROJECT_BLOCK prjBlock ON prjBlock.BLOCK_ID = rpritem.BLOCK_ID
    LEFT OUTER JOIN RPR_PROJECT_FREE_PART prjFreePart ON prjFreePart.FREE_PART_ID = rpritem.FREE_PART_ID
    LEFT OUTER JOIN (
        SELECT
            InsurancePolicy.OperationProjectId,
            InsurancePolicyCollection.DueDate,
            SUM(InsurancePolicyCollection.Amount) AS InsuranceAmount
        FROM
            InsurancePolicy
            INNER JOIN InsurancePolicyCollection ON InsurancePolicyCollection.PolicyId = InsurancePolicy.PolicyId
        WHERE
            ISNULL(InsurancePolicy.IsInvoicedWithLease, 0) = 1
            AND ISNULL(InsurancePolicy.IsDeleted, 0) = 0
        GROUP BY
            InsurancePolicy.OperationProjectId,
            InsurancePolicyCollection.DueDate
    ) inspol ON inspol.OperationProjectId = lop.OperationProjectId AND inspol.DueDate = pay.PaymentDate
WHERE
    pay.TotalPaymentAmount > 0