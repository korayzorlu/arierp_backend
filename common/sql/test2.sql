SELECT TOP 10000 *
FROM UTOPIA_LOG.dbo.FoundationLog
WHERE
LogTypeId in (1,16)
-- MenuExplanation LIKE '%Fail%'
ORDER BY
    OperationTime DESC;