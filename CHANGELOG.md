# Changelog

All notable changes to the Solar Forecast Arbiter Framework will be documented
in this file.

Detailed changes to the Solar Forecast Arbiter Core python library can be found
in the core documentation's [what's new](https://solarforecastarbiter-core.readthedocs.io/en/latest/whatsnew/index.html) series.

## [1.0beta4] - 2020-02-07

### Added

- Daily updating precomputed reports for select reference data.

- Reports now contain a summary of data affected by the data resampling and
  alignment process. The summary includes the number of data points removed by
  each phase of validation.

- Reports now contain a table of all included metrics over the entire selected
  period.

- Reports may be configured to filter data by quality flag. Currently allows
  filtering of *user flagged* and *nighttime* values.

- The dashboard report view now allows users to search metric plots by
  forecast and to sort metric plots by metric, category and forecast.

- Dashboard users can now download report metrics as a csv using a link in the
  *Metrics* section of the report.

- Reports in the *pending* and *failed* state now display a message to the user
  about their status. For failed reports, this is a list of errors encountered
  while processing the report.

### Changed

- The API's report response's `raw_report` attribute was updated to reflect the
  set of processed report data needed for rendering a final report. The
  `raw_report` attribute was previously presented as a serialized version of
  the final rendered report.

- The core library's Report received a major refactoring. See the core
  [what's new](https://solarforecastarbiter-core.readthedocs.io/en/latest/whatsnew/1.0.0b4.html)
  for details.

- The button for downloading timeseries data from the dashboard has moved to
  below the plots on any Forecast, Observation or Probabilistic Forecast's
  page. The same start and end times are used for downloading data and creating
  plots.

- The start and end time values for the dashboard's timeseries plots are now
  prefilled with time range requested. By default, this will display the last
  three days of data.

### Fixed

- Corrected handling of empty observation timeseries during metrics
  preprocessing which was causing report processing to fail.

- Corrected handling of `interval_label` == `ending` when computing metrics
  for a report containing mixed `interval_label`s.

## [1.0beta3] - 2019-12-16

### Added

- Dashboard report form now includes all deterministic metrics options
  identified by stakeholders.

- Dashboard report form now includes options to calculate metrics by categories
  Total, Year, Month, Date, and Hour of Day.

- Ability to analyze forecasts of aggregated observations in reports.

- Reports may be downloaded in HTML format from the dashboard at
  `/reports/<report_id>/downloads/html`.

- The API report schema's `object_pair` json objects have been updated to
  support pairing forecasts with either observations or aggregates. See the
  [api documentation](https://api.solarforecastarbiter.org/#tag/Reports/paths/~1reports~1{report_id}/get) for details.

- Dashboard report downloads contain a GPG signed report as well as md5, sha1
  and sha256 checksums for validation.

- CHANGELOG.md (this file) for tracking and communicating changes.

- Dashboard tables now allow for filtering on multiple columns. e.g. Variable,
  Provider and Site for Observation and Forecast tables. 

### Fixed

- Permissions acting on aggregates are now accessible on the dashboard via a
  Role's permission listing.

- Removed dashboard functionality to create ineffectual permissions granting
  `update` action on forecasts, sites, observations and probabilistic
  forecasts.

- Removed permissions listing from the dashboard role creation form. Users
  will now add permissions after the Role has been created.

- Updated dashboard role and permission forms to retain checklist selections
  in the event of an error. 

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
