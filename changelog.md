# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.3] - 2024/02/08

- Fixed bug where the annotator was logging duplicate data streams for each video in a session.
- Fixed bug where the participant status indicators under the session view were not updating properly.

## [1.0.2] - 2024/02/07

- Fixed bug where the `Coupled` condition for `Video Coupling` would occasionally assign and serve viewers videos for which they were flagged as the `Owner`.

## [1.0.1] - 2023/09/29

### Added

- Fixed the conditional display of `View Ordering` depending on `Video Coupling` value.
- Fixed the conditional display of `Video Coupling` depending on `Capacity` value.

## [1.0.0] - 2023/09/29

### Added

- Initial release featuring a complete overhaul of both backend and frontend functionality.

- A great many bugs for future me to deal with.
