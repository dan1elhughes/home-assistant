- alias: Battery idle
  mode: single
  trigger:
    - platform: state
      entity_id: binary_sensor.battery_idle_off_peak
  condition:
    - condition: template
      value_template: >
        {% raw %}{{{% endraw %} trigger.to_state.state in ['on', 'off'] {% raw %}}}{% endraw %}
  action:
    - service: "switch.turn_{% raw %}{{{% endraw %} trigger.to_state.state {% raw %}}}{% endraw %}"
      target:
        entity_id:
        {% for device in power_when_battery_idle %}
        # {{ device.name }}
        - {{ device.entity }}
        {% endfor %}
