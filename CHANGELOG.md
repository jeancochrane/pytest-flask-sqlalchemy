# Change Log

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Removed

- Drop support for Python versions prior to 3.6

## [1.0.2](https://github.com/jeancochrane/pytest-flask-sqlalchemy/releases/tag/v1.0.2) (2019-04-03)

### Changed

- Support SQLAlchemy 1.3 by adjusting the mock for threadlocal engine strategy [\#15](https://github.com/jeancochrane/pytest-flask-sqlalchemy/pull/15)

## [1.0.1](https://github.com/jeancochrane/pytest-flask-sqlalchemy/releases/tag/v1.0.1) (2019-03-02)

### Changed

- Expire session state at the top level [\#6](https://github.com/jeancochrane/pytest-flask-sqlalchemy/pull/6)
