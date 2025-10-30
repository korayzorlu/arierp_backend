SELECT
    FREE_PART_ID,
    FREE_PART_NO,
    PROJECT_ID,
    BLOCK_ID,
    TAX_GROUP_ID,
    ISLAND_NO,
    PLOT_NO,
    PARCEL_NO,
    GROSS_AREA,
    NET_AREA,
    LIST_PRICE,
    LIST_PRICE_CURR_ID,
    dbo.GeneralCurrency.CurrencyCode AS LIST_PRICE_CURR_CODE,
    dbo.GeneralTax.TaxRate AS KDV_RATIO,
    ISNULL(freePart.CODE_ID, 111) AS CODE_ID
FROM
    dbo.RPR_PROJECT_FREE_PART freePart
    LEFT JOIN dbo.GeneralCurrency
        ON freePart.LIST_PRICE_CURR_ID = dbo.GeneralCurrency.CurrencyId
    LEFT JOIN dbo.GeneralTax
        ON freePart.TAX_GROUP_ID = dbo.GeneralTax.TaxGroupId
WHERE
    IS_DELETED = 0;