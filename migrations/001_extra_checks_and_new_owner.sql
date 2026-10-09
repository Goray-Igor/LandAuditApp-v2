DECLARE @Apply bit = 0;   -- 0 = предпросмотр, 1 = применить

-- ПРЕДПРОСМОТР
SELECT 'Audit_Extra_Checks' AS [об'єкт],
       CASE WHEN OBJECT_ID('dbo.Audit_Extra_Checks', 'U') IS NULL
            THEN 'буде створено' ELSE 'вже існує' END AS [статус];

SELECT v.col AS [колонка Audit_Lease_Individual],
       CASE WHEN COL_LENGTH('dbo.Audit_Lease_Individual', v.col) IS NULL
            THEN 'буде додано' ELSE 'вже існує' END AS [статус]
FROM (VALUES ('new_owner_ipn'), ('new_owner_has_passport_copy'),
             ('new_owner_has_inn_copy'), ('new_owner_has_title_deed_copy')) AS v(col);

-- ЗАСТОСУВАННЯ
IF @Apply = 1
BEGIN
    BEGIN TRY
        BEGIN TRAN;

        IF OBJECT_ID('dbo.Audit_Extra_Checks', 'U') IS NULL
        BEGIN
            CREATE TABLE dbo.Audit_Extra_Checks (
                id                                    int IDENTITY(1,1) PRIMARY KEY,
                cadastral_number                      nvarchar(50)  NOT NULL,
                contract_type                         nvarchar(100) NOT NULL,
                counterparty_type                     nvarchar(50)  NOT NULL,
                auditor_code                          nvarchar(255) NULL,
                area_discrepancy_title_vs_contract    bit NOT NULL DEFAULT 0,
                state_act_area_rounded_2dp            bit NOT NULL DEFAULT 0,
                lessee_alienation_with_notary_consent bit NOT NULL DEFAULT 0,
                lessee_bears_destruction_risk         bit NOT NULL DEFAULT 0,
                updated_at                            datetime2 NULL,
                CONSTRAINT UQ_Audit_Extra_Checks UNIQUE (cadastral_number, contract_type, counterparty_type)
            );
        END

        IF COL_LENGTH('dbo.Audit_Lease_Individual', 'new_owner_ipn') IS NULL
            ALTER TABLE dbo.Audit_Lease_Individual ADD new_owner_ipn nvarchar(50) NULL;
        IF COL_LENGTH('dbo.Audit_Lease_Individual', 'new_owner_has_passport_copy') IS NULL
            ALTER TABLE dbo.Audit_Lease_Individual ADD new_owner_has_passport_copy bit NULL;
        IF COL_LENGTH('dbo.Audit_Lease_Individual', 'new_owner_has_inn_copy') IS NULL
            ALTER TABLE dbo.Audit_Lease_Individual ADD new_owner_has_inn_copy bit NULL;
        IF COL_LENGTH('dbo.Audit_Lease_Individual', 'new_owner_has_title_deed_copy') IS NULL
            ALTER TABLE dbo.Audit_Lease_Individual ADD new_owner_has_title_deed_copy bit NULL;

        COMMIT;
        PRINT 'Міграцію застосовано.';
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0 ROLLBACK;
        THROW;
    END CATCH
END