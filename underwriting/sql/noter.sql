SELECT ContractHeaderId,
       MAX(ApprovedDate),
       MAX(NotaryOwnerTypeId),
       MAX(StampNo),
       MAX(SIGNATURE_DATE),
       MAX(DailyWagesNo)
  FROM ContractNotaryPublicEntry
 WHERE ContractHeaderId IS NOT NULL
 GROUP BY ContractHeaderId
