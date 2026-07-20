SELECT OperationPaymentId,
    OperationProjectId,
    SequenceNo,
    PaymentDate,
    VATRate,
    VATAmount,
    Interest,
    Payment,
    TotalPaymentAmount,
    Principal,
    PrincipalDisplay,
    Balance,
    InterestDisplay,
    PaymentTypeId
FROM LopPaymentList
--WHERE OperationProjectId = '98996'
ORDER BY
    OperationPaymentId DESC
