SET @reforgid = (SELECT id FROM organizations WHERE name = 'Reference');
DELETE FROM permissions WHERE organization_id = @reforgid AND description IN (
'Create all reports', 'Update all reports', 'Create all report values',
'Read all reports', 'Read all report values');
