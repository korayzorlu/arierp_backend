SELECT con.partner_id,
    max(CURRENT_DATE - ins.payment_date) AS max_overdue_days
   FROM leasing_installment ins
     JOIN leasing_lease l ON ins.lease_id = l.id
     JOIN contracts_contract con ON l.contract_id = con.id
  WHERE ins.overdue_amount > 0::numeric AND (l.lease_status::text = ANY (ARRAY['aktiflestirildi'::character varying, 'planlandi'::character varying, 'durduruldu'::character varying]::text[]))
  GROUP BY con.partner_id;