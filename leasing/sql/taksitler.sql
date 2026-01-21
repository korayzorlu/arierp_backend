SELECT OperationPaymentId,
    OperationProjectId,
    SequenceNo,
    PaymentDate,
    VATRate,
    VATAmount,
    Interest,
    Payment,
    TotalPaymentAmount,
    PrincipalDisplay,
    Balance,
    InterestDisplay,
    PaymentTypeId
FROM LopPaymentList
-- WHERE OperationProjectId = '67721'
ORDER BY
    OperationPaymentId DESC
