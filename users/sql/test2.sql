
SELECT *
FROM 
    dbo.FoundationUsers AS fu
    LEFT OUTER JOIN dbo.FoundationUserRoles AS fur 
        ON fu.UserId = fur.UserId;