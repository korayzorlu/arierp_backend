SELECT TOP 1000 MainLopId,TransferPeriodTypeId,IsRevision,IS_LAST_PROJECT,Incite,ProjectLeasingTypeId,LeasingTypeId,*

FROM
    LeasingOperationProject
WHERE
    MainLopId = '50116'
ORDER BY
    OperationProjectId DESC