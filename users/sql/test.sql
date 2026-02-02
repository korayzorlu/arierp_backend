
SELECT 
    *
FROM 
    dbo.FoundationUsers AS fu
    LEFT OUTER JOIN dbo.OCLocationTitlesList AS oct 
        ON fu.OSPersonId = oct.EmployeeId;