SELECT QuotationHeaderId,
    SubStatuteDefinition,
    CustomerId,
    CurrencyCode,
    LeasingBaseCost,
    CustomerRepresentative,
    RequestDate,
    Vendor,
    Project
FROM QuotationHeaderLightList
-- WHERE
--     QuotationHeaderId = 52275;