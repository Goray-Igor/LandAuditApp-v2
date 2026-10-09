DECLARE @Apply bit = 0;   -- 0 = предпросмотр, 1 = применить

-- ПРЕДПРОСМОТР
SELECT t.tbl AS [таблиця],
       CASE WHEN OBJECT_ID('dbo.' + t.tbl, 'U') IS NULL THEN 'таблиці не існує — буде пропущено'
            WHEN COL_LENGTH('dbo.' + t.tbl, 'previous_lessee') IS NULL THEN 'буде додано колонку previous_lessee'
            ELSE 'вже існує' END AS [статус]
FROM (VALUES ('Audit_Lease_Individual'), ('Audit_Lease_OMS'), ('DKP_reestr')) AS t(tbl);

-- ЗАСТОСУВАННЯ
IF @Apply = 1
BEGIN
    BEGIN TRY
        BEGIN TRAN;

        IF OBJECT_ID('dbo.Audit_Lease_Individual', 'U') IS NOT NULL
           AND COL_LENGTH('dbo.Audit_Lease_Individual', 'previous_lessee') IS NULL
            EXEC('ALTER TABLE dbo.Audit_Lease_Individual ADD previous_lessee nvarchar(255) NULL');

        IF OBJECT_ID('dbo.Audit_Lease_OMS', 'U') IS NOT NULL
           AND COL_LENGTH('dbo.Audit_Lease_OMS', 'previous_lessee') IS NULL
            EXEC('ALTER TABLE dbo.Audit_Lease_OMS ADD previous_lessee nvarchar(255) NULL');

        IF OBJECT_ID('dbo.DKP_reestr', 'U') IS NOT NULL
           AND COL_LENGTH('dbo.DKP_reestr', 'previous_lessee') IS NULL
            EXEC('ALTER TABLE dbo.DKP_reestr ADD previous_lessee nvarchar(255) NULL');

        COMMIT;
        PRINT 'Міграцію застосовано.';
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0 ROLLBACK;
        THROW;
    END CATCH
END