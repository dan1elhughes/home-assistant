from pathlib import Path


def test_predbat_control_toggle_is_below_mode():
    source = (Path(__file__).parents[1] / "src/dashboard_sections.tpl").read_text()
    predbat = source.split("title: Predbat", 1)[1].split("label: Overrides", 1)[0]
    mode = predbat.split("- entity: select.predbat_mode", 1)[1]
    assert mode.split("- entity:", 1)[1].lstrip().startswith("automation.predbat_control")
