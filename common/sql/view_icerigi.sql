SELECT definition AS FoundationFailedUserList
FROM sys.sql_modules
WHERE object_id = OBJECT_ID('FoundationFailedUserList');