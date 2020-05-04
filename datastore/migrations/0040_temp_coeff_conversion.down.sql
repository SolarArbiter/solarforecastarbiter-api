UPDATE arbiter_data.sites SET temperature_coefficient = temperature_coefficient / 100, modified_at = modified_at WHERE temperature_coefficient IS NOT NULL;
