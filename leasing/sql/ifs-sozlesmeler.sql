SELECT a.sozlesme_no,
       a.ari_sozlesme_no,
       a.musteri_adi,
       a.tc_vergi_no,
       a.araci_kurum alt_musteri,
       a.araci_kurum_tc_vergi_no alt_musteri_tc_vergi_no,
       a.proje_id,
       ifsapp.project_api.Get_Description(proje_id) proje_adi,
       a.stok_no,
       a.sozlesme_tarihi,
       a.birim_fiyat,
       a.kdv_orani,
       a.nakit_tahsilat,
       a.senetli_tahsilat,
       a.objstate durum,
       nvl(a.company, ifsapp.project_api.Get_Company(proje_id)) sirket_kodu,
       ifsapp.company_api.get_name(nvl(a.company,
                                       ifsapp.project_api.Get_Company(proje_id))) sirket_unvani,
       a.fatura_tarihi,
       a.fatura_no,
       a.fatura_tutari,
       a.fatura_kdv_tutari,
       a.teslim_durumu,
       a.teslim_tarihi
FROM ifsapp.sincrm_sozlesme a

-- WHERE a.stok_no = 'BBSN.119982'
     --AND a.araci_kurum_tc_vergi_no = '30964162810'
--WHERE a.stok_no ='DTSN.A01336'
--a.objstate = 'Sozlesmeli'
     --AND a.araci_kurum_tc_vergi_no = '30964162810'
