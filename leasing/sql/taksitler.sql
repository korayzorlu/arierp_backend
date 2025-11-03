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
    PaymentTypeId
FROM LopPaymentList
--WHERE OperationProjectId = '22590'