pdf2zh-plugin-sungrow
=====================

Sungrow translator plugin for pdf2zh-next. Distributed as a standalone Python package and discovered via entry points.

Install
- Local (editable): `pip install -e ./examples/pdf2zh-plugin-sungrow`
- Git/PyPI: Publish the package and install with `pip install <name or git+url>`

Entry Point
The plugin registers under the group `pdf2zh_next.translators` as `sungrow` and exposes a callable `register_translator` that registers the translator with pdf2zh-next.

Usage
After installing, pdf2zh-next will automatically discover the plugin. Configure via the `SungrowSettings` fields in your config/CLI.

