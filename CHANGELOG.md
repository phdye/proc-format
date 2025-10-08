# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Added
- Form-feed character (`\f`) preservation during formatting. Form-feed characters are now automatically preserved by temporarily replacing them with markers before clang-format processing and restoring them afterward. This ensures that page breaks and section separators in source files are maintained.

### Changed
- Initial creation of documentation skeleton and developer/user guides.
