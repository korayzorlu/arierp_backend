CREATE TRIGGER Tr_Limit_SSMS_Tek_Oturum
ON ALL SERVER FOR LOGON
AS
BEGIN
    DECLARE @GirisYapanKullanici NVARCHAR(100) = ORIGINAL_LOGIN();
    DECLARE @ProgramAdi NVARCHAR(256) = PROGRAM_NAME();
    DECLARE @AktifSSMSOturumSayisi INT;

    IF @GirisYapanKullanici IN ('KullaniciAdi1', 'KullaniciAdi2')
    BEGIN
        
        IF @ProgramAdi LIKE 'Microsoft SQL Server Management Studio%'
        BEGIN
            
            SELECT @AktifSSMSOturumSayisi = COUNT(*) 
            FROM sys.dm_exec_sessions 
            WHERE login_name = @GirisYapanKullanici 
              AND is_user_process = 1
              AND program_name LIKE 'Microsoft SQL Server Management Studio%';

            IF @AktifSSMSOturumSayisi > 1
            BEGIN
                ROLLBACK;
            END
        END
    END
END;

DROP TRIGGER Tr_Limit_SSMS_Tek_Oturum ON ALL SERVER;
