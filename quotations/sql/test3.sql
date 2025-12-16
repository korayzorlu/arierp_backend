SELECT TOP 1000
    quo.RPR_QUO_ID,
    quoItem.QUO_ITEM_ID,
    quo.QUO_HEADER_ID,
    crmInst.CustomerName AS CUSTOMER_NAME,
    custType.PARAMETER_TEXT AS CUSTOMER_TYPE_ID,
    project.PROJECT_NAME,
    block.BLOCK_NO,
    freePart.FREE_PART_NO,
    quoItem.GROSS_SALE_AMOUNT,
    grossCurr.CurrencyCode AS GROSS_SALE_AMOUNT_CURR_ID,
    quoItem.CUSTOMER_SIGN_DATE,
    quoItem.CONTRACT_DELIVERY_DATE,
    quoItem.FREE_PART_DELIVERY_DATE,
    quoItem.PLANNED_DELIVERY_DATE,
    subStat.DefinitionName AS LAST_SUB_STATU_NAME,
    subStat.DefinitionId AS LAST_SUB_STATU_ID,
    CASE qpp.IS_CPI_CONTRACT
        WHEN '1' THEN 'Evet'
        ELSE 'Hayır'
    END AS IsCpiContract,
    qpp.AVERAGE_RETURN_PERIOD,
    freePart.TIMESHARE_PERIOD,
    freePart.START_DATE,
    freePart.FINISH_DATE,
    (
        SELECT TOP 1 ContractHeaderCode
        FROM ContractHeader (NOLOCK)
        WHERE QuotationHeaderId = quoItem.QUO_HEADER_ID
          AND ISNULL(IS_DELETED, 0) = 0
          AND StateId = 1
        ORDER BY 1 DESC
    ) AS ContractHeaderCode,
    quo.ContractHeaderCode AS RezervContractHeaderCode,
    quo.IS_FROM_INTEGRATION,
    (
        SELECT TOP 1 TaxName
        FROM GeneralTax (NOLOCK)
        WHERE TaxGroupId = quoItem.TAX_GROUP_ID
    ) AS KDV,
    freePart.BBSN_NO
FROM dbo.RPR_QUO quo
LEFT JOIN dbo.CrmCustomerListCombo crmInst
    ON quo.CRM_CUSTOMER_ID = crmInst.CustomerId
LEFT JOIN dbo.RPR_PARAMETER custType
    ON quo.CUSTOMER_TYPE_ID = custType.PARAMETER_VALUE
    AND custType.PARAMETER_NAME = 'CUSTOMER_TYPE_ID'
LEFT JOIN dbo.RPR_QUO_ITEM quoItem
    ON quo.RPR_QUO_ID = quoItem.RPR_QUO_ID
LEFT JOIN dbo.RPR_PROJECT project
    ON quoItem.PROJECT_ID = project.PROJECT_ID
LEFT JOIN dbo.RPR_PROJECT_BLOCK block
    ON quoItem.BLOCK_ID = block.BLOCK_ID
LEFT JOIN dbo.RPR_PROJECT_FREE_PART freePart
    ON quoItem.FREE_PART_ID = freePart.FREE_PART_ID
LEFT JOIN dbo.RPR_QUO_PAYMENT_PLAN qpp
    ON quo.RPR_QUO_ID = qpp.RPR_QUO_ID
LEFT JOIN dbo.GeneralCurrency grossCurr
    ON quoItem.GROSS_SALE_AMOUNT_CURR_ID = grossCurr.CurrencyId
LEFT JOIN FoundationStatuteMenu subStat
    ON quo.LAST_SUB_STATU_ID = subStat.DefinitionId
WHERE
    quo.IS_DELETED = 0
    AND ISNULL(freePart.IS_DELETED, 0) = 0
--    AND quo.RPR_QUO_ID = 47015
