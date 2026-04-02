SELECT RiskDocumentId,
    RiskHeaderId,
    CustomerId,
    ContractHeaderId,
    OrgContractHeaderId,
    Debit,
    ProcessStartDate,
    DailyWagesDate,
    ServiceDate,
    OfficialCancellationDate,
    Paid,
    Diff,
    State,
    ApprovalState,
    ResultId,
    PROCESS_SITUATION_ID
FROM RiskDocumentWarningFollowListBaseLPDDOR
WHERE
    (PROCESS_SITUATION_ID is null or ResultId in (0,1,2)) 
    AND 1=1
    --AND CustomerId=29308
    AND ResultId in (0,1,2)
    -- AND ContractHeaderId = '57797'