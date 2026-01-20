CREATE procedure [dbo].[LeasePaymentDueDateOver_CollectionAmount]    @DueDate as varchar(10),    @SourceLopIds as varchar(max)    as    begin   declare @sql as varchar(max) =''    set @sql ='   SELECT  lop.SourceLOPId,lop.OperationProjectId,   ISNULL(( SELECT                           ABS(SUM(TrnAmount * ( ( TrnAmountType * 2 ) - 1 ))) totalAmount             FROM      TradeTransaction (NOLOCK)                       LEFT JOIN LOPRevisionJoinMainList lopStatu ( NOLOCK ) ON TrnOprLeasingOperationPrjId = lopStatu.SourceLOPId AND TrnOprCustomerId = lopStatu.CustomerId                       LEFT JOIN JournalSetupEnums e1 ( NOLOCK ) ON TrnPostingType = e1.JrnStpEnumValue AND e1.JrnStpEnumType = 50             WHERE     TrnPostingType NOT IN ( 111, 112, 113, 114, 115, 126, 121 )                       AND NOT ( lopStatu.RiskIncludingTypeId = 8                                 AND TrnPostingType = 121                               )                       AND TrnDummy = 0                       AND ( CASE WHEN TrnIsDeleted = 4                                      AND lopStatu.RiskIncludingTypeId = 7                                       AND ( SELECT    lll.RiskIncludingTypeId                                             FROM      LeasingOperationProject lll ( NOLOCK )                                             WHERE     lll.OperationProjectId = lopStatu.OperationProjectId                                           ) = 6 THEN 3                                  WHEN TrnIsDeleted = 4                                       AND lopStatu.RiskIncludingTypeId = 6                                       AND ( SELECT TOP 1                                                       lll.RiskIncludingTypeId                                             FROM      LOPRevisionJoinListOutPlan lll ( NOLOCK )                                             WHERE     ( lll.OperationProjectId = TrnOprRevisionLOPId                                                         AND TrnOprRevisionLOPId <> 0                                                       )                                                       OR ( lll.OperationProjectId = TrnOprLeasingOperationPrjId                                                            AND TrnOprRevisionLOPId = 0                                                          )                                           ) = 7 THEN 3                                  ELSE TrnIsDeleted                             END NOT IN ( 6, 4, 2, 8, 1 )                             OR ( TrnIsDeleted = 6                                  AND TrnAmount <> 0                                )                           )                       AND ( TrnAmount <> 0                             OR TrnAmountLocal <> 0                             OR TrnAmountCompany <> 0                           )                       AND TrnLayer = 1                       AND TrnLedgerStatu = 50                       AND NOT ( TrnIsDeleted = 2                                 AND TrnPostingType > 120                                 AND TrnPostingType < 110                               )                       AND TrnPostingType not in (461,420)                       AND TrnPostingGroupId = 1                       AND TrnAccountType = 11                       AND TrnDueDate <= ''' + @DueDate + '''                       AND TrnOprLeasingOperationPrjId = lop.SourceLOPId           ), 0)           +ISNULL(( SELECT                         ABS(SUM(TrnAmount * ( ( TrnAmountType * 2 ) - 1 ))) totalAmount               FROM    TradeTransaction (NOLOCK)                       LEFT JOIN LOPRevisionJoinMainList lopStatu ( NOLOCK ) ON TrnOprLeasingOperationPrjId = lopStatu.SourceLOPId                                                                 AND TrnOprCustomerId = lopStatu.CustomerId                       LEFT JOIN JournalSetupEnums e1 ( NOLOCK ) ON TrnPostingType = e1.JrnStpEnumValue AND e1.JrnStpEnumType = 50               WHERE   TrnPostingType NOT IN ( 111, 112, 113, 114, 115, 126, 121 )                       AND TrnDummy = 0                       AND ( CASE WHEN TrnIsDeleted = 4                                       AND lopStatu.RiskIncludingTypeId = 7                                       AND ( SELECT    lll.RiskIncludingTypeId                                             FROM      LeasingOperationProject lll ( NOLOCK )                                             WHERE     lll.OperationProjectId = lopStatu.OperationProjectId                                           ) = 6 THEN 3                                  WHEN TrnIsDeleted = 4                                       AND lopStatu.RiskIncludingTypeId = 6                                       AND ( SELECT TOP 1                                                       lll.RiskIncludingTypeId                                             FROM      LOPRevisionJoinListOutPlan lll ( NOLOCK )                                             WHERE     ( lll.OperationProjectId = TrnOprRevisionLOPId                                                         AND TrnOprRevisionLOPId <> 0                                                       )                                                       OR ( lll.OperationProjectId = TrnOprLeasingOperationPrjId                                                            AND TrnOprRevisionLOPId = 0                                                          )                                           ) = 7 THEN 3                                  ELSE TrnIsDeleted                             END NOT IN ( 6, 4, 2, 8, 1 )                             OR ( TrnIsDeleted = 6                                  AND TrnAmount <> 0                                )                           )                       AND ( TrnAmount <> 0                             OR TrnAmountLocal <> 0                             OR TrnAmountCompany <> 0                           )                       AND TrnLayer = 1                       AND TrnLedgerStatu = 50                       AND NOT ( TrnIsDeleted = 2                                 AND TrnPostingType > 120                                 AND TrnPostingType < 110                               )                       AND TrnPostingType not in (461,420)                       AND TrnPostingGroupId = 1                       AND TrnAccountType = 11                       AND TrnDueDate <= ''' + @DueDate + ''' AND TrnOprLeasingOperationPrjId IN (                       SELECT  SourceLOPId                       FROM    LeasingOperationProject (NOLOCK)                       WHERE   OperationTypeId = 2                               AND OperationProjectId IN (                               SELECT  loprev.PreviousLOPId                               FROM    dbo.LeasingOperationProject loprev ( NOLOCK )                               WHERE   ( ( lop.IsLOPRevision = 2                                           AND loprev.IsLOPRevision = 1                                         )                                         OR loprev.IsLOPRevision = 2                                       )                                       AND loprev.OperationTypeId = 2                                       AND loprev.RiskIncludingTypeId <> 3                                       AND loprev.MainLopId = lop.MainLopId ) )             ),0) totalAmount   FROM    dbo.LeasingOperationProject  lop (nolock)   LEFT JOIN dbo.LeasingOperationProject oldLop (nolock) ON oldlop.OperationProjectId= lop.MainLopId   where    lop.operationprojectId not in (SELECT OperationProjectId FROM dbo.LeasingOperationProject (nolock) WHERE ContractHeaderId IN  ( SELECT ContractHeaderId FROM dbo.LeasingOperationProject (nolock) WHERE RiskIncludingTypeId <> 3  AND OperationTypeId=2) AND OperationTypeId =1) AND lop.RiskIncludingTypeId NOT IN (3,9)  ' if @SourceLopIds<>'' 	set @sql = @sql + ' and lop.SourceLOPId in (' + @SourceLopIds+ ')'      print (@sql)      EXEC (@sql)   end   
-- Kodun okunabilirliği için sadece biçimlendirme yapıldı, mantık değiştirilmedi.

CREATE PROCEDURE [dbo].[LeasePaymentDueDateOver_CollectionAmount]
    @DueDate AS VARCHAR(10),
    @SourceLopIds AS VARCHAR(MAX)
AS
BEGIN
    DECLARE @sql AS VARCHAR(MAX) = ''

    SET @sql = '
    SELECT
        lop.SourceLOPId,
        lop.OperationProjectId,
        ISNULL((
            SELECT ABS(SUM(TrnAmount * ((TrnAmountType * 2) - 1))) totalAmount
            FROM TradeTransaction (NOLOCK)
                LEFT JOIN LOPRevisionJoinMainList lopStatu (NOLOCK)
                    ON TrnOprLeasingOperationPrjId = lopStatu.SourceLOPId
                    AND TrnOprCustomerId = lopStatu.CustomerId
                LEFT JOIN JournalSetupEnums e1 (NOLOCK)
                    ON TrnPostingType = e1.JrnStpEnumValue
                    AND e1.JrnStpEnumType = 50
            WHERE
                TrnPostingType NOT IN (111, 112, 113, 114, 115, 126, 121)
                AND NOT (
                    lopStatu.RiskIncludingTypeId = 8
                    AND TrnPostingType = 121
                )
                AND TrnDummy = 0
                AND (
                    CASE
                        WHEN TrnIsDeleted = 4
                            AND lopStatu.RiskIncludingTypeId = 7
                            AND (
                                SELECT lll.RiskIncludingTypeId
                                FROM LeasingOperationProject lll (NOLOCK)
                                WHERE lll.OperationProjectId = lopStatu.OperationProjectId
                            ) = 6 THEN 3
                        WHEN TrnIsDeleted = 4
                            AND lopStatu.RiskIncludingTypeId = 6
                            AND (
                                SELECT TOP 1 lll.RiskIncludingTypeId
                                FROM LOPRevisionJoinListOutPlan lll (NOLOCK)
                                WHERE (
                                    lll.OperationProjectId = TrnOprRevisionLOPId
                                    AND TrnOprRevisionLOPId <> 0
                                )
                                OR (
                                    lll.OperationProjectId = TrnOprLeasingOperationPrjId
                                    AND TrnOprRevisionLOPId = 0
                                )
                            ) = 7 THEN 3
                        ELSE TrnIsDeleted
                    END NOT IN (6, 4, 2, 8, 1)
                    OR (TrnIsDeleted = 6 AND TrnAmount <> 0)
                )
                AND (
                    TrnAmount <> 0
                    OR TrnAmountLocal <> 0
                    OR TrnAmountCompany <> 0
                )
                AND TrnLayer = 1
                AND TrnLedgerStatu = 50
                AND NOT (
                    TrnIsDeleted = 2
                    AND TrnPostingType > 120
                    AND TrnPostingType < 110
                )
                AND TrnPostingType NOT IN (461, 420)
                AND TrnPostingGroupId = 1
                AND TrnAccountType = 11
                AND TrnDueDate <= ''' + @DueDate + '''
                AND TrnOprLeasingOperationPrjId = lop.SourceLOPId
        ), 0)
        +
        ISNULL((
            SELECT ABS(SUM(TrnAmount * ((TrnAmountType * 2) - 1))) totalAmount
            FROM TradeTransaction (NOLOCK)
                LEFT JOIN LOPRevisionJoinMainList lopStatu (NOLOCK)
                    ON TrnOprLeasingOperationPrjId = lopStatu.SourceLOPId
                    AND TrnOprCustomerId = lopStatu.CustomerId
                LEFT JOIN JournalSetupEnums e1 (NOLOCK)
                    ON TrnPostingType = e1.JrnStpEnumValue
                    AND e1.JrnStpEnumType = 50
            WHERE
                TrnPostingType NOT IN (111, 112, 113, 114, 115, 126, 121)
                AND TrnDummy = 0
                AND (
                    CASE
                        WHEN TrnIsDeleted = 4
                            AND lopStatu.RiskIncludingTypeId = 7
                            AND (
                                SELECT lll.RiskIncludingTypeId
                                FROM LeasingOperationProject lll (NOLOCK)
                                WHERE lll.OperationProjectId = lopStatu.OperationProjectId
                            ) = 6 THEN 3
                        WHEN TrnIsDeleted = 4
                            AND lopStatu.RiskIncludingTypeId = 6
                            AND (
                                SELECT TOP 1 lll.RiskIncludingTypeId
                                FROM LOPRevisionJoinListOutPlan lll (NOLOCK)
                                WHERE (
                                    lll.OperationProjectId = TrnOprRevisionLOPId
                                    AND TrnOprRevisionLOPId <> 0
                                )
                                OR (
                                    lll.OperationProjectId = TrnOprLeasingOperationPrjId
                                    AND TrnOprRevisionLOPId = 0
                                )
                            ) = 7 THEN 3
                        ELSE TrnIsDeleted
                    END NOT IN (6, 4, 2, 8, 1)
                    OR (TrnIsDeleted = 6 AND TrnAmount <> 0)
                )
                AND (
                    TrnAmount <> 0
                    OR TrnAmountLocal <> 0
                    OR TrnAmountCompany <> 0
                )
                AND TrnLayer = 1
                AND TrnLedgerStatu = 50
                AND NOT (
                    TrnIsDeleted = 2
                    AND TrnPostingType > 120
                    AND TrnPostingType < 110
                )
                AND TrnPostingType NOT IN (461, 420)
                AND TrnPostingGroupId = 1
                AND TrnAccountType = 11
                AND TrnDueDate <= ''' + @DueDate + '''
                AND TrnOprLeasingOperationPrjId IN (
                    SELECT SourceLOPId
                    FROM LeasingOperationProject (NOLOCK)
                    WHERE OperationTypeId = 2
                        AND OperationProjectId IN (
                            SELECT loprev.PreviousLOPId
                            FROM dbo.LeasingOperationProject loprev (NOLOCK)
                            WHERE (
                                (
                                    lop.IsLOPRevision = 2
                                    AND loprev.IsLOPRevision = 1
                                )
                                OR loprev.IsLOPRevision = 2
                            )
                            AND loprev.OperationTypeId = 2
                            AND loprev.RiskIncludingTypeId <> 3
                            AND loprev.MainLopId = lop.MainLopId
                        )
                )
        ), 0) totalAmount
    FROM dbo.LeasingOperationProject lop (NOLOCK)
        LEFT JOIN dbo.LeasingOperationProject oldLop (NOLOCK)
            ON oldlop.OperationProjectId = lop.MainLopId
    WHERE
        lop.operationprojectId NOT IN (
            SELECT OperationProjectId
            FROM dbo.LeasingOperationProject (NOLOCK)
            WHERE ContractHeaderId IN (
                SELECT ContractHeaderId
                FROM dbo.LeasingOperationProject (NOLOCK)
                WHERE RiskIncludingTypeId <> 3
                    AND OperationTypeId = 2
            )
            AND OperationTypeId = 1
        )
        AND lop.RiskIncludingTypeId NOT IN (3, 9)
    '

    IF @SourceLopIds <> ''
        SET @sql = @sql + ' AND lop.SourceLOPId IN (' + @SourceLopIds + ')'

    PRINT (@sql)
    EXEC (@sql)
END