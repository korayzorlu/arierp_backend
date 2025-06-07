from rest_framework import serializers
from rest_framework.utils import html, model_meta, representation


class CariHesapHareketleriListSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    tarih = serializers.DateTimeField(format="%d.%m.%Y %H:%M:%S")
    belgeTarih = serializers.DateTimeField(format="%d.%m.%Y %H:%M:%S")
    kod = serializers.CharField()
    cari = serializers.CharField()
    evrakTip = serializers.CharField()
    belgeNo = serializers.CharField()
    aciklama = serializers.CharField()
    doviz = serializers.CharField()
    meblag = serializers.FloatField()
    araToplam = serializers.FloatField()
    iskonto = serializers.FloatField()
    vergi = serializers.FloatField()
    kur = serializers.FloatField()

class PersonellerListSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    tarih = serializers.DateTimeField(format="%d.%m.%Y %H:%M:%S")
    isim = serializers.CharField()
    soyisim = serializers.CharField()
    girisTarihi = serializers.DateTimeField(format="%d.%m.%Y %H:%M:%S")
    cikisTarihi = serializers.DateTimeField(format="%d.%m.%Y %H:%M:%S")
    cikisNeden = serializers.CharField()
    doviz = serializers.CharField()
    ucret = serializers.FloatField()
    ikramiye = serializers.CharField()
    meslekKodu = serializers.CharField()

class PersonelTahakkuklariListSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    tarih = serializers.DateTimeField(format="%d.%m.%Y %H:%M:%S")
    personel = serializers.CharField()
    donem = serializers.CharField()
    brutUcret = serializers.FloatField()
    netUcret = serializers.FloatField()

class VpnTaskListSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    status = serializers.CharField()