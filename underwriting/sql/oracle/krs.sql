SELECT tari
       saat,
       aciklama,
       aybasi,
       rowid                         objid,
       ltrim(lpad(to_char(rowversion,'YYYYMMDDHH24MISS'),2000))                    objversion,
       rowkey                        objkey
FROM   trleas_krs_tab
