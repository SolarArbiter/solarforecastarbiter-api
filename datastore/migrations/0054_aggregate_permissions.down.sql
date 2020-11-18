SET @orgid = get_organization_id('Reference');

DELETE FROM arbiter_data.permissions WHERE organization_id = @orgid AND description IN (
    'Read aggregates', 'Read aggregate values', 'Create aggregates', 'Update aggregates'
);
