SELECT object_name, object_type 
FROM all_objects 
WHERE object_type IN ('TABLE', 'VIEW')
  AND owner = 'IFSAPP'
ORDER BY object_type, object_name;