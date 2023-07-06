{% for target in agile_targets %}
### {{ target.name }} ###
- alias: "Agile target: {{ target.name }}"
  trigger:
    - platform: state
      entity_id: {{ target.id }}
      to: null # Only trigger on state change, not on attribute change.
  condition:
    alias: "State is valid"
    condition: or
    conditions:
      - "{% raw %}{{ trigger.to_state.state == 'on'}}{% endraw %}"
      - "{% raw %}{{ trigger.to_state.state == 'off'}}{% endraw %}"
  action:
    - service_template: switch.turn_{% raw %}{{ trigger.to_state.state }}{% endraw %}
      target:
        entity_id: {{ target.group }}
{% endfor %}
