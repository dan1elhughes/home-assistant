{% for target in agile_targets %}
### {{ target.name }} ###
- alias: "Agile target: {{ target.name }}"
  trigger:
    - platform: state
      entity_id: {{ target.id }}
      to: null # Only trigger on state change, not on attribute change.
  condition:
    - condition: or
      alias: "State is valid"
      conditions:
        - "{% raw %}{{ trigger.to_state.state == 'on'}}{% endraw %}"
        - "{% raw %}{{ trigger.to_state.state == 'off'}}{% endraw %}"
    - condition: state
      alias: "Automations enabled"
      entity_id: input_boolean.automations
      state: "on"
  action:
    - service_template: homeassistant.turn_{% raw %}{{ trigger.to_state.state }}{% endraw %}
      target:
        entity_id: "{{ target.group }}"
{% endfor %}
