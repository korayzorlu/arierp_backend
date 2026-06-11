DELETE FROM TRLEAS_TAPU_ISLEM_TAB i WHERE i.daire_id NOT IN(select DAIRE_ID from TRLEAS_DAIRE_TAB) and sigorta_sirketi is null;
  FOR rec_ IN (select *
                 from TRLEAS_DAIRE_TAB i
                where i.DAIRE_ID not in
                      (select DAIRE_ID from TRLEAS_TAPU_ISLEM_TAB)) loop
    INSERT into TRLEAS_TAPU_ISLEM_TAB(daire_id,rowversion,rowstate) values (rec_.daire_id,sysdate,'Yeni');
  END LOOP;
  for rec_ in (select i.daire_id, n.mkk_tescil_no, n.mkk_tescil_tarihi
                 from TRLEAS_NOTER_TAB n, TRLEAS_TAPU_ISLEM2 i
                where i.SOZLESME_NO = n.contract_header_id) loop
    update TRLEAS_TAPU_ISLEM_tab
       set mkk_tescil_no     = rec_.mkk_tescil_no,
           mkk_tescil_tarihi = rec_.mkk_tescil_tarihi
    where  daire_id = rec_.daire_id;
    update trleas_kira_plani_tab
    set mkk_tescil_no = rec_.mkk_tescil_no,
        mkk_tescil_tarihi = rec_.mkk_tescil_tarihi
    WHERE daire_id = rec_.daire_id;
  end loop;

  FOR rec_ IN(SELECT DAIRE_ID, COUNT(1) say FROM TRLEAS_TAPU_ISLEM_TAB GROUP BY DAIRE_ID HAVING COUNT(1)>1)
  LOOP
    DELETE FROM TRLEAS_TAPU_ISLEM_TAB 
      WHERE DAIRE_ID=rec_.DAIRE_ID AND rownum=1;
  END LOOP;
  FOR rec_ IN(SELECT DAIRE_ID, COUNT(1) say FROM TRLEAS_DAIRE_TAB GROUP BY DAIRE_ID HAVING COUNT(1)>1)
  LOOP
    DELETE FROM TRLEAS_DAIRE_TAB 
      WHERE DAIRE_ID=rec_.DAIRE_ID AND rownum=1;
  END LOOP;
/* INSERT INTO ARI_PROJE_YETKI
  SELECT P.PROJECT_NAME,U.USERNAME,(SELECT COUNT(1) FROM ARI_PROJE_YETKI Y WHERE Y.PROJE = 'BURSA MODERN' AND Y.KULLANICI = U.USERNAME AND Y.AKTIF =1) FROM ARIUSERS U,
  (SELECT DISTINCT PROJECT_NAME FROM ARIDAIRELISTESI WHERE PROJECT_NAME NOT IN(SELECT PROJE FROM ARI_PROJE_YETKI)) P;*/
END Tapu_Daire_Yenile