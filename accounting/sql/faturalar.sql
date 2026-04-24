SELECT TrnId,
        TrnOprLeasingOperationPrjId,
        CustomerId,
        InvoiceDate,
        InvoiceNumber,
        InvoiceAmount
FROM
    TradeTransactionAllInvoices (NOLOCK)
WHERE
    DetailInformation = 'Kira'
    AND TrnOprLeasingOperationPrjId <> '0'
    --AND TrnOprLeasingOperationPrjId = '99180'
