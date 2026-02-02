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

