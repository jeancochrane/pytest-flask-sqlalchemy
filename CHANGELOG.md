# Change Log

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0](https://github.com/jeancochrane/pytest-flask-sqlalchemy/releases/tag/v1.1.0) (2022-04-30)

### Changed

- Add support for Python 3.8, 3.9, and 3.10 ([#60](https://github.com/jeancochrane/pytest-flask-sqlalchemy/pull/60))
- Add support for SQLAlchemy 1.4 ([#51](https://github.com/jeancochrane/pytest-flask-sqlalchemy/pull/51))

### Removed

- Drop support for Python versions prior to 3.6 ([#34](https://github.com/jeancochrane/pytest-flask-sqlalchemy/pull/34))
- Drop support for Python 3.6 ([#60](https://github.com/jeancochrane/pytest-flask-sqlalchemy/pull/60))
- Drop support for pytest < 6.0.1 ([#39](https://github.com/jeancochrane/pytest-flask-sqlalchemy/pull/39)) 

## [1.0.2](https://github.com/jeancochrane/pytest-flask-sqlalchemy/releases/tag/v1.0.2) (2019-04-03)

### Changed

- Support SQLAlchemy 1.3 by adjusting the mock for threadlocal engine strategy [\#15](https://github.com/jeancochrane/pytest-flask-sqlalchemy/pull/15)

## [1.0.1](https://github.com/jeancochrane/pytest-flask-sqlalchemy/releases/tag/v1.0.1) (2019-03-02)

### Changed

- Expire session state at the top level [\#6](https://github.com/jeancochrane/pytest-flask-sqlalchemy/pull/6)
