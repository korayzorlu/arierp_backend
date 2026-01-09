SELECT OperationPaymentId,
    OperationProjectId,
    SequenceNo,
    PaymentDate,
    VATRate,
    VATAmount,
    Payment,
    TotalPaymentAmount,
    PrincipalDisplay,
    Balance,
    InterestDisplay,
    PaymentTypeId,
    OperationPaymentId
FROM LopPaymentList
ORDER BY
    OperationPaymentId DESC
--WHERE OperationProjectId = '22590'