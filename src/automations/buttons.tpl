{% for button in buttons %}
### {{ button.name }} ###
- alias: "{{ button.name }}"
  mode: single
  trigger:
    - platform: event
      event_type: zha_event
      event_data:
        device_ieee: {{ button.ieee }}
  action:
    - choose:
        - conditions: "{% raw %}{{{% endraw %} trigger.event.data.command == 'on' {% raw %}}}{% endraw %}"
          alias: "on"
          sequence:
            - action: light.turn_on
              entity_id: {{ button.light }}
              data:
                brightness_pct: 1

        - conditions: "{% raw %}{{{% endraw %} trigger.event.data.command == 'off_with_effect' {% raw %}}}{% endraw %}"
          alias: "off_with_effect"
          sequence:
            - action: light.turn_on
              entity_id: {{ button.light }}
              data:
                brightness_pct: 1

        - conditions: "{% raw %}{{{% endraw %} trigger.event.data.command == 'on_hold' {% raw %}}}{% endraw %}"
          alias: "on_hold"
          sequence:
            - action: light.turn_off
              entity_id: {{ button.light }}
{% endfor %}
