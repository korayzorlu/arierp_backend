SELECT DISTINCT
       cpp.company_id                                               company_id,
       c.name                                                       company_name,
       cpp.emp_no                                                   emp_no,
       Employee_Status_Details_API.Get_Status(company_id,emp_no,SYSDATE) employee_status,
       Person_Gender_API.Decode(p.sex) gender,
       Pers_Api.Get_Sex(p.person_id) sex,
       cpp.internal_display_name                                    internal_display_name,
       p.fname                                                      fname,
       p.lname                                                      lname,
       p.name8                                                      title,
       p.person_id                                                  person_id,
       work_location_API.Get_Description(cpp.company_office) company_office,
       company_person_api.get_work_email(cpp.company_id, cpp.emp_no) def_E_Mail,
       company_person_api.get_work_phone(cpp.company_id, cpp.emp_no) def_Phone,
       company_person_api.get_work_mobile(cpp.company_id, cpp.emp_no) def_Mobile,
       company_person_api.get_work_fax(cpp.company_id, cpp.emp_no) def_Fax,
       decode(Emp_Employed_Time_API.Is_Employed(c.company, cpp.emp_no, SYSDATE),'1','TRUE','0','FALSE')   is_employed,
       cpp.fname                                                    message
FROM   company_person_pub     cpp,
       pers_tab               p,
       company_tab            c
WHERE  cpp.person_id  = p.person_id
AND    cpp.company_id = c.company
AND    Employee_Status_Details_API.Get_Emp_Status_Seq(company_id,emp_no,SYSDATE) = 1
