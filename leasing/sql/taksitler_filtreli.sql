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
FROM
    LopPaymentList
WHERE
    OperationProjectId = ?
ORDER BY
    OperationPaymentId DESC
