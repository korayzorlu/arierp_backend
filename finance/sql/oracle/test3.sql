SELECT
    -- Sözleşme Temel Bilgileri
    sozlesme_no,
    crm_id,
    proje_id,
    stok_no,
    rezervasyon_tarihi,
    sozlesme_tarihi,
    sozlesme_numara_serisi,
    sozlesme_turu,

    -- Müşteri Bilgileri
    musteri_no,
    musteri_no                               AS customer_id,
    musteri_crm_id,
    sincrm_util_api.maskele(musteri_adi)     AS musteri_adi,
    sincrm_util_api.maskele(tc_vergi_no)     AS tc_vergi_no,
    yabanci_musteri_adi,
    yabanci_musteri,

    -- Sözleşme Detayları
    sozlesme_aciklama,
    kefaletli,
    doviz_cinsi,
    doviz_kuru,
    birim_fiyat,
    ilk_birim_fiyat,
    kdv_orani,
    odeme_sekli,
    pesinat,
    pesine_indirgenmis_bedel,
    bugune_indirgenmis_bedel,
    periyot,
    baslangic_vadesi,
    senet_baslangic_no,
    taksit_sayisi,
    toplam_senet_tutari,
    katki_payli,

    -- Tarihler
    islem_tarihi,
    fesih_tarihi,
    teslim_tarihi,
    tapu_tarihi,
    fatura_tarihi,
    hukuk_devir_tarihi,
    icra_takip_tarihi,
    tahliye_dava_tarihi,

    -- Durum
    iptal_durumu,
    iptal_nedeni,
    teslim_durumu,
    ozel_durum,
    ozel_durum_ayrinti,
    personel_durumu,
    hukuk_pasif,
    decode(rowstate, 'Sozlesmeli', 1, 'Yeni', 0, 0) AS satis,

    -- Hukuk / Temerrüt
    temerrut_tutari,
    temerrut_gun_sayisi,

    -- Satış Temsilcisi
    satis_temsilcisi_guid,
    satis_temsilcisi_ad_soyad,

    -- Kampanya
    kampanya_guid,
    kampanya_adi,
    kampanya_baslangic_tarihi,

    -- Aracı Kurum
    sincrm_util_api.maskele(araci_kurum)                    AS araci_kurum,
    sincrm_util_api.maskele(araci_kurum_tc_vergi_no)        AS araci_kurum_tc_vergi_no,
    araci_kurum_musteri_no,
    araci_kurum_musteri_crm_id,
    araci_kurum_tel_no,
    araci_kurum_email,

    -- Finansal
    cari_bakiye,
    nakit_tahsilat,
    senetli_tahsilat,
    kdv_tahsilat,
    kredi_banka,
    kredi_tutari,
    fatura_tutari,
    fatura_kdv_tutari,
    fatura_no,
    iban_no,
    invoice_id,
    ipotek_bilgisi,
    tufe_orani,
    tufe_baslangic,
    company,

    -- ARI Bilgileri
    ari_sozlesme_no,
    ari_komisyonu,
    ari_anapara,
    ari_vade_farki,

    -- Müşteri Değişikliği
    yeni_musteri_no,
    eski_musteri_no,
    eski_sozlesme_no,
    temlik_musteri_adi,
    temlik_kimlik_no,

    -- More Card
    more_card_no,
    more_card_unvan,

    -- Mutabakat: Sözleşme Satır Kalemleri
    NVL((
        SELECT SUM(birim_fiyat)
        FROM   SINCRM_SOZLESME_SATIR_TAB st
        WHERE  st.sozlesme_no  = s.sozlesme_no
        AND    st.ek_bedel_no  = '12'
    ), 0) AS mut_birim_fiyat,

    NVL((
        SELECT ROUND(SUM(birim_fiyat * st.kdv_orani / 100), 2)
        FROM   SINCRM_SOZLESME_SATIR_TAB st
        WHERE  st.sozlesme_no  = s.sozlesme_no
        AND    st.ek_bedel_no  = '12'
    ), 0) AS mut_birim_fiyat_kdv,

    NVL((
        SELECT SUM(birim_fiyat)
        FROM   SINCRM_SOZLESME_SATIR_TAB st
        WHERE  st.sozlesme_no  = s.sozlesme_no
        AND    st.ek_bedel_no  = '01'
    ), 0) AS mut_tufe_farki,

    NVL((
        SELECT SUM(birim_fiyat)
        FROM   SINCRM_SOZLESME_SATIR_TAB st
        WHERE  st.sozlesme_no  = s.sozlesme_no
        AND    st.ek_bedel_no  = '02'
    ), 0) AS mut_dekorasyon,

    NVL((
        SELECT SUM(ROUND(birim_fiyat * st.kdv_orani / 100, 2))
        FROM   SINCRM_SOZLESME_SATIR_TAB st
        WHERE  st.sozlesme_no  = s.sozlesme_no
        AND    st.ek_bedel_no  = '02'
    ), 0) AS mut_dekorasyon_kdv,

    NVL((
        SELECT SUM(birim_fiyat)
        FROM   SINCRM_SOZLESME_SATIR_TAB st
        WHERE  st.sozlesme_no  = s.sozlesme_no
        AND    st.ek_bedel_no  = '13'
    ), 0) AS mut_vade_farki,

    NVL((
        SELECT ROUND(SUM(birim_fiyat * st.kdv_orani / 100), 2)
        FROM   SINCRM_SOZLESME_SATIR_TAB st
        WHERE  st.sozlesme_no  = s.sozlesme_no
        AND    st.ek_bedel_no  = '13'
    ), 0) AS mut_vade_farki_kdv,

    NVL((
        SELECT SUM(birim_fiyat)
        FROM   SINCRM_SOZLESME_SATIR_TAB st
        WHERE  st.sozlesme_no  = s.sozlesme_no
        AND    st.ek_bedel_no  = '04'
    ), 0) AS mut_kur_farki,

    NVL((
        SELECT SUM(birim_fiyat)
        FROM   SINCRM_SOZLESME_SATIR_TAB st
        WHERE  st.sozlesme_no  = s.sozlesme_no
        AND    st.ek_bedel_no  = '05'
    ), 0) AS mut_damga_pulu,

    -- Mutabakat: KDV Oranlarına Göre
    NVL((
        SELECT SUM(birim_fiyat * st.kdv_orani / 100)
        FROM   SINCRM_SOZLESME_SATIR_TAB st
        WHERE  st.sozlesme_no  = s.sozlesme_no
        AND    st.kdv_orani    = 1
    ), 0) AS mut_yuzde1_kdv,

    NVL((
        SELECT SUM(birim_fiyat * st.kdv_orani / 100)
        FROM   SINCRM_SOZLESME_SATIR_TAB st
        WHERE  st.sozlesme_no  = s.sozlesme_no
        AND    st.kdv_orani    = 8
    ), 0) AS mut_yuzde8_kdv,

    NVL((
        SELECT SUM(birim_fiyat * st.kdv_orani / 100)
        FROM   SINCRM_SOZLESME_SATIR_TAB st
        WHERE  st.sozlesme_no  = s.sozlesme_no
        AND    st.kdv_orani    = 18
    ), 0) AS mut_yuzde18_kdv,

    -- Mutabakat: Diğer Kalemler
    NVL((
        SELECT SUM(birim_fiyat)
        FROM   SINCRM_SOZLESME_SATIR_TAB st
        WHERE  st.sozlesme_no  = s.sozlesme_no
        AND    st.ek_bedel_no  = '06'
    ), 0) AS mut_konut_sigorta_bedeli,

    NVL((
        SELECT SUM(birim_fiyat)
        FROM   SINCRM_SOZLESME_SATIR_TAB st
        WHERE  st.sozlesme_no  = s.sozlesme_no
        AND    st.ek_bedel_no  = '07'
    ), 0) AS mut_eski_donem_aidati,

    NVL((
        SELECT SUM(birim_fiyat)
        FROM   SINCRM_SOZLESME_SATIR_TAB st
        WHERE  st.sozlesme_no  = s.sozlesme_no
        AND    st.ek_bedel_no  = '08'
    ), 0) AS mut_tapu_takip_hizmet_bedeli,

    NVL((
        SELECT SUM(birim_fiyat)
        FROM   SINCRM_SOZLESME_SATIR_TAB st
        WHERE  st.sozlesme_no  = s.sozlesme_no
        AND    st.ek_bedel_no  = '08'
    ), 0) AS mut_doner_sermaye,

    NVL((
        SELECT ROUND(SUM(birim_fiyat * st.kdv_orani / 100), 2)
        FROM   SINCRM_SOZLESME_SATIR_TAB st
        WHERE  st.sozlesme_no  = s.sozlesme_no
        AND    st.ek_bedel_no  = '08'
    ), 0) AS mut_doner_sermaye_kdv,

    NVL((
        SELECT SUM(birim_fiyat)
        FROM   SINCRM_SOZLESME_SATIR_TAB st
        WHERE  st.sozlesme_no  = s.sozlesme_no
        AND    st.ek_bedel_no  = '09'
    ), 0) AS mut_abonmanlik_bedeli,

    NVL((
        SELECT ROUND(SUM(birim_fiyat * st.kdv_orani / 100), 2)
        FROM   SINCRM_SOZLESME_SATIR_TAB st
        WHERE  st.sozlesme_no  = s.sozlesme_no
        AND    st.ek_bedel_no  = '09'
    ), 0) AS mut_abonmanlik_bedeli_kdv,

    NVL((
        SELECT SUM(birim_fiyat)
        FROM   SINCRM_SOZLESME_SATIR_TAB st
        WHERE  st.sozlesme_no  = s.sozlesme_no
        AND    st.ek_bedel_no  = '14'
    ), 0) AS mut_iskan_bedeli,

    NVL((
        SELECT ROUND(SUM(birim_fiyat * st.kdv_orani / 100), 2)
        FROM   SINCRM_SOZLESME_SATIR_TAB st
        WHERE  st.sozlesme_no  = s.sozlesme_no
        AND    st.ek_bedel_no  = '14'
    ), 0) AS mut_iskan_bedeli_kdv,

    NVL((
        SELECT SUM(birim_fiyat)
        FROM   SINCRM_SOZLESME_SATIR_TAB st
        WHERE  st.sozlesme_no  = s.sozlesme_no
        AND    st.ek_bedel_no  = '10'
    ), 0) AS mut_iskonto,

    NVL((
        SELECT ROUND(SUM(birim_fiyat * st.kdv_orani / 100), 2)
        FROM   SINCRM_SOZLESME_SATIR_TAB st
        WHERE  st.sozlesme_no  = s.sozlesme_no
        AND    st.ek_bedel_no  = '10'
    ), 0) AS mut_iskonto_kdv,

    NVL((
        SELECT SUM(birim_fiyat)
        FROM   SINCRM_SOZLESME_SATIR_TAB st
        WHERE  st.sozlesme_no  = s.sozlesme_no
        AND    st.ek_bedel_no  = '03'
    ), 0) AS mut_emlak_vergisi,

    NVL((
        SELECT ROUND(SUM(birim_fiyat * st.kdv_orani / 100), 2)
        FROM   SINCRM_SOZLESME_SATIR_TAB st
        WHERE  st.sozlesme_no  = s.sozlesme_no
        AND    st.ek_bedel_no  = '03'
    ), 0) AS mut_emlak_vergisi_kdv,

    -- IFS Sistem Alanları
    rowid                                                                        AS objid,
    ltrim(lpad(to_char(rowversion, 'YYYYMMDDHH24MISS'), 2000))                  AS objversion,
    rowstate                                                                     AS objstate,
    SINCRM_SOZLESME_API.Finite_State_Events__(rowstate)                         AS objevents,
    SINCRM_SOZLESME_API.Finite_State_Decode__(rowstate)                         AS state,
    rowkey                                                                       AS objkey

FROM   sincrm_sozlesme_tab s
WITH   read only
