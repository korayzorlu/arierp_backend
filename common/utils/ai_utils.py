EXAMPLE_DEF = '''
def extract_contract_numbers(description):
    if not isinstance(description, str):
        return []

    text = description.lower() # Tüm metni küçük harfe çevir

    matches = []

    # 1. 'sözleşme no', 'no:', 'söz. no', 'nolu sözleşme' gibi tanımlayıcılarla birlikte geçen numaralar
    #    Nokta ile ayrılmış sayıları da yakalamak için [\d\.-_]+ kullanıldı.
    pattern_named = r"""
        (?:
            sözleşme\s*no[:\s]* | # sözleşme no:
            sözleşme\s*[:\s]* | # sözleşme:
            söz\.?\s*no[:\s]* | # söz. no:
            kontrat\s*no[:\s]* | # kontrat no:
            no[:\s]+                  | # no:
            nolu\s+sözleşme             # nolu sözleşme
        )
        [^\d]*([\d\.-_]+)             # numara (rakam, nokta, tire, alt çizgi içerebilir)
    """
    matches.extend(re.findall(pattern_named, text, re.VERBOSE))

    # 2. Parantez içindeki 5+ haneli (veya nokta/tire/alt çizgi içeren) numaralar
    pattern_parens = r'\(([\d\.-_]{5,}(?:[-_]\d{2,})*)\)'
    matches.extend(re.findall(pattern_parens, text))

    # 3. 'sözleşme' kelimesinden hemen önce veya sonra gelen veya içinde geçen numaralar
    # Bu, '48.152 sözleşme' gibi durumları yakalamak için eklendi.
    pattern_proximity = r'(?:\b(\d[\d\.-_]*)\s*sözleşme\b|\bsözleşme\s*(\d[\d\.-_]*)\b)'
    proximity_matches = re.findall(pattern_proximity, text)
    for m in proximity_matches:
        if m[0]: # eğer ilk grup eşleştiyse
            matches.append(m[0])
        if m[1]: # eğer ikinci grup eşleştiyse
            matches.append(m[1])

    # 4. Açıkta geçen 5-12 haneli numaralar (daha dikkatli bir filtreleme ile)
    # Bu kısmı daha güvenli hale getirmek için, banka hareketlerinde TC, IBAN veya tarih gibi sayıları ayırt etmek gerekebilir.
    # Ancak genel bir 'standalone' numara arayışı için kullanılabilir.
    # Şimdilik bu bölümü çok geniş tutmamak adına, sadece belirli bir uzunluktaki sayıları alalım.
    # Daha fazla false positive önlemek için, bu kısmı, eğer diğer kurallar işe yaramazsa son çare olarak kullanmak daha mantıklı olabilir.
    # Örneğin: YIL/AY/GÜN, veya 11 haneli TC, 26 haneli IBAN desenleri dışındaki sayıları hedefleyebiliriz.
    pattern_standalone = r'\b(\d{5,12})\b' # 5-12 haneli sayılar
    raw_standalone_matches = re.findall(pattern_standalone, text)

    # Bulunan tüm eşleşmeleri bir set'e atarak tekrar edenleri kaldır ve temizle
    unique_matches = set()
    for match in matches:
        # Yakalanan numara genellikle string formatında olacaktır.
        # İstenirse burada daha fazla doğrulama veya temizleme yapılabilir (örneğin baştaki/sondaki tireleri kaldırma)
        unique_matches.add(match.strip('-_. ')) # Boşluk, nokta, tire, alt çizgi gibi karakterleri temizle

    # Standalone eşleşmeleri de kontrol edip ekle
    for m in raw_standalone_matches:
        # TC veya IBAN gibi duran sayıları eleyebiliriz, ancak bu her zaman kesin bir çözüm değildir.
        # Bu kısım uygulamanın iş mantığına göre daha fazla geliştirilebilir.
        if m not in unique_matches and len(m) != 11: # Basit bir TC kimlik numarası elemesi
            unique_matches.add(m)

    return list(unique_matches)
'''
