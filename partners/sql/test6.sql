SELECT
    R.Neutral MenuResource,
    M.*
FROM dbo.FoundationMenu AS M
LEFT JOIN UTOPIA_RESOURCE.dbo.FoundationResourcesMenuTR_TR AS R
    ON CAST(M.MenuId AS VARCHAR(20)) = R.ResourceId
