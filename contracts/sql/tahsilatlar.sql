SELECT DISTINCT
    0 AS Trn_Temp_RevenueCheckColumn,
    TrnId,
    TrnFromToType AS TrnFromToType_HIDDEN,
    TrnFromLedgerAccountId AS TrnFromLedgerAccountId_HIDDEN,
    TrnFromTradeAccountCode AS TrnFromTradeAccountCode_HIDDEN,
    TrnFromId = CASE TrnFromToType
        WHEN 10 THEN tatFrom.AccTypUniqueId
        WHEN 20 THEN LedgerAccount.AccountCode
        ELSE ''
    END,
    AccountCode AS TrnFromLedgerAccountId_AC,
    AccountName AS TrnFromLedgerAccountId_AN,
    tatFrom.AccTypUniqueId AS TrnFromTradeAccountCode,
    e1.JrnStpEnumDescription AS viewTrnFromToType,
    e2.JrnStpEnumDescription AS viewTrnPostingType,
    TrnPostingType,
    '' AS Status,
    1 AS StatusId,
    JrnStpPstGrpName AS JrnStpPstGrpName,
    ch.ContractHeaderCode AS TrnOprContractId,
    TrnAccountCode,
    ta.AccName,
    tat.AccTypUniqueId AS OPR_AccTypUniqueId,
    tat.AccName AS OPR_AccName,
    TrnDate,
    TrnDueDate,
    TrnAmountTypeDebit = CASE TrnAmountType WHEN 1 THEN TrnAmount ELSE 0 END,
    TrnAmountTypeCredit = CASE TrnAmountType WHEN 0 THEN TrnAmount ELSE 0 END,
    TrnCurrencyCode,
    TrnAmountTypeLocalDebit = CASE TrnAmountType WHEN 1 THEN TrnAmountLocal ELSE 0 END,
    TrnAmountTypeLocalCredit = CASE TrnAmountType WHEN 0 THEN TrnAmountLocal ELSE 0 END,
    TrnExchangeRateLocal,
    TrnLegalExchangeRateLocal_TEMP = CASE
        WHEN TrnLegalExchangeRateLocal = TrnExchangeRateLocal THEN ''
        ELSE 'X'
    END,
    TrnDescription,
    TrnIsPlanned + TrnReturnValueId AS TrnIsPlanned,
    TrnIsPlanned_INFO = CASE TrnSourceType
        WHEN 3 THEN 'Banka Otomasyonu'
        WHEN 31 THEN 'ATS Banka Oto.'
        WHEN 32 THEN 'BTS Banka Oto.'
        WHEN 33 THEN 'ZİNCİRLİKUYU Banka Oto.'
        WHEN 2 THEN 'Aktarım Datası'
        WHEN 80 THEN 'Otomatik Tahsilat'
        WHEN 60 THEN 'EFT'
        WHEN 90 THEN 'Satıcı Avansı Tahsilatı'
        ELSE CASE TrnIsPlanned
            WHEN 1 THEN 'Planlanmış'
            ELSE CASE TrnReturnValueId
                WHEN 0 THEN 'Elle Girilmiş'
                ELSE 'Modülden Gelmiş'
            END
        END
    END,
    userx.NameSurname AS CreatedUserId,
    TrnReturnDocumentNo,
    TrnCommittedRefId
FROM TradeTransaction (NOLOCK)
LEFT JOIN FoundationUserList userx (NOLOCK)
    ON (
        CASE TrnCommittedRefId
            WHEN 0 THEN TrnUserId
            ELSE (
                SELECT subTT.TrnUserId
                FROM TradeTransaction subTT (NOLOCK)
                WHERE subTT.TrnId = TradeTransaction.TrnCommittedRefId
            )
        END
    ) = userx.UserId
LEFT JOIN JournalSetupEnums e1 (NOLOCK)
    ON TrnFromToType = e1.JrnStpEnumValue AND e1.JrnStpEnumType = 80
LEFT JOIN JournalSetupEnums e2 (NOLOCK)
    ON TrnPostingType = e2.JrnStpEnumValue AND e2.JrnStpEnumType = 50
LEFT JOIN LedgerAccount (NOLOCK)
    ON TrnFromLedgerAccountId = LedgerAccount.AccountId
LEFT JOIN ContractHeader ch (NOLOCK)
    ON TrnOprContractId = ch.ContractHeaderId
LEFT JOIN TradeAccount ta (NOLOCK)
    ON TrnAccountId = ta.AccId
LEFT JOIN JournalSetupPostingTypeGroups (NOLOCK)
    ON TrnPostingGroupId = JournalSetupPostingTypeGroups.JrnStpPstGrpId
LEFT JOIN TradeAccountAndTypeComboList tat (NOLOCK)
    ON TrnOprCustomerId = tat.AccCrmId AND tat.AccTypType = 11
LEFT JOIN TradeAccountTypes tatFrom (NOLOCK)
    ON TrnFromTradeAccountCode = tatFrom.AccTypUniqueId
    AND tatFrom.AccTypType = 31
    AND TrnFromToType = 10
WHERE
    TrnDummy = 0
    AND (
        TrnIsDeleted NOT IN (6, 4, 2, 8, 1)
        OR (TrnIsDeleted = 6 AND TrnAmount <> 0)
    )
    AND TrnAccountType IN (21, 11, 1)
    --AND TrnDate >= CONVERT(DATETIME, '2015-7-4', 102)
    --AND TrnDate <= CONVERT(DATETIME, '2025-7-28', 102)
    --AND TrnOprContractId = 57985
    AND TrnLayer = 1
    AND TrnLedgerStatu = 50
    AND ISNULL(TrnFromToType, 0) <> 0
    AND TrnTemplateType <> 0
    AND TrnAmountType = 0
    AND TrnPostingType IN (221, 211, 101, 102, 103, 931, 482)
ORDER BY
    TrnDueDate,
    AccountName;