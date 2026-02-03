SELECT TrnId,
        TrnOprLeasingOperationPrjId,
        CustomerId,
        InvoiceDate,
        InvoiceNumber,
        InvoiceAmount
FROM
    TradeTransactionAllInvoices (NOLOCK)
WHERE
    TrnOprLeasingOperationPrjId = '98395'