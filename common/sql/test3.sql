DECLARE @UserName  varchar(50) = 'tolga.dumantepe';
DECLARE @StartDate datetime    = '2026-08-01';
DECLARE @EndDate   datetime    = '2026-09-08';

SELECT COUNT(*)
FROM
    UTOPIA_LOG.dbo.FoundationFailedUser
WHERE
    UserName = @UserName
    AND Date >= @StartDate
    AND Date <  DATEADD(DAY, 1, @EndDate)
