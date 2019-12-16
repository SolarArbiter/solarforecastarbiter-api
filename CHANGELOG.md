# Changelog

All notable changes to the Solar Forecast Arbiter Framework will be documented
in this file.

Detailed changes to the Solar Forecast Arbiter Core python library can be found
in the core documentation's [what's new](https://solarforecastarbiter-core.readthedocs.io/en/latest/whatsnew/index.html) series.

## [1.0beta3] - 2019-12-16

### Added

- Report form now includes all deterministic metrics options identified by
  stakeholders.

- Report form now includes options to calculate metrics by categories Total,
  Year, Month, Date, and Hour of Day.

- Ability to analyze forecasts of aggregated observations in reports.

- Reports may be downloaded in HTML format at
  `/reports/<report_id>/downloads/html`.

- The API report schema's `object_pair` json objects have been updated to
  support pairing forecasts with either observations or aggregates. See the
  [api documentation](https://api.solarforecastarbiter.org/#tag/Reports/paths/~1reports~1{report_id}/get) for details.

- Report downloads contain a GPG signed report as well as md5, sha1 and sha256
  checksums for validation.

- CHANGELOG.md (this file) for tracking and communicating changes.

### Fixed

- Permissions acting on aggregates are now accessible via a Role's permission
  listing.

## [1.0beta2] - 2019-11-18

### Added

- Aggregates can be created through the dashboard. See  [Aggregate Documentation](https://solarforecastarbiter.org/documentation/dashboard/working-with-data/#create-new-aggregate) 

- Day-ahead probabilistic reference forecasts based on the GEFS are available for DOE RTC, NOAA SURFRAD, NOAA SOLRAD, and NREL MIDC networks.

### Fixed

- Issues with report plots and tables including inconsistent forecast ordering
  and coloring in report bar charts, limitations on number of forecasts than
  can be plotted, limitations on number of metrics in a table.

## [1.0beta] - 2019-10-4

### Added

- User management controls for organization admin. See [Dashboard Administration Documentation](https://solarforecastarbiter.org/documentation/dashboard/administration/)

- Start/End selection for plots on Forecast, Probabilistic Forecasts and
  Observation Pages. 

## Fixed

- Reports now calculate monthly, daily, hourly metrics in the timezone
  specified by the site metadata instead of UTC.

- Reference NWP forecasts now properly account for `interval_label`.

## [1.0alpha] - 2019-06-28

Initial Solar Forecast Arbiter Dashboard release. Includes site, forecast,
probabilistic forecast, and basic report functionality.
