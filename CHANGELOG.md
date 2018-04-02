# Changelog

All notable changes to this project will be documented in this file.

## [Releases](https://github.com/ValentinBELYN/OnionHA/releases)
## [v1.0.4](https://github.com/ValentinBELYN/OnionHA/releases/tag/v1.0.4) (2018-04-02)

### Changed
- Code optimization.

### Removed
- Delete the `syslog` option from the configuration file.

## [Releases](https://github.com/ValentinBELYN/OnionHA/releases)
## [v1.0.3](https://github.com/ValentinBELYN/OnionHA/releases/tag/v1.0.3) (2018-02-17)

### Added
- New logging function.

### Changed
- Rewrite `version`, `about` and `help` commands.
- Overall performance has been improved with many code optimizations and the use of f-strings.

### Fixed
- Fix an error in the code which did not display the correct gateway address in the terminal and logs.

## [v1.0.2](https://github.com/ValentinBELYN/OnionHA/releases/tag/v1.0.2) (2018-02-04)

### Changed
- Change `startDelay` to `initDelay` in the configuration file.
- Code optimization.

## [v1.0.1](https://github.com/ValentinBELYN/OnionHA/releases/tag/v1.0.1) (2018-02-01)

### Changed
- Onion now uses `subprocess.run()` method instead of `subprocess.call()`.
- Change from `danger` status to `critical`.
- Small improvements.

### Removed
- Remove built-in `capitalize()` function.

### Fixed
- Fix a bug that could crash the program when running scenarios.

## [v1.0.0](https://github.com/ValentinBELYN/OnionHA/releases/tag/v1.0.0) (2018-01-07)

- Initial release.
